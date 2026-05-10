#
# -*- coding: utf-8 -*-
#
# Gaming Chaos Engine V0.1.0 – A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# ... (license header identical to all other project files) ...

"""推演引擎 — 博弈模型驱动 + 精英智能体扰动 / Simulation engine — game-model-driven with elite-agent perturbation.

核心参考模型 / Key reference models:
  - PSRO (Policy-Space Response Oracles): iterative best-response toward Nash equilibrium
  - GenBR (Generative Best Response): opponent-state imagination + strategy search
  - NGRC (Next-Gen Reservoir Computing): polynomial-feature dynamics from history
  - Attraos: phase-space reconstruction and attractor-invariance analysis

推演流程 / Simulation flow:
  1. 检测博弈类型（价格战 / 拍卖 / 谈判 / 产量博弈）/ Detect game type
  2. 从数据库获取精英智能体作为策略扰动源 / Load elite agents as perturbation sources
  3. 运行博弈模型，每步计算理性策略 + 智能体扰动 / Run game model with perturbations
  4. Lyapunov + 分岔分析 / Chaos analysis
"""

from __future__ import annotations

import logging
import math
import statistics
from typing import Any, Callable, Dict, List, Optional, Tuple

from gce.core.GCE_forager import GCE_Forager
from gce.core.GCE_gene import GCE_deserialize_gene
from gce.core.GCE_predictor import GCE_Predictor
from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
from gce.environment.GCE_sentiment import GCE_compute_sentiment_bias
from gce.simulation.GCE_lyapunov import GCE_estimate_lyapunov, GCE_perturbation_analysis
from gce.simulation.GCE_schemas import GCE_Participant, GCE_Scenario, GCE_SimulationResult
from gce.storage.GCE_repository import GCE_get_elite_agents, GCE_get_agent_gene_blob

logger = logging.getLogger("gce.simulation.GCE_engine")

# ── 博弈类型检测关键词 / Game-type detection keywords ──────────────────────

_GAME_TYPE_PATTERNS: Dict[str, List[str]] = {
    "price_war": [
        "价格竞争", "价格战", "价格博弈", "定价博弈", "价格",
        "定价", "降价", "优惠", "打折",
        "price competition", "price war",
    ],
    "auction": [
        "拍卖", "竞拍", "竞标", "频谱", "出价", "报价",
        "auction", "bid",
    ],
    "negotiation": [
        "谈判", "协商", "协商谈判", "定价谈判", "医保谈判",
        "negotiation", "bargain",
    ],
    "output_competition": [
        "产量博弈", "产量竞争", "产能", "供给",
        "output competition", "capacity",
    ],
}


def _detect_game_type(objective: str) -> str:
    """从场景描述中检测博弈类型 / Detect game type from scenario description."""
    scores: Dict[str, int] = {}
    for game_type, keywords in _GAME_TYPE_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in objective)
        if score > 0:
            scores[game_type] = score
    if not scores:
        return "price_war"  # 默认：价格竞争 / Default
    return max(scores, key=lambda k: scores[k])


def _detect_participant_count(scenario: GCE_Scenario) -> int:
    """从场景推断实际参与方数量 / Infer actual participant count from scenario."""
    n_prices = len(scenario.initial_prices)
    n_participants = len(scenario.participants)
    # 前两个数字通常是时间步参数，实际价格从后面开始
    if n_prices >= 5:
        return min(n_prices - 2, 5)
    elif n_prices >= 3:
        return n_prices
    return max(n_participants, 2)


def _infer_cost_basis(initial_prices: List[float]) -> List[float]:
    """从初始价格推断各参与方的成本基础 / Infer cost basis from initial prices.

    成本推断逻辑 / Cost inference:
      - 将价格与时间数字分离：数值大的更可能是价格
      - 成本 ≈ 最低合理价格 × 0.4-0.6 (行业标准毛利率推断)
    """
    if len(initial_prices) <= 2:
        return [p * 0.4 for p in initial_prices]

    # 分离价格与可能混入的非价格数字 / Separate prices from non-price numbers
    sorted_prices = sorted(initial_prices)
    # 如果最大值是最小值的3倍以上，可能混入了无关数字
    if sorted_prices[-1] / max(sorted_prices[0], 0.01) > 10:
        # 按数量级分组，取中间组 / Group by magnitude, take the middle group
        median_idx = len(sorted_prices) // 2
        trimmed = sorted_prices[max(0, median_idx - 2):median_idx + 2]
    else:
        trimmed = sorted_prices[-5:] if len(sorted_prices) > 5 else sorted_prices

    min_price = min(trimmed)
    # 成本估计：最低价的 40%-60%，基于市场竞争程度 / Cost: 40-60% of lowest price
    cost_ratio = 0.45 + 0.10 * (len(trimmed) / max(len(trimmed), 5))
    return [max(0.01, p * cost_ratio) for p in trimmed[:5]]


# ── 智能体扰动函数 / Agent perturbation helpers ──────────────────────────

def _load_elite_predictors(
    db_path: str,
    elite_count: int,
    window_size: int = 20,
) -> Tuple[List[GCE_Predictor], List[int]]:
    """加载精英智能体的预测器 / Load elite agent predictors."""
    elites = GCE_get_elite_agents(db_path, elite_count)
    predictors: List[GCE_Predictor] = []
    masks: List[int] = []

    for agent in (elites or []):
        blob = GCE_get_agent_gene_blob(db_path, agent["id"])
        if blob is None:
            continue
        gene = GCE_deserialize_gene(blob)
        predictors.append(GCE_Predictor(tree=gene.tree))
        masks.append(gene.mask)

    return predictors, masks


def _agent_perturbation(
    history: List[float],
    predictors: List[GCE_Predictor],
    masks: List[int],
    window_size: int,
) -> float:
    """用精英智能体的预测偏差作为策略扰动 / Use elite agent prediction deviation as perturbation.

    扰动 = 精英预测中位数 - 当前价格均值
    这代表"市场预期"对"当前状态"的偏离，模拟集体非理性行为。
    """
    if not predictors:
        # 无智能体时可使用 NGRC 风格的多项式特征残差
        return _ngrc_style_residual(history)

    # 构建虚拟事件历史 / Build virtual event history
    virtual_history: List[GCE_RawEvent] = []
    for i, val in enumerate(history):
        virtual_history.append(GCE_RawEvent(
            source_id="price",
            event_type=GCE_EventType.NUMERIC,
            timestamp=i,
            value=val,
        ))

    predictions: List[float] = []
    for i, predictor in enumerate(predictors):
        mask = masks[i] if i < len(masks) else 0xFFFFFFFF
        forager = GCE_Forager(mask=mask, window_size=window_size)
        for event in virtual_history:
            forager.GCE_update(event)
        features = forager.GCE_extract()
        if features is None:
            continue
        result = predictor.GCE_predict(features)
        if result is not None:
            predictions.append(result[0])

    if not predictions:
        return _ngrc_style_residual(history)

    current_mean = statistics.mean(history[-window_size:]) if history else 0.0
    elite_median = statistics.median(predictions)

    # 扰动 = 精英预期 - 当前均值，归一化 / Perturbation = elite expectation - current mean, normalized
    scale = max(abs(current_mean), 0.01)
    perturbation = (elite_median - current_mean) / scale
    # 截断在合理范围 / Clamp to reasonable range
    return max(-0.5, min(0.5, perturbation))


def _ngrc_style_residual(history: List[float]) -> float:
    """NGRC风格的多项式特征残差 / NGRC-style polynomial feature residual.

    当没有精英智能体时，用近期数据的多项式外推误差作为扰动。
    参考 NGRC (Next-Generation Reservoir Computing) 的非线性特征方法。
    """
    if len(history) < 4:
        return 0.0
    recent = history[-4:]
    # 二次多项式外推 / Quadratic extrapolation
    x1, x2, x3, x4 = recent
    # 用前3个点拟合二次函数，预测第4个点
    a = (x3 - 2 * x2 + x1) / 2.0
    b = (x3 - x1) / 2.0
    c = x2
    predicted = a * 9 + b * 3 + c  # t=3 时的预测值
    residual = (x4 - predicted) / max(abs(x4), 0.01)
    return max(-0.3, min(0.3, residual * 0.1))


# ── 博弈模型 / Game models ────────────────────────────────────────────────

def _run_bertrand_game(
    scenario: GCE_Scenario,
    initial_prices: List[float],
    n_players: int,
    future_steps: int,
    predictors: List[GCE_Predictor],
    masks: List[int],
    window_size: int,
    sentiment_context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[float], Dict[str, List[float]], List[Dict], float, float, Dict[str, Any]]:
    """Bertrand 价格竞争模型 / Bertrand price competition model.

    模型 / Model:
      - N 家企业在同一市场定价 / N firms set prices in a common market
      - 市场份额 = softmax(-price_j) — 价格低者得更多份额
      - 理性策略：价格向"纳什均衡价格"调整（边际成本 + 竞争溢价）
      - 精英智能体对调整幅度施加扰动
      - 迭代求解近似纳什均衡 (PSRO 风格)

    返回 / Returns:
      - consensus_trajectory: 加权平均价格轨迹
      - player_trajectories: 每个参与方的价格轨迹
      - key_events: 关键事件列表
      - nash_convergence: 纳什收敛度 (0-1, 越高越接近均衡)
    """
    # 从初始价格推断各玩家成本 / Infer costs from initial prices
    costs = _infer_cost_basis(initial_prices)
    # 确保有 n_players 个成本 / Ensure n_players costs
    while len(costs) < n_players:
        costs.append(costs[-1] * (0.9 + 0.05 * len(costs)))
    costs = costs[:n_players]

    # 初始化价格 / Initialize prices
    player_prices: List[List[float]] = []
    for i in range(n_players):
        if i < len(initial_prices):
            start_price = initial_prices[i]
        else:
            start_price = initial_prices[-1] * (0.95 + 0.02 * i)
        player_prices.append([start_price])

    consensus_trajectory: List[float] = []
    key_events: List[Dict] = []
    demand_elasticity = 2.0 + 0.5 * n_players  # 弹性随玩家数增加
    sentiment_biases: Dict[str, List[float]] = {}

    for step in range(future_steps):
        current_prices = [p[-1] for p in player_prices]
        avg_price = statistics.mean(current_prices)

        # 计算市场份额 / Compute market shares (softmax over negative prices)
        neg_prices = [-p * demand_elasticity for p in current_prices]
        max_neg = max(neg_prices)
        exp_shares = [math.exp(np - max_neg) for np in neg_prices]
        total_exp = sum(exp_shares)
        market_shares = [es / total_exp for es in exp_shares]

        # 每玩家的最优反应价格 / Best-response price for each player
        new_prices: List[float] = []
        for i in range(n_players):
            cost_i = costs[i]
            my_price = current_prices[i]
            my_share = market_shares[i]

            # 竞争对手加权平均价格 / Competitor weighted average price
            competitor_prices = [current_prices[j] for j in range(n_players) if j != i]
            competitor_avg = statistics.mean(competitor_prices) if competitor_prices else my_price

            # 利润最大化的一阶条件 / First-order condition for profit maximization
            # optimal_price = cost + 1/elasticity (adjusted for market position)
            optimal_margin = (competitor_avg - cost_i) * 0.5 + (avg_price - cost_i) * 0.3
            rational_price = cost_i + max(0.01 * cost_i, optimal_margin * 0.7)

            # 价格向理性价格调整 / Adjust toward rational price
            adjustment_speed = 0.3 + 0.1 * (1.0 - my_share)  # 份额越小越激进
            base_next = my_price + (rational_price - my_price) * adjustment_speed

            # 智能体扰动 / Agent perturbation
            history_for_agent = [p[-min(20, len(p)):] for p in player_prices]
            flat_history = [v for sublist in history_for_agent for v in sublist]
            perturbation = _agent_perturbation(flat_history, predictors, masks, window_size)

            # 舆情偏置调制 / Sentiment bias modulation
            player_name = scenario.participants[i].name if i < len(scenario.participants) else f"Player-{i}"
            if sentiment_context and sentiment_context.get("source") != "fallback":
                s_bias = GCE_compute_sentiment_bias(sentiment_context, "price_war", player_name)
            else:
                s_bias = 0.0
            sentiment_biases.setdefault(player_name, []).append(s_bias)
            combined_pert = perturbation * (1.0 + s_bias)

            # 应用扰动（作为价格变化的比例） / Apply perturbation as proportion of price change
            perturbed_price = base_next * (1.0 + combined_pert * 0.05)
            # 价格不能低于成本 / Price can't go below cost
            perturbed_price = max(cost_i * 1.01, perturbed_price)
            # 价格不能高于初始的 2 倍 / Price can't exceed 2x initial
            perturbed_price = min(initial_prices[min(i, len(initial_prices) - 1)] * 2.0, perturbed_price)

            new_prices.append(perturbed_price)

            # 检测关键事件 / Detect key events
            price_change = abs(perturbed_price - my_price) / max(my_price, 0.01)
            if price_change > 0.15:
                key_events.append({
                    "step": step,
                    "player": scenario.participants[i].name if i < len(scenario.participants) else f"Player-{i}",
                    "type": "sharp_price_move",
                    "change_pct": round(price_change * 100, 1),
                    "from": round(my_price, 4),
                    "to": round(perturbed_price, 4),
                })

        for i in range(n_players):
            player_prices[i].append(new_prices[i])

        # 共识轨迹：市场份额加权平均价 / Consensus: market-share-weighted average
        consensus = sum(new_prices[i] * market_shares[i] for i in range(n_players))
        consensus_trajectory.append(consensus)

    # 计算纳什收敛度 / Compute Nash convergence
    final_prices = [p[-1] for p in player_prices]
    price_spread = max(final_prices) - min(final_prices)
    avg_final = statistics.mean(final_prices)
    nash_convergence = max(0.0, 1.0 - price_spread / max(avg_final, 0.01))

    # 构建参与方轨迹字典 / Build player trajectory dict
    player_trajectories: Dict[str, List[float]] = {}
    for i in range(n_players):
        name = scenario.participants[i].name if i < len(scenario.participants) else f"Player-{i + 1}"
        player_trajectories[name] = player_prices[i][1:]  # 跳过初始值

    # 均衡估计：最终价格的加权平均 / Equilibrium estimate
    equilibrium_estimate = sum(final_prices[i] * market_shares[i] for i in range(n_players))

    # 舆情影响摘要 / Sentiment impact summary
    sentiment_impact = _summarize_sentiment_impact(sentiment_biases)

    return consensus_trajectory, player_trajectories, key_events, equilibrium_estimate, nash_convergence, sentiment_impact


def _run_auction_game(
    scenario: GCE_Scenario,
    initial_prices: List[float],
    n_players: int,
    future_steps: int,
    predictors: List[GCE_Predictor],
    masks: List[int],
    window_size: int,
    sentiment_context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[float], Dict[str, List[float]], List[Dict], float, float, Dict[str, Any]]:
    """拍卖竞价模型 / Auction bidding model.

    采用维克里拍卖（第二价格密封拍卖）框架，多轮竞价 / Vickrey-style multi-round bidding.

    模型 / Model:
      - N 个竞拍者争夺 K 个单位（频谱/地块）/ N bidders for K units
      - 每轮各竞拍者提交密封报价 / Each round: sealed bids
      - 赢家支付第二高价格 / Winners pay second-highest price
      - 理性策略：报价 = 估值 - 风险折扣 / Rational: bid = valuation - risk discount
      - 竞争越激烈，风险折扣越小 / More competition → smaller discount
    """
    # 从初始出价推断估值 / Infer valuations from initial bids
    if len(initial_prices) >= n_players:
        valuations = list(initial_prices[:n_players])
    else:
        valuations = initial_prices + [initial_prices[-1] * (0.95 + 0.03 * i)
                                       for i in range(n_players - len(initial_prices))]

    player_bids: List[List[float]] = []
    for i in range(n_players):
        player_bids.append([valuations[i]])

    consensus_trajectory: List[float] = []
    key_events: List[Dict] = []
    sentiment_biases: Dict[str, List[float]] = {}

    # 拍卖轮次
    for step in range(future_steps):
        current_bids = [b[-1] for b in player_bids]
        sorted_bids = sorted(current_bids, reverse=True)

        # 赢家 = 最高出价者 / Winner = highest bidder
        winner_idx = current_bids.index(sorted_bids[0])
        # 第二高价 / Second-highest price
        second_price = sorted_bids[1] if len(sorted_bids) > 1 else sorted_bids[0] * 0.9

        new_bids: List[float] = []
        for i in range(n_players):
            my_val = valuations[i]
            my_bid = current_bids[i]

            # 竞争压力：其他出价者对我的威胁程度
            other_bids = [current_bids[j] for j in range(n_players) if j != i]
            max_other = max(other_bids) if other_bids else my_bid * 0.8

            # 理性报价：估值减去风险折扣 / Rational bid with risk discount
            # 风险折扣随竞争程度调整 / Risk discount adjusts with competition level
            risk_discount = (my_val - max_other) * 0.15 if max_other < my_val else 0.0
            rational_bid = my_val - risk_discount

            # 如果在上一轮输了，稍微提高出价 / If lost last round, raise slightly
            if i != winner_idx and current_bids[i] < sorted_bids[0]:
                rational_bid = my_bid + (sorted_bids[0] - my_bid) * 0.25

            # 限制在估值范围内 / Cap at valuation
            rational_bid = min(rational_bid, my_val * 0.98)

            # 智能体扰动 / Agent perturbation
            history_flat = [v for sublist in player_bids for v in sublist[-20:]]
            perturbation = _agent_perturbation(history_flat, predictors, masks, window_size)

            # 舆情偏置调制 / Sentiment bias modulation
            player_name = scenario.participants[i].name if i < len(scenario.participants) else f"Bidder-{i + 1}"
            if sentiment_context and sentiment_context.get("source") != "fallback":
                s_bias = GCE_compute_sentiment_bias(sentiment_context, "auction", player_name)
            else:
                s_bias = 0.0
            sentiment_biases.setdefault(player_name, []).append(s_bias)
            combined_pert = perturbation * (1.0 + s_bias)

            perturbed_bid = rational_bid * (1.0 + combined_pert * 0.03)

            # 限制范围 / Clamp
            perturbed_bid = max(my_val * 0.5, min(my_val * 1.05, perturbed_bid))
            new_bids.append(perturbed_bid)

            # 关键事件 / Key events
            if i == winner_idx:
                key_events.append({
                    "step": step,
                    "player": scenario.participants[i].name if i < len(scenario.participants) else f"Bidder-{i + 1}",
                    "type": "winning_bid",
                    "bid": round(perturbed_bid, 4),
                    "second_price": round(second_price, 4),
                })

        for i in range(n_players):
            player_bids[i].append(new_bids[i])
        consensus_trajectory.append(statistics.mean(new_bids))

    # 均衡估计：最终最高出价 / Equilibrium estimate: final highest bid
    final_bids = [b[-1] for b in player_bids]
    equilibrium_estimate = max(final_bids)

    # 纳什收敛度 / Nash convergence
    bid_spread = max(final_bids) - min(final_bids)
    nash_convergence = max(0.0, 1.0 - bid_spread / max(statistics.mean(final_bids), 0.01))

    player_trajectories: Dict[str, List[float]] = {}
    for i in range(n_players):
        name = scenario.participants[i].name if i < len(scenario.participants) else f"Bidder-{i + 1}"
        player_trajectories[name] = player_bids[i][1:]

    sentiment_impact = _summarize_sentiment_impact(sentiment_biases)

    return consensus_trajectory, player_trajectories, key_events, equilibrium_estimate, nash_convergence, sentiment_impact


def _run_negotiation_game(
    scenario: GCE_Scenario,
    initial_prices: List[float],
    n_players: int,
    future_steps: int,
    predictors: List[GCE_Predictor],
    masks: List[int],
    window_size: int,
    sentiment_context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[float], Dict[str, List[float]], List[Dict], float, float, Dict[str, Any]]:
    """谈判博弈模型 / Negotiation game model.

    模型 / Model:
      - N 方就一个价格进行谈判 / N parties negotiate over a price
      - 买方希望价格低，卖方希望价格高
      - 各方交替出价，逐步向中间靠拢
      - 让步幅度反映耐心程度和 BATNA（最佳替代方案）
    """
    # 区分买方与卖方 / Separate buyers and sellers
    sorted_prices = sorted(initial_prices[:n_players])
    mid = n_players // 2

    # 卖方（高价方）和买方（低价方）/ Sellers (high) and buyers (low)
    seller_indices = list(range(mid, n_players))
    buyer_indices = list(range(0, mid))
    if not buyer_indices:
        buyer_indices = [0]
        seller_indices = list(range(1, n_players)) if n_players > 1 else [0]

    # 初始化出价 / Initialize offers
    player_offers: List[List[float]] = []
    for i in range(n_players):
        start = initial_prices[min(i, len(initial_prices) - 1)]
        player_offers.append([start])

    consensus_trajectory: List[float] = []
    key_events: List[Dict] = []
    sentiment_biases: Dict[str, List[float]] = {}

    # 买卖双方初始位置 / Initial positions
    seller_avg = statistics.mean([initial_prices[min(i, len(initial_prices) - 1)]
                                   for i in seller_indices])
    buyer_avg = statistics.mean([initial_prices[min(i, len(initial_prices) - 1)]
                                  for i in buyer_indices])
    spread = seller_avg - buyer_avg

    for step in range(future_steps):
        current_offers = [o[-1] for o in player_offers]
        seller_current = statistics.mean([current_offers[i] for i in seller_indices])
        buyer_current = statistics.mean([current_offers[i] for i in buyer_indices])
        midpoint = (seller_current + buyer_current) / 2.0

        new_offers: List[float] = []
        for i in range(n_players):
            my_offer = current_offers[i]
            is_seller = i in seller_indices

            # 理性让步策略 / Rational concession strategy
            # 方向：卖方降价，买方加价，向中点靠拢
            if is_seller:
                # 卖方让步幅度 / Seller concession rate
                concession_rate = 0.15 + 0.05 * (step / max(future_steps, 1))
                rational_offer = my_offer - (my_offer - midpoint) * concession_rate
                rational_offer = max(buyer_current, rational_offer)
            else:
                concession_rate = 0.15 + 0.05 * (step / max(future_steps, 1))
                rational_offer = my_offer + (midpoint - my_offer) * concession_rate
                rational_offer = min(seller_current, rational_offer)

            # 智能体扰动（模拟谈判者的非理性坚持或让步）
            history_flat = [v for sublist in player_offers for v in sublist[-20:]]
            perturbation = _agent_perturbation(history_flat, predictors, masks, window_size)

            # 舆情偏置调制 / Sentiment bias modulation
            player_name = scenario.participants[i].name if i < len(scenario.participants) else f"Party-{i + 1}"
            if sentiment_context and sentiment_context.get("source") != "fallback":
                s_bias = GCE_compute_sentiment_bias(sentiment_context, "negotiation", player_name)
            else:
                s_bias = 0.0
            sentiment_biases.setdefault(player_name, []).append(s_bias)
            combined_pert = perturbation * (1.0 + s_bias)

            # 谈判中的扰动 = 情绪因素 / Emotional factor
            perturbed_offer = rational_offer * (1.0 + combined_pert * 0.02)

            # 限制在合理范围 / Clamp
            perturbed_offer = max(buyer_current * 0.8, min(seller_current * 1.2, perturbed_offer))
            new_offers.append(perturbed_offer)

            # 检测让步事件 / Detect concession
            if is_seller and my_offer - perturbed_offer > spread * 0.1:
                key_events.append({
                    "step": step,
                    "player": scenario.participants[i].name if i < len(scenario.participants) else f"Party-{i + 1}",
                    "type": "major_concession",
                    "from": round(my_offer, 4),
                    "to": round(perturbed_offer, 4),
                })

        for i in range(n_players):
            player_offers[i].append(new_offers[i])
        consensus_trajectory.append(statistics.mean(new_offers))

    # 均衡估计：最终的中点 / Equilibrium: final midpoint
    final_offers = [o[-1] for o in player_offers]
    final_seller = statistics.mean([final_offers[i] for i in seller_indices])
    final_buyer = statistics.mean([final_offers[i] for i in buyer_indices])
    equilibrium_estimate = (final_seller + final_buyer) / 2.0

    # 纳什收敛度：买卖双方价格差距缩小程度
    initial_gap = abs(seller_avg - buyer_avg)
    final_gap = abs(final_seller - final_buyer)
    nash_convergence = max(0.0, 1.0 - final_gap / max(initial_gap, 0.01))

    player_trajectories: Dict[str, List[float]] = {}
    for i in range(n_players):
        name = scenario.participants[i].name if i < len(scenario.participants) else f"Party-{i + 1}"
        player_trajectories[name] = player_offers[i][1:]

    sentiment_impact = _summarize_sentiment_impact(sentiment_biases)

    return consensus_trajectory, player_trajectories, key_events, equilibrium_estimate, nash_convergence, sentiment_impact


def _run_output_competition(
    scenario: GCE_Scenario,
    initial_prices: List[float],
    n_players: int,
    future_steps: int,
    predictors: List[GCE_Predictor],
    masks: List[int],
    window_size: int,
    sentiment_context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[float], Dict[str, List[float]], List[Dict], float, float, Dict[str, Any]]:
    """Cournot 产量竞争模型 / Cournot output competition model.

    模型 / Model:
      - N 家企业决定产量 / N firms choose output quantities
      - 市场价格 = 需求函数的逆函数(总产量) / Market price = inverse demand(total output)
      - 每家企业选择产量以最大化利润 / Each firm chooses output to maximize profit
      - 产量决定后价格由市场出清 / Market clearing price follows quantities
    """
    # 从初始价格推断参数 / Infer parameters from initial prices
    base_price = statistics.mean(initial_prices[:n_players]) if initial_prices else 100.0
    # 需求截距和斜率 / Demand intercept and slope
    demand_intercept = base_price * 2.0
    demand_slope = demand_intercept / (n_players * 10.0)

    costs = _infer_cost_basis(initial_prices)
    while len(costs) < n_players:
        costs.append(costs[-1] * 0.9)
    costs = costs[:n_players]

    # 初始产量 / Initial output levels
    player_outputs: List[List[float]] = []
    for i in range(n_players):
        # 价格越高 → 初始产量越小（合理推断）
        init_output = demand_intercept / (demand_slope * (n_players + 1)) * (0.8 + 0.2 * (i % 3))
        player_outputs.append([init_output])

    consensus_trajectory: List[float] = []
    key_events: List[Dict] = []
    sentiment_biases: Dict[str, List[float]] = {}

    for step in range(future_steps):
        current_outputs = [o[-1] for o in player_outputs]
        total_output = sum(current_outputs)
        market_price = max(0.01, demand_intercept - demand_slope * total_output)

        new_outputs: List[float] = []
        for i in range(n_players):
            cost_i = costs[i]
            my_output = current_outputs[i]
            others_output = total_output - my_output

            # 古诺最优反应 / Cournot best response
            # qi = (a - ci)/(2b) - sum(qj)/(2)
            residual_demand = max(0.01, demand_intercept - cost_i)
            optimal_output = max(0.01, residual_demand / (2 * demand_slope) - others_output / 2)

            # 调整速度 / Adjustment speed
            adjustment = 0.25
            rational_output = my_output + (optimal_output - my_output) * adjustment

            # 智能体扰动
            history_flat = [v for sublist in player_outputs for v in sublist[-20:]]
            perturbation = _agent_perturbation(history_flat, predictors, masks, window_size)

            # 舆情偏置调制 / Sentiment bias modulation
            player_name = scenario.participants[i].name if i < len(scenario.participants) else f"Firm-{i + 1}"
            if sentiment_context and sentiment_context.get("source") != "fallback":
                s_bias = GCE_compute_sentiment_bias(sentiment_context, "output_competition", player_name)
            else:
                s_bias = 0.0
            sentiment_biases.setdefault(player_name, []).append(s_bias)
            combined_pert = perturbation * (1.0 + s_bias)

            perturbed_output = rational_output * (1.0 + combined_pert * 0.05)
            perturbed_output = max(0.01, perturbed_output)

            new_outputs.append(perturbed_output)

        for i in range(n_players):
            player_outputs[i].append(new_outputs[i])

        # 共识轨迹使用市场价格 / Consensus trajectory uses market price
        total_new = sum(new_outputs)
        market_price = max(0.01, demand_intercept - demand_slope * total_new)
        consensus_trajectory.append(market_price)

    # 均衡价格 / Equilibrium price
    final_total = sum(o[-1] for o in player_outputs)
    equilibrium_estimate = max(0.01, demand_intercept - demand_slope * final_total)

    # 纳什收敛度
    final_outs = [o[-1] for o in player_outputs]
    output_spread = max(final_outs) - min(final_outs)
    nash_convergence = max(0.0, 1.0 - output_spread / max(statistics.mean(final_outs), 0.01))

    player_trajectories: Dict[str, List[float]] = {}
    for i in range(n_players):
        name = scenario.participants[i].name if i < len(scenario.participants) else f"Firm-{i + 1}"
        player_trajectories[name] = player_outputs[i][1:]

    sentiment_impact = _summarize_sentiment_impact(sentiment_biases)

    return consensus_trajectory, player_trajectories, key_events, equilibrium_estimate, nash_convergence, sentiment_impact


# ── 舆情影响汇总 / Sentiment impact summarizer ────────────────────────────

def _summarize_sentiment_impact(
    sentiment_biases: Dict[str, List[float]],
) -> Dict[str, Any]:
    """汇总各参与方的舆情偏置统计 / Summarize per-player sentiment bias stats."""
    if not sentiment_biases:
        return {"active": False, "player_impacts": {}}
    player_impacts = {}
    all_zero = True
    for name, biases in sentiment_biases.items():
        if not biases:
            continue
        avg_bias = statistics.mean(biases)
        max_bias = max(biases, key=abs)
        if abs(avg_bias) > 0.0001:
            all_zero = False
        player_impacts[name] = {
            "mean_bias": round(avg_bias, 4),
            "max_abs_bias": round(max_bias, 4),
            "direction": "amplify" if avg_bias > 0.02 else ("dampen" if avg_bias < -0.02 else "neutral"),
        }
    if all_zero:
        return {"active": False, "player_impacts": {}}
    overall_bias = statistics.mean([p["mean_bias"] for p in player_impacts.values()]) if player_impacts else 0.0
    return {
        "active": True,
        "overall_bias": round(overall_bias, 4),
        "player_impacts": player_impacts,
    }


# ── 主推演入口 / Main simulation entry ─────────────────────────────────────

def GCE_run_simulation(
    scenario: GCE_Scenario,
    db_path: str,
    config: Dict[str, Any],
) -> Optional[GCE_SimulationResult]:
    """运行博弈推演 / Run game-theoretic simulation.

    1. 检测博弈类型 / Detect game type
    2. 加载精英智能体作为扰动源 / Load elite agents as perturbation sources
    3. 运行对应的博弈模型 / Run the appropriate game model
    4. Lyapunov + 分岔分析 / Chaos analysis
    """
    sim_cfg = config.get("simulation", {})
    elite_count = sim_cfg.get("elite_count", 10)
    future_steps = scenario.time_steps
    epsilon = sim_cfg.get("perturbation_epsilon", 0.001)
    divergence_threshold = sim_cfg.get("divergence_threshold", 0.5)
    window_size = config.get("evolution", {}).get("window_size", 20)

    # 1. 检测博弈类型 — 优先用 parser 已检测的结果 / Detect game type, prefer parser result
    game_type = scenario.game_type or _detect_game_type(scenario.objective)
    n_players = _detect_participant_count(scenario)
    sentiment_context = scenario.sentiment_context or {}

    # 2. 加载精英智能体 / Load elite predictors
    predictors, masks = _load_elite_predictors(db_path, elite_count, window_size)

    # 3. 运行博弈模型 / Run game model
    initial_prices = scenario.initial_prices

    if game_type == "auction":
        consensus, player_traj, key_events, equilibrium, nash_conv, sentiment_impact = _run_auction_game(
            scenario, initial_prices, n_players, future_steps, predictors, masks, window_size,
            sentiment_context)
    elif game_type == "negotiation":
        consensus, player_traj, key_events, equilibrium, nash_conv, sentiment_impact = _run_negotiation_game(
            scenario, initial_prices, n_players, future_steps, predictors, masks, window_size,
            sentiment_context)
    elif game_type == "output_competition":
        consensus, player_traj, key_events, equilibrium, nash_conv, sentiment_impact = _run_output_competition(
            scenario, initial_prices, n_players, future_steps, predictors, masks, window_size,
            sentiment_context)
    else:
        # 默认：Bertrand 价格竞争 / Default: Bertrand price competition
        consensus, player_traj, key_events, equilibrium, nash_conv, sentiment_impact = _run_bertrand_game(
            scenario, initial_prices, n_players, future_steps, predictors, masks, window_size,
            sentiment_context)

    # 4. Lyapunov 分析 / Lyapunov estimation
    lyap = GCE_estimate_lyapunov(consensus, tau=1, dim=3)

    # 5. 轨迹波动率 / Trajectory volatility
    if len(consensus) >= 2:
        diffs = [abs(consensus[i] - consensus[i - 1]) / max(abs(consensus[i - 1]), 0.01)
                 for i in range(1, len(consensus))]
        volatility = statistics.mean(diffs) if diffs else 0.0
    else:
        volatility = 0.0

    # 6. 微扰分岔分析 / Perturbation bifurcation analysis
    init_state = initial_prices[:3] if len(initial_prices) >= 3 else \
        initial_prices + [initial_prices[-1]] * (3 - len(initial_prices))

    def _initial_state_fn() -> List[float]:
        return list(init_state)

    # 使用博弈模型作为仿真函数 / Use game model as simulation function
    def _simulate_fn(state: List[float], steps: int) -> List[float]:
        if game_type == "auction":
            traj, _, _, _, _, _ = _run_auction_game(
                scenario, state, n_players, steps, predictors, masks, window_size)
        elif game_type == "negotiation":
            traj, _, _, _, _, _ = _run_negotiation_game(
                scenario, state, n_players, steps, predictors, masks, window_size)
        elif game_type == "output_competition":
            traj, _, _, _, _, _ = _run_output_competition(
                scenario, state, n_players, steps, predictors, masks, window_size)
        else:
            traj, _, _, _, _, _ = _run_bertrand_game(
                scenario, state, n_players, steps, predictors, masks, window_size)
        return traj

    bifurcations = GCE_perturbation_analysis(
        GCE_initial_state=_initial_state_fn,
        simulate_fn=_simulate_fn,
        epsilon=epsilon,
        threshold=divergence_threshold,
        steps=future_steps,
    )

    # 7. 构建精英策略摘要 / Build elite strategy summary
    strategy_summary: Dict[str, Any] = {
        "elite_count": len(predictors),
        "game_type": game_type,
        "n_players": n_players,
        "nash_convergence": nash_conv,
        "equilibrium_estimate": equilibrium,
        "volatility": volatility,
    }

    return GCE_SimulationResult(
        consensus_trajectory=consensus,
        lyapunov_estimate=lyap,
        bifurcation_points=bifurcations,
        elite_strategies=strategy_summary,
        game_type=game_type,
        participant_trajectories=player_traj,
        equilibrium_estimate=equilibrium,
        nash_convergence=nash_conv,
        trajectory_volatility=volatility,
        key_events=key_events,
        sentiment_impact=sentiment_impact,
    )
