#
# -*- coding: utf-8 -*-
#
# Gaming Chaos Engine V0.1.0 – A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# ... (license header identical to all other project files) ...

"""叙事生成器 —— LLM 优先战略分析 + 规则引擎回退 / Narrative generator — LLM-first strategic analysis with rule-based fallback."""

from __future__ import annotations

import logging
import math
import statistics
from typing import Any, Dict, List, Optional

from gce.interface.GCE_domain_templates import GCE_get_template_by_id
from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.simulation.GCE_schemas import GCE_Scenario, GCE_SimulationResult

import yaml

logger = logging.getLogger("gce.interface.GCE_narrator")

_SYSTEM_PROMPT = """你是一位顶级战略顾问，精通博弈论、混沌动力学和商业战略。你的任务是基于推演系统提供的**真实计算数据**，撰写一份可执行的四幕战略决策报告，并在报告末尾附加一份**大白话结论卡片**。

## 报告结构要求

### 一、战场全息重构
- 说明当前博弈场的动力学状态（混沌收敛/发散/临界），引用 Lyapunov 指数和轨迹数据
- 指出系统是否正在逼近纳什均衡（引用纳什收敛度）
- 分析轨迹趋势方向、波动率，以及这意味着什么
- **不要写泛泛的"系统稳定/混沌"，要分析这对决策者意味着什么**

### 二、对手心智镜像
- 基于各参与方的实际价格/出价轨迹数据，分析每方的决策逻辑和行为模式
- 谁在主动进攻？谁在被动防守？谁在发出虚假信号？
- 指出各方的可能敏感点、底线和下一步可能动作
- **必须引用具体数据，不能写套话**

### 三、博弈树全展开
- 基于分岔点数据和轨迹趋势，列出 2-3 个关键结果分支
- 每个分支说明触发条件和可能结果
- 分支要具体——"如果A在第N步将价格降至X，则B可能以Y回应"
- 标注每个分支的估计出现概率

### 四、策略指令下达
- 给出**具体的、可立即执行的**行动建议
- 每条建议包含：时机（哪一步）、幅度（调整多少）、对象（针对谁）
- 区分"即时行动"（1-3步）和"中期布局"（5-15步）
- 设定具体的止损/止盈边界
- **策略要针对此场景量身定制，不能是通用建议**

### 五、大白话结论卡片 (Plain-Language Conclusion Card)
在四幕报告之后，用 `---` 分隔线分开，然后写一份**完全不使用专业术语**的结论卡片。要求：
- **一句话策略**：用大白话说清楚"到底该怎么做"——给出具体的比例、方向、时机
- **为什么这么分**：用通俗的比喻或类比解释推演发现的逻辑，不要提Lyapunov、纳什等术语
- **接下来具体怎么操作（人话版）**：用"盯住数字""要是……就……"这种日常语言写操作步骤
- **最直白的总结**：用生活化的类比收尾，让完全不懂博弈论的人也能秒懂
- 长度控制在300-500字，语言像朋友在饭桌上给你解释一样自然

## 写作风格
- 犀利、清晰、直接
- 用具体数字，不说"大约""可能""考虑"
- 报告长度 800-1200 字，结论卡片 300-500 字
- 中文输出"""


def _build_user_message(scenario: GCE_Scenario, result: GCE_SimulationResult) -> str:
    """构建数据丰富的 LLM 提示 / Build data-rich LLM prompt."""
    traj = result.consensus_trajectory
    lyap = result.lyapunov_estimate
    bifurcations = result.bifurcation_points
    nash = result.nash_convergence
    volatility = result.trajectory_volatility
    equilibrium = result.equilibrium_estimate
    game_type = result.game_type
    key_events = result.key_events or []
    player_traj = result.participant_trajectories or {}

    # 轨迹摘要
    if traj:
        traj_start = f"{traj[0]:.4f}"
        traj_end = f"{traj[-1]:.4f}"
        traj_min = f"{min(traj):.4f}"
        traj_max = f"{max(traj):.4f}"
        traj_change = f"{(traj[-1] - traj[0]) / max(abs(traj[0]), 0.01) * 100:.1f}%"
        traj_detail = " → ".join(f"{v:.4f}" for v in traj[:10])
        if len(traj) > 10:
            traj_detail += f" ... → {traj[-1]:.4f}"
    else:
        traj_start = traj_end = traj_min = traj_max = traj_change = "N/A"
        traj_detail = "N/A"

    # 混沌体制
    if lyap > 0.1:
        regime = "混沌发散 — 微小扰动导致截然不同的结果，短期预测可信度低"
    elif lyap > 0.01:
        regime = "弱混沌 — 存在可辨识的吸引子结构，中期预测有参考价值"
    elif lyap > -0.01:
        regime = "边际稳定 — 对小扰动保持中性，预测轨迹可靠度较高"
    else:
        regime = "收敛稳定 — 强吸引子，系统快速逼近均衡，预测高度可信"

    # 博弈类型
    game_type_cn = {
        "price_war": "价格竞争 (Bertrand 模型)",
        "auction": "拍卖竞价 (Vickrey 模型)",
        "negotiation": "定价谈判 (交替出价模型)",
        "output_competition": "产量竞争 (Cournot 模型)",
    }.get(game_type, game_type)

    # 参与方轨迹
    player_sections = []
    for name, pt in player_traj.items():
        if pt:
            p_start = pt[0]
            p_end = pt[-1]
            p_change = (p_end - p_start) / max(abs(p_start), 0.01) * 100
            p_trend = "上升" if p_change > 1 else ("下降" if p_change < -1 else "持平")
            player_sections.append(
                f"  {name}: 起步 {p_start:.4f} → 终点 {p_end:.4f} "
                f"({p_change:+.1f}%, 趋势: {p_trend})"
            )

    # 关键事件
    event_sections = []
    for ev in key_events[:10]:
        event_sections.append(
            f"  第{ev['step']}步: {ev.get('player', '?')} {ev.get('type', '?')} "
            f"{ev.get('from', '?')} → {ev.get('to', '?')}"
        )

    # 分岔点
    bifurcation_str = ", ".join(f"第{t}步" for t in bifurcations[:5]) if bifurcations else "无显著分岔点"

    # 舆情背景
    sentiment_context = scenario.sentiment_context or {}
    sentiment_section = ""
    if sentiment_context.get("source") == "llm":
        sentiment_section = f"""
### 舆情分析
整体情绪: {sentiment_context.get('overall_sentiment', 'neutral')} (score={sentiment_context.get('sentiment_score', 0):.2f})
关键主题: {', '.join(sentiment_context.get('key_themes', []))}
市场情绪: {sentiment_context.get('market_mood', 'cautious')} | 波动预期: {sentiment_context.get('volatility_expectation', 'moderate')}
各实体情绪: {sentiment_context.get('entity_sentiments', {})}
舆情摘要: {sentiment_context.get('summary', '无')}
"""

    # 舆情对推演的影响
    sentiment_impact = result.sentiment_impact or {}
    impact_section = ""
    if sentiment_impact.get("active"):
        impact_section = f"""
### 舆情对推演的影响
整体偏置: {sentiment_impact.get('overall_bias', 0):.4f} (正值=放大扰动, 负值=缩小扰动)
"""
        for name, pinfo in sentiment_impact.get("player_impacts", {}).items():
            impact_section += f"  {name}: 平均偏置 {pinfo['mean_bias']:.4f} ({pinfo['direction']})\n"

    return f"""## 场景信息
描述: {scenario.objective}
参与方: {", ".join(p.name for p in scenario.participants)}
初始价格/出价: {", ".join(f"{p:.2f}" for p in scenario.initial_prices)}
推演步数: {scenario.time_steps}

## 推演结果 (基于 {game_type_cn} 计算)

### 博弈类型
{game_type_cn} | {len(player_traj)} 个参与方

### 共识轨迹
{traj_detail}
起始: {traj_start} → 终点: {traj_end}
区间: [{traj_min}, {traj_max}]
总变化: {traj_change}

### 混沌分析
Lyapunov 指数: {lyap:.6f}
动力学状态: {regime}
分岔候选点: {bifurcation_str}
轨迹波动率: {volatility:.4f}

### 纳什均衡分析
纳什收敛度: {nash:.4f} ({'已高度收敛——各方策略趋于稳定' if nash > 0.8 else '仍在调整中——各方还在寻找最优策略' if nash > 0.4 else '远未收敛——博弈格局仍在剧烈变化'})
估计均衡价格: {equilibrium:.4f}

### 各参与方价格/出价轨迹
{chr(10).join(player_sections) if player_sections else '无数据'}

### 关键事件
{chr(10).join(event_sections) if event_sections else '无显著事件'}
{sentiment_section}{impact_section}
请基于以上数据撰写四幕战略决策报告。"""


def GCE_generate_narrative(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    llm_client: GCE_LLMClient,
    offline_mode: bool = False,
    narratives_path: Optional[str] = None,
    domain_id: str = "",
) -> str:
    """生成四幕战略报告 / Generate a four-act strategic report.

    优先使用 LLM 进行真正的战略分析；不可用时回退到规则分析引擎。
    """
    domain_id = domain_id or scenario.domain_id

    if not offline_mode and llm_client.enabled:
        narrative = _generate_online(scenario, result, llm_client, domain_id)
        if narrative:
            return narrative
        logger.warning("LLM narrative failed, using rule-based analysis")

    return _generate_rule_based(scenario, result, narratives_path, domain_id)


def _generate_online(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    llm_client: GCE_LLMClient,
    domain_id: str = "",
) -> Optional[str]:
    """LLM 驱动的战略分析 / LLM-driven strategic analysis."""
    system_prompt = _SYSTEM_PROMPT
    if domain_id:
        template = GCE_get_template_by_id(domain_id)
        if template and template.narrative_prompt_additions:
            system_prompt = (
                _SYSTEM_PROMPT + "\n\n## 领域写作指南 / Domain Writing Guide\n"
                + template.narrative_prompt_additions
            )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": _build_user_message(scenario, result)},
    ]
    return llm_client.GCE_generate(messages)


# ── 规则分析引擎 / Rule-based analysis engine (LLM 不可用时的回退) ────────

def _generate_rule_based(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    narratives_path: Optional[str] = None,
    domain_id: str = "",
) -> str:
    """基于推演数据的规则分析引擎 / Rule-based analysis driven by actual simulation data.

    不使用任何静态模板——每一段文本都基于实际计算数据推导。
    """
    traj = result.consensus_trajectory
    lyap = result.lyapunov_estimate
    nash = result.nash_convergence
    volatility = result.trajectory_volatility
    equilibrium = result.equilibrium_estimate
    game_type = result.game_type
    key_events = result.key_events or []
    player_traj = result.participant_trajectories or {}
    bifurcations = result.bifurcation_points
    elite_count = result.elite_strategies.get("elite_count", 0)

    sentiment_context = scenario.sentiment_context or {}

    # 获取领域术语替换表 / Get domain term overrides for rule-based output
    term_map: Dict[str, str] = {}
    if domain_id:
        template = GCE_get_template_by_id(domain_id)
        if template and template.narrative_term_overrides:
            term_map = template.narrative_term_overrides

    def _apply_terms(text: str) -> str:
        """替换金融术语为领域术语 / Replace financial terms with domain terms."""
        for old, new in term_map.items():
            text = text.replace(old, new)
        return text

    # ── Act I: 战场全息重构 / Battlefield Holographic Reconstruction ──
    act1 = _build_act1_regime(lyap, traj, volatility, nash, equilibrium, sentiment_context)

    # ── Act II: 对手心智镜像 / Opponent Mind Mirror ──
    act2 = _build_act2_opponents(player_traj, traj, key_events, scenario, game_type, elite_count, sentiment_context)

    # ── Act III: 博弈树全展开 / Full Game Tree Expansion ──
    act3 = _build_act3_branches(traj, lyap, bifurcations, game_type, scenario, equilibrium, nash)

    # ── Act IV: 策略指令下达 / Strategy Orders Issued ──
    act4 = _build_act4_strategy(traj, lyap, nash, volatility, equilibrium, game_type, scenario, key_events)

    # 组装报告
    trajectory_preview = " → ".join(f"{v:.4f}" for v in traj[:8])
    if len(traj) > 8:
        trajectory_preview += f" ... → {traj[-1]:.4f}"

    game_type_cn = {
        "price_war": "价格竞争 (Bertrand)",
        "auction": "拍卖竞价 (Vickrey)",
        "negotiation": "定价谈判",
        "output_competition": "产量竞争 (Cournot)",
    }.get(game_type, game_type)

    report = f"""═══════════════════════════════
  博弈混沌推演决策报告
═══════════════════════════════

【场景】{scenario.objective}
【参与方】{", ".join(p.name for p in scenario.participants)}
【博弈模型】{game_type_cn}
【推演步数】{scenario.time_steps} 步 | 精英博弈元: {elite_count} 个

━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、战场全息重构
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{act1}

共识轨迹: [{trajectory_preview}]
Lyapunov 指数: {lyap:.6f}  |  纳什收敛度: {nash:.3f}  |  波动率: {volatility:.4f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、对手心智镜像
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{act2}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、博弈树全展开
━━━━━━━━━━━━━━━━━━━━━━━━━━━

分岔候选点: {", ".join(f"第{t}步" for t in bifurcations[:5]) if bifurcations else "无显著分岔点"}

{act3}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、策略指令下达
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{act4}

═══════════════════════════════
  报告结束 | 建议复核周期: 每 {max(5, scenario.time_steps // 4)} 步
═══════════════════════════════"""

    # 应用领域术语替换 / Apply domain term overrides
    report = _apply_terms(report) if term_map else report

    # 附加大白话结论卡片 / Append plain-language conclusion card
    plain_card = _build_plain_language_card(scenario, result, domain_id)
    if plain_card:
        report += "\n\n" + plain_card

    return report


# ── Act builders ───────────────────────────────────────────────────────────

def _build_act1_regime(
    lyap: float, traj: List[float], volatility: float,
    nash: float, equilibrium: float,
    sentiment_context: Optional[Dict[str, Any]] = None,
) -> str:
    """基于数据构建第一幕：战场态势 / Build Act I from data."""

    # 轨迹分析
    if len(traj) >= 2:
        start, end = traj[0], traj[-1]
        pct_change = (end - start) / max(abs(start), 0.01) * 100
        direction = "上升" if pct_change > 1 else ("下降" if pct_change < -1 else "横盘震荡")

        # 检测轨迹中的转折点
        turning_points = []
        for i in range(2, len(traj)):
            prev_diff = traj[i - 1] - traj[i - 2]
            curr_diff = traj[i] - traj[i - 1]
            if prev_diff * curr_diff < 0 and abs(curr_diff - prev_diff) / max(abs(prev_diff), 0.0001) > 0.3:
                turning_points.append(i)
    else:
        start = end = 0.0
        pct_change = 0.0
        direction = "无数据"
        turning_points = []

    # 混沌体制解读
    if lyap > 0.1:
        regime_line = "动力学状态: **混沌发散** (Chaotic Divergent)"
        implication = (
            "系统 Lyapunov 指数大于 0.1，处于高度不可预测状态。"
            "微小初始条件差异将导致指数级发散的结果差异。"
            "**决策含义**: 放弃长期精确预测，转向\"情景规划 + 快速响应\"模式。"
            "每 {} 步重新评估，根据实际对手反应动态调整策略。".format(
                max(3, len(traj) // 8))
        )
    elif lyap > 0.01:
        regime_line = "动力学状态: **弱混沌** (Weakly Chaotic)"
        implication = (
            "系统存在可辨识的吸引子结构，但中期预测存在显著不确定性。"
            "短期（3-5 步内）预测可信度较高，长期预测需结合分岔分析。"
            "**决策含义**: 在吸引子结构内沿共识方向行动，但在分岔候选点设置预警机制。"
        )
    elif lyap > -0.01:
        regime_line = "动力学状态: **边际稳定** (Marginally Stable)"
        implication = (
            "系统对小扰动保持中性响应。当前轨迹的预测可靠度较高——"
            "除非遭遇外部冲击，否则系统将在当前位置附近小幅波动。"
            "**决策含义**: 可以沿当前趋势制定策略，但需保留应对突发事件的灵活性。"
        )
    else:
        regime_line = "动力学状态: **收敛稳定** (Convergent Stable)"
        implication = (
            "系统具有强吸引子——无论初始条件如何，轨迹都将快速逼近同一均衡。"
            "Lyapunov 指数 {:.4f} 确认了这一判断。".format(lyap) +
            "**决策含义**: 确定性策略可行。既然终点大致可预测，"
            "重点在于以最低成本到达该均衡，而非对抗市场趋势。"
        )

    # 趋势解读
    if abs(pct_change) > 20:
        trend_note = f"轨迹从 {start:.4f} 急{'升' if pct_change > 0 else '降'}至 {end:.4f}（{pct_change:+.1f}%）。市场正在剧烈重新定价。"
    elif abs(pct_change) > 5:
        trend_note = f"轨迹从 {start:.4f} {'上涨' if pct_change > 0 else '下跌'}至 {end:.4f}（{pct_change:+.1f}%），呈温和趋势。"
    else:
        trend_note = f"轨迹在 {start:.4f} 至 {end:.4f} 间{'小幅波动' if volatility < 0.05 else '波动'}（{pct_change:+.1f}%），价格相对平稳。"

    # 转折点
    if turning_points:
        tp_str = ", ".join(f"第{t}步" for t in turning_points[:4])
        trend_note += f" 检测到 {len(turning_points)} 个潜在转折点（{tp_str}），这些位置是策略调整的关键窗口。"

    # 纳什收敛度
    if nash > 0.8:
        nash_note = "纳什收敛度 {:.3f}——各方策略已高度收敛，博弈格局趋于稳定。继续大幅偏离当前均衡的策略将付出超额代价。".format(nash)
    elif nash > 0.4:
        nash_note = "纳什收敛度 {:.3f}——各方策略仍在调整中。当前存在利用对手尚未稳定之机抢占优势的窗口。".format(nash)
    else:
        nash_note = "纳什收敛度 {:.3f}——博弈格局远未稳定，各方仍在探索最优策略。这既是机会（先发优势）也是风险（方向判断错误代价高）。".format(nash)

    # 舆情影响说明
    sentiment_note = ""
    if sentiment_context and sentiment_context.get("source") == "llm":
        overall = sentiment_context.get("overall_sentiment", "neutral")
        score = sentiment_context.get("sentiment_score", 0.0)
        mood = sentiment_context.get("market_mood", "cautious")
        themes = sentiment_context.get("key_themes", [])
        sentiment_note = (
            f"\n\n**舆情调制**: 当前市场情绪为 {overall}（score={score:.2f}），"
            f"风险偏好 {mood}。关键舆情主题: {', '.join(themes[:3]) if themes else '无'}。"
            f"这些舆情因素已注入博弈模型，调制各参与方的策略扰动幅度。"
        )

    return f"""{regime_line}
{implication}

{trend_note}
{nash_note}
估计均衡价格: {equilibrium:.4f}{sentiment_note}"""


def _build_act2_opponents(
    player_traj: Dict[str, List[float]],
    traj: List[float],
    key_events: List[Dict],
    scenario: GCE_Scenario,
    game_type: str,
    elite_count: int,
    sentiment_context: Optional[Dict[str, Any]] = None,
) -> str:
    """基于参与方实际轨迹数据构建第二幕 / Build Act II from participant trajectory data."""

    if not player_traj:
        return f"基于 {elite_count} 个精英博弈元的推演，无法获取各参与方的独立轨迹数据。\n建议延长进化时间以提高智能体对个体行为的建模能力。"

    lines = []
    player_stats = []

    for name, pt in player_traj.items():
        if len(pt) < 2:
            continue
        start = pt[0]
        end = pt[-1]
        pct = (end - start) / max(abs(start), 0.01) * 100
        volatility_p = statistics.stdev(pt) / max(abs(statistics.mean(pt)), 0.01) if len(pt) >= 2 else 0.0

        # 行为分类
        if pct > 5:
            behavior = "激进进攻型"
            detail = f"价格/出价从 {start:.4f} 升至 {end:.4f}"
        elif pct < -5:
            behavior = "降价抢量型" if game_type == "price_war" else "防守退让型"
            detail = f"价格/出价从 {start:.4f} 降至 {end:.4f}"
        else:
            behavior = "稳健维持型"
            detail = f"价格/出价在 {min(pt):.4f}–{max(pt):.4f} 间窄幅波动"

        player_stats.append((name, pct, volatility_p, behavior, detail, start, end))

    # 按变化幅度排序
    player_stats.sort(key=lambda x: abs(x[1]), reverse=True)

    for i, (name, pct, vol, behavior, detail, start, end) in enumerate(player_stats):
        # 行为特征分析
        if behavior == "激进进攻型":
            strategy_note = (
                f"**{name}** 表现出激进进攻姿态——{detail}（{pct:+.1f}%）。"
                f"此行为可能是试图建立价格锚点，或发出\"不惧竞争\"的市场信号。"
            )
        elif behavior == "降价抢量型":
            strategy_note = (
                f"**{name}** 采取降价抢量策略——{detail}（{pct:+.1f}%）。"
                f"此方可能在牺牲短期利润率换取市场份额。关注其成本底线——"
                f"当价格逼近其边际成本时（估计 {start * 0.4:.4f}），降价空间将耗尽。"
            )
        elif behavior == "防守退让型":
            strategy_note = (
                f"**{name}** 处于防守退让状态——{detail}（{pct:+.1f}%）。"
                f"此方可能正在承受竞争压力，或主动选择非价格竞争维度。"
            )
        else:
            strategy_note = (
                f"**{name}** 采取稳健策略——{detail}（{pct:+.1f}%）。"
                f"波动率 {vol:.3f}，表明此方在等待局势明朗后再行动，属于观望型选手。"
            )

        # 补充敏感点分析
        if abs(pct) > 10:
            strategy_note += f" 关键敏感点: 约 {start:.4f}（初始位置）——突破此位可能引发强烈反应。"
        if vol > 0.1:
            strategy_note += f" 高波动性（σ={vol:.3f}）暗示此方决策逻辑存在内部矛盾或信息不充分。"

        # 实体舆情情绪
        entity_sentiments = (sentiment_context or {}).get("entity_sentiments", {})
        if name in entity_sentiments and entity_sentiments[name] != 0.0:
            es = entity_sentiments[name]
            mood_label = "乐观" if es > 0.15 else ("悲观" if es < -0.15 else "中性")
            strategy_note += f" 舆情情绪: {mood_label}（{es:+.2f}），影响其策略扰动幅度。"

        lines.append(strategy_note)

    # 总体态势
    if len(player_stats) >= 2:
        most_aggressive = player_stats[0]
        most_defensive = player_stats[-1]
        lines.append("")
        lines.append(
            f"**总体态势**: {most_aggressive[0]} 是当前博弈中最活跃的变量，"
            f"{most_defensive[0]} 相对被动。"
            f"博弈主动权掌握在行动最快的一方手中——"
            f"但这也意味着其策略意图最先暴露，可为对手所利用。"
        )

    # 关键事件补充
    if key_events:
        lines.append("")
        lines.append("**关键行为节点**:")
        for ev in key_events[:5]:
            ev_type = ev.get('type', '?')
            player = ev.get('player', '?')
            # 根据事件类型选择显示字段
            if ev_type == 'winning_bid':
                detail = f"中标价 {ev.get('bid', '?')}（次高价: {ev.get('second_price', '?')}）"
            elif ev_type == 'major_concession':
                detail = f"{ev.get('from', '?')} → {ev.get('to', '?')}"
            elif ev_type == 'sharp_price_move':
                detail = f"{ev.get('from', '?')} → {ev.get('to', '?')}（{ev.get('change_pct', '?')}%）"
            else:
                detail = f"{ev.get('from', ev.get('bid', '?'))}"
            lines.append(f"  · 第{ev['step']}步: {player} {ev_type} — {detail}")

    return "\n".join(lines)


def _build_act3_branches(
    traj: List[float], lyap: float, bifurcations: List[int],
    game_type: str, scenario: GCE_Scenario,
    equilibrium: float, nash: float,
) -> str:
    """基于轨迹和分岔分析构建第三幕：博弈分支 / Build Act III from trajectory and bifurcation data."""

    if not traj:
        return "轨迹数据不足，无法展开博弈树。"

    current = traj[-1]
    start = traj[0]
    total_change = (current - start) / max(abs(start), 0.01)

    lines = []

    # 基于实际数据构建分支
    if bifurcations:
        # 有分岔点——以分岔点为核心构建
        for i, bp in enumerate(bifurcations[:3]):
            if bp < len(traj):
                bp_value = traj[bp]
                lines.append(f"**分支 {i + 1}** (分岔点: 第{bp}步, 价格 {bp_value:.4f})")
                lines.append(f"  触发条件: 在第{bp}步前后，若有外部扰动（如竞争对手突然调价超过{abs(total_change) * 0.2:.1f}%），系统将偏离当前轨迹。")
                lines.append(f"  上行路径: 价格突破 {bp_value * 1.05:.4f} → 引发新一轮竞争 → 均衡上移至 {equilibrium * 1.1:.4f}")
                lines.append(f"  下行路径: 价格跌破 {bp_value * 0.95:.4f} → 触发恐慌性降价 → 均衡下移至 {equilibrium * 0.9:.4f}")
                lines.append(f"  概率估计: 上行 {40 + i * 5}% / 下行 {35 - i * 5}% / 维持 {25}%")
                lines.append("")
    else:
        # 无显著分岔点——基于轨迹趋势构建
        if total_change > 0.05:
            trend = "上行"
        elif total_change < -0.05:
            trend = "下行"
        else:
            trend = "横盘"

        lines.append(f"当前无显著分岔点，系统呈{trend}趋势。以下基于纳什收敛度（{nash:.3f}）和轨迹方向构建可能路径：")
        lines.append("")

        if nash > 0.7:
            lines.append(f"**分支 1 — 收敛到均衡** (概率: ~65%)")
            lines.append(f"  {trend}趋势延续，各方向均衡价格 {equilibrium:.4f} 靠拢。")
            lines.append(f"  策略空间收窄，先发优势减弱，竞争转向非价格维度。")
            lines.append("")
            lines.append(f"**分支 2 — 外部冲击打破均衡** (概率: ~25%)")
            shock_pct = max(abs(traj[-1] - traj[0]) / max(abs(traj[0]), 0.01) * 1.5, 5.0)
            lines.append(f"  某参与方突然采取非理性大幅调价（超过{shock_pct:.1f}%），打破当前均衡。")
            lines.append(f"  系统进入短期混沌，重新寻找新均衡点。")
            lines.append("")
            lines.append(f"**分支 3 — 默契共谋** (概率: ~10%)")
            lines.append("  各方意识到价格战无益，形成默契维持当前价格水平。")
            lines.append(f"  均衡价格 {equilibrium:.4f} 成为实际市场价格。")
        elif nash > 0.3:
            lines.append(f"**分支 1 — 加速{trend}** (概率: ~50%)")
            lines.append(f"  当前{trend}趋势加速，价格可能在未来5-10步内触及 {equilibrium * (1.1 if trend == '上行' else 0.9):.4f}。")
            lines.append(f"  建议在此位置预设应对方案。")
            lines.append("")
            lines.append(f"**分支 2 — 趋势反转** (概率: ~30%)")
            lines.append(f"  竞争对手的激进反应可能改变趋势方向。反转信号：单步变化超过近期波动率的2倍。")
            lines.append("")
            lines.append(f"**分支 3 — 震荡筑底/顶** (概率: ~20%)")
            lines.append(f"  价格在 {traj[-1] * 0.95:.4f}–{traj[-1] * 1.05:.4f} 区间内反复拉锯，等待新信息打破僵局。")
        else:
            lines.append(f"**分支 1 — 趋势延续** (概率: ~40%)")
            lines.append(f"  Lyapunov 指数 {lyap:.4f} 暗示系统对初始条件敏感。")
            lines.append(f"  {'上行' if total_change > 0 else '下行'}趋势可能惯性延续。")
            lines.append("")
            lines.append(f"**分支 2 — 反向运动** (概率: ~35%)")
            lines.append("  高不确定性环境下，方向性押注风险较大。建议采用双向对冲策略。")
            lines.append("")
            lines.append(f"**分支 3 — 跃迁到新吸引盆** (概率: ~25%)")
            lines.append("  系统可能在某个临界点跃迁到完全不同的均衡。关注波动率突然放大——这是跃迁前兆。")

    return "\n".join(lines)


def _build_act4_strategy(
    traj: List[float], lyap: float, nash: float,
    volatility: float, equilibrium: float,
    game_type: str, scenario: GCE_Scenario,
    key_events: List[Dict],
) -> str:
    """基于推演数据构建第四幕：可执行策略 / Build Act IV with actionable strategies from data."""

    if not traj:
        return "轨迹数据不足，无法生成具体策略。"

    current = traj[-1]
    start = traj[0]
    total_pct = (current - start) / max(abs(start), 0.01) * 100

    # 战略基调
    if nash > 0.8:
        posture = "巩固优势 + 非价格竞争"
    elif nash > 0.4:
        posture = "主动塑造均衡 + 抢占先机"
    else:
        posture = "快速试错 + 灵活调整"

    lines = [f"**战略基调**: {posture}", ""]

    # 即时行动 (1-3步)
    lines.append("**【即时行动】（1–3 步内执行）**")
    lines.append("")

    action_num = 1

    if game_type == "price_war":
        # 价格战的具体建议
        price_step = abs(current - equilibrium) / max(traj.index(current) if current in traj else 1, 1)
        if total_pct < -5:
            # 价格下行中
            lines.append(f"{action_num}. **设定降价底线**: 当前轨迹已下降 {total_pct:.1f}%。基于成本推断，价格下限设在 {start * 0.35:.4f}。触及此线立即停止跟随降价，转而在其他维度竞争。")
            action_num += 1
            counter_move_pct = max(abs(volatility) * 100 * 3, 2.0)
            lines.append(f"{action_num}. **非对称反击**: 不要跟随对手的降价步调。在对手降价的下一步，将价格上调 {counter_move_pct:.1f}% 同时提升服务质量信号。此举测试对手是\"价格屠夫\"还是\"理性竞争者\"。")
            action_num += 1
        elif total_pct > 5:
            lines.append(f"{action_num}. **锁定先发优势**: 当前价格已上涨 {total_pct:.1f}%。在竞争对手跟进之前，将当前价格水平与长期合同捆绑（如锁定 {scenario.time_steps // 3} 步的价格承诺）。")
            action_num += 1
        else:
            lines.append(f"{action_num}. **试探性调价**: 在当前价 {current:.4f} 基础上，向 {equilibrium * (1.02 if total_pct >= 0 else 0.98):.4f} 方向微调 {abs(volatility) * 0.5:.1f}%。观察对手反应——是跟随、反向还是忽略。将对手的反应模式记录为后续策略的输入。")
            action_num += 1

    elif game_type == "auction":
        lines.append(f"{action_num}. **锚定出价**: 当前共识价格为 {current:.4f}。在下一轮出价中，以 {current * 0.95:.4f} 作为初始锚点，观察对手是否跟随下调。若对手跟随，说明其估值弹性较大。")
        action_num += 1
        if nash < 0.5:
            lines.append(f"{action_num}. **跳价策略**: 在对手预期你小幅加价时，直接出价 {current * 1.03:.4f}（+3%）。此举可以打乱对手的增量出价节奏，迫使其重新评估估值上限。")
            action_num += 1

    elif game_type == "negotiation":
        lines.append(f"{action_num}. **设定让步节奏**: 当前谈判区间 [{min(traj):.4f}, {max(traj):.4f}]。规划未来3步的让步幅度：第1步让步 {abs(traj[-1] - traj[-2]) * 0.8 if len(traj) >= 2 else abs(total_pct) * 0.01:.4f}，第2步减半，第3步暂停——发出\"逼近底线\"的信号。")
        action_num += 1
        if len(scenario.participants) >= 3:
            lines.append(f"{action_num}. **分化谈判对手**: 在 {len(scenario.participants)} 方谈判中，识别立场最接近你目标价的一方（当前距离均衡 {equilibrium:.4f} 最近者），优先与其达成双边协议，打破多边僵局。")
            action_num += 1

    else:
        lines.append(f"{action_num}. **部署监测**: 在 Lyapunov 指数为 {lyap:.4f} 的环境下，重点监测 {(3 if lyap > 0 else 5)} 步内的轨迹变化率。若单步变化超过 {volatility * 2:.4f}，触发策略重新评估。")
        action_num += 1

    # 风险管控 (通用但数据驱动)
    lines.append("")
    lines.append(f"{action_num}. **止损触发条件**: 若轨迹偏离预期方向超过 {max(abs(total_pct) * 0.5, 10):.1f}%，立即进入\"观察模式\"——暂停主动调价，收集3步数据后重新决策。")
    action_num += 1

    # 中期布局
    lines.append("")
    lines.append("**【中期布局】（5–15 步）**")
    lines.append("")

    if nash > 0.7:
        lines.append(f"{action_num}. **均衡化运营**: 纳什收敛度已达 {nash:.3f}。将竞争焦点从价格转向非价格维度（服务质量、产品差异化、客户锁定）。价格维度的竞争空间已不大。")
        action_num += 1
    else:
        lines.append(f"{action_num}. **塑造均衡窗口**: 纳什收敛度仅 {nash:.3f}，意味着均衡尚未形成——你有机会通过主动行动将均衡引导到对自己有利的位置。目标：在未来 {scenario.time_steps // 3} 步内，将价格推移至 {equilibrium * (1.03 if total_pct >= 0 else 0.97):.4f}，使之成为新的锚点。")
        action_num += 1

    if lyap > 0.01:
        lines.append(f"{action_num}. **混沌对冲**: Lyapunov 指数 {lyap:.4f} 暗示分岔风险。准备双向应对方案——同时为价格上行和下行情景准备预案，在分岔点确认后的1步内切换至对应方案。")
        action_num += 1

    lines.append(f"{action_num}. **定期复盘节点**: 每 {max(3, scenario.time_steps // 6)} 步评估一次策略有效性，对比实际轨迹与预测轨迹的偏离度。若连续2个评估周期偏离超过 {volatility * 1.5:.3f}，重新运行完整推演。")
    action_num += 1

    lines.append("")
    lines.append(f"**【关键数字备忘】**")
    lines.append(f"  · 当前价: {current:.4f}")
    lines.append(f"  · 估计均衡: {equilibrium:.4f}")
    lines.append(f"  · 纳什收敛度: {nash:.3f}")
    lines.append(f"  · 轨迹波动率: {volatility:.4f}")
    lines.append(f"  · 距均衡距离: {abs(current - equilibrium) / max(current, 0.01) * 100:.1f}%")

    return "\n".join(lines)


# ── 大白话结论卡片 / Plain-Language Conclusion Card ──────────────────────

def _build_plain_language_card(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    domain_id: str = "",
) -> str:
    """生成大白话结论卡片 / Generate plain-language conclusion card.

    不出现任何专业术语（Lyapunov、纳什、均衡等），
    只给出"照着做就行"的具体行动方案。
    多方（3+）博弈时自动启用分层权重排名。
    """
    traj = result.consensus_trajectory
    if not traj or len(traj) < 2:
        return ""

    current = traj[-1]
    start = traj[0]
    total_pct = (current - start) / max(abs(start), 0.01) * 100
    nash = result.nash_convergence
    equilibrium = result.equilibrium_estimate
    volatility = result.trajectory_volatility
    game_type = result.game_type
    player_traj = result.participant_trajectories or {}

    # 获取领域上下文 / Get domain context
    template = None
    if domain_id:
        from gce.interface.GCE_domain_templates import GCE_get_template_by_id
        template = GCE_get_template_by_id(domain_id)

    # ── 参与方分析：谁在冲？谁在退？ / Player analysis ──
    player_roles: List[Dict[str, Any]] = []
    for name, pt in player_traj.items():
        if len(pt) < 2:
            continue
        pct = (pt[-1] - pt[0]) / max(abs(pt[0]), 0.01) * 100
        player_roles.append({
            "name": name,
            "pct": pct,
            "start": pt[0],
            "end": pt[-1],
            "role": "attacker" if pct > 5 else ("defender" if pct < -5 else "neutral"),
        })
    player_roles.sort(key=lambda x: x["pct"], reverse=True)

    attacker = player_roles[0] if player_roles else None
    defender = player_roles[-1] if len(player_roles) > 1 else None
    is_multi = len(player_roles) >= 3
    ranked = _compute_multi_party_weights(player_roles) if is_multi else []

    # ── 根据领域选择语言风格 / Select language style by domain ──
    lang = _get_plain_language_context(domain_id, game_type)

    # ── 构建卡片 / Build card ──
    lines = [
        "─" * 50,
        f"  {lang['card_title']}",
        "─" * 50,
        "",
    ]

    # 一句话策略
    lines.append(f"**一句话策略**：")
    if is_multi:
        lines.append(_build_multi_one_liner(ranked, lang, total_pct))
    else:
        lines.append(_build_one_liner(
            attacker, defender, equilibrium, current, total_pct, nash, lang, game_type,
            scenario.participants,
        ))
    lines.append("")

    # 为什么这么分
    lines.append(f"**为什么这么分？**")
    if is_multi:
        lines.extend(_build_multi_why_section(ranked, start, current, equilibrium, lang))
    else:
        lines.extend(_build_why_section(
            attacker, defender, start, current, equilibrium, total_pct, nash, lang,
        ))
    lines.append("")

    # 具体操作
    lines.append(f"**接下来具体怎么操作（人话版）**")
    if is_multi:
        lines.extend(_build_multi_plain_actions(ranked, current, equilibrium, volatility, total_pct, nash, lang, scenario))
    else:
        lines.extend(_build_plain_actions(
            attacker, defender, current, equilibrium, volatility, total_pct,
            nash, lang, game_type, scenario,
        ))
    lines.append("")

    # 最直白的总结
    lines.append(f"**最直白的总结**：")
    if is_multi:
        lines.append(_build_multi_plain_summary(ranked, lang))
    else:
        lines.append(_build_plain_summary(
            attacker, defender, total_pct, nash, equilibrium, lang, game_type,
        ))

    # 多方权重详情表 / Multi-party weight breakdown
    if is_multi:
        lines.append("")
        lines.append("**各参与方权重排名**：")
        for i, p in enumerate(ranked):
            direction = "↑" if p["pct"] > 0 else ("↓" if p["pct"] < 0 else "→")
            lines.append(
                f"  {i+1}. {p['name']} [{p['tier_name']}] "
                f"变化{direction}{abs(p['pct']):.0f}% — 建议份额约{p['share_pct']}%"
            )

    return "\n".join(lines)


def _compute_multi_party_weights(
    player_roles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """为多方博弈计算分层权重 / Compute tiered weights for multi-party games.

    权重逻辑：正向动量得高分 → 值得投入更多；负向动量得低分 → 只给兜底。
    """
    n = len(player_roles)
    if n <= 2:
        return player_roles

    # 方向感知的动量得分：正向加分，负向打折
    momentums = []
    for p in player_roles:
        raw = p["pct"]
        if raw > 0:
            score = raw  # 正向完全计入
        else:
            score = raw * 0.3  # 负向打折（绝对值大不代表值得投入）
        momentums.append(score)

    # 按得分排序（高到低）
    sorted_indices = sorted(range(n), key=lambda i: momentums[i], reverse=True)

    if n == 3:
        tier_pcts = [0.55, 0.28, 0.17]
    elif n == 4:
        tier_pcts = [0.50, 0.25, 0.15, 0.10]
    else:
        tier_pcts = ([0.45, 0.25, 0.15, 0.10, 0.05])[:n]

    tiers = []
    for i, si in enumerate(sorted_indices):
        p = player_roles[si].copy()
        pct = p["pct"]
        # 数据驱动的层级命名 / Data-driven tier naming
        if i == 0:
            p["tier_name"] = "主力" if pct > 5 else "相对最优"
        elif pct > 5:
            p["tier_name"] = "次主力"
        elif pct > -5:
            p["tier_name"] = "维持"
        elif pct > -15:
            p["tier_name"] = "防守"
        else:
            p["tier_name"] = "兜底"
        p["share_pct"] = round(tier_pcts[i] * 100) if i < len(tier_pcts) else 5
        p["momentum"] = momentums[si]
        tiers.append(p)

    return tiers


def _build_multi_one_liner(
    ranked: List[Dict[str, Any]],
    lang: Dict[str, str],
    total_pct: float,
) -> str:
    """多方一句话：分层分配策略 / Multi-party one-liner with tiered allocation."""
    time_hint = "未来一年" if "月" in str(total_pct) else "下一阶段"
    review_hint = "每半年" if "月" in str(total_pct) else "每个周期"

    parts = []
    for p in ranked:
        if p["tier_name"] in ("主力", "次主力"):
            parts.append(f"{p['name']}拿大头（约{p['share_pct']}%）")
        elif p["tier_name"] == "维持":
            parts.append(f"{p['name']}维持现状（约{p['share_pct']}%）")
        else:
            parts.append(f"{p['name']}托底（约{p['share_pct']}%）")

    tier_str = "，".join(parts)
    return (
        f"{time_hint}，把可调配的{lang['resource_unit']}分层分配：{tier_str}。"
        f"然后{review_hint}根据实际效果微调一次。"
    )


def _build_multi_why_section(
    ranked: List[Dict[str, Any]],
    start: float,
    current: float,
    equilibrium: float,
    lang: Dict[str, str],
) -> List[str]:
    """多方"为什么"段落 / Multi-party "why" section."""
    lines = []
    for p in ranked:
        direction = "上升" if p["pct"] > 0 else "下降"
        if p["pct"] > 5:
            lines.append(
                f"{p['name']}势头正猛（指标{direction}了{abs(p['pct']):.0f}%），"
                f"每一份{lang['resource_unit']}投给它的回报率最高，应该拿最大份额。"
            )
        elif p["pct"] > -5:
            lines.append(
                f"{p['name']}变化不大（{direction}{abs(p['pct']):.0f}%），"
                f"保持现有投入就够，不需要大动作。"
            )
        else:
            lines.append(
                f"{p['name']}正在后退（{direction}{abs(p['pct']):.0f}%），"
                f"保留最低限度的{lang['resource_unit']}防止崩盘即可，不宜追加。"
            )
    return lines


def _build_multi_plain_actions(
    ranked: List[Dict[str, Any]],
    current: float,
    equilibrium: float,
    volatility: float,
    total_pct: float,
    nash: float,
    lang: Dict[str, str],
    scenario: GCE_Scenario,
) -> List[str]:
    """多方操作步骤 / Multi-party action steps."""
    lines = []

    lines.append("**立即**：")
    for p in ranked:
        if p["tier_name"] == "主力":
            lines.append(
                f"  - {p['name']}：把份额拉到总盘约{p['share_pct']}%，集中火力推上去。"
            )
        elif p["tier_name"] == "维持":
            lines.append(
                f"  - {p['name']}：维持约{p['share_pct']}%份额，不增不减，静观其变。"
            )
        else:
            lines.append(
                f"  - {p['name']}：保留约{p['share_pct']}%兜底，避免彻底崩盘。"
            )

    lines.append("")
    lines.append("**盯住两个数字**：")
    vol_threshold = max(abs(volatility) * 100, 1.5)
    lines.append(
        f"- 如果{lang['metric_name']}{lang['metric_unit']}的单{'月' if '月' in str(total_pct) else '周期'}变化"
        f"掉到{vol_threshold:.1f}%以下，就开会重新研究是不是哪里出问题了。"
    )
    shock_threshold = max(abs(total_pct) * 0.5, 10)
    lines.append(
        f"- 如果整个轨迹偏离现在预测的方向超过{shock_threshold:.0f}%，"
        f"马上暂停所有大动作，先观察一段时间再说。"
    )

    if equilibrium > 0 and abs(equilibrium - current) / max(abs(current), 0.01) > 0.02:
        time_steps = max(10, scenario.time_steps // 3)
        lines.append("")
        lines.append(
            f"**中期目标**：争取在{time_steps}个时间单位左右，"
            f"把{lang['metric_name']}推到{equilibrium * 1.03:.1f}附近。"
            f"到了这个数，比例可能需要重新调整。"
        )

    return lines


def _build_multi_plain_summary(
    ranked: List[Dict[str, Any]],
    lang: Dict[str, str],
) -> str:
    """多方直白总结 / Multi-party plain-language summary."""
    主力 = [p for p in ranked if p["tier_name"] == "主力"]
    兜底 = [p for p in ranked if p["tier_name"] in ("防守", "兜底")]
    if 主力 and 兜底:
        return (
            f"现在的局势就像打仗：{主力[0]['name']}是冲在最前面的先锋，"
            f"资源应该优先倾斜给它。{兜底[0]['name']}是最后一道防线，"
            f"留一点{lang['resource_unit']}别让它垮就行。"
            f"中间的几个保持现状观望，等局势明朗了再调。"
        )
    elif 主力:
        return (
            f"现在的局势，{主力[0]['name']}是{lang['attacker_metaphor']}。"
            f"顺势而为，先把{lang['resource_unit']}集中在它身上，等信号明确了再调整。"
        )
    else:
        return "各方暂时势均力敌，别急着梭哈，先观察、再行动。"


def _get_plain_language_context(domain_id: str, game_type: str) -> Dict[str, str]:
    """根据领域返回大白话语言包 / Return plain-language phrases by domain."""
    contexts = {
        "planetary_ecology": {
            "card_title": "保护资金分配结论卡",
            "resource_unit": "保护资金",
            "resource_verb": "拨给",
            "metric_name": "综合生态指数",
            "metric_unit": "",
            "action_context": "在下一批保护资金的分配表上",
            "monitor_context": "种群数量和栖息地质量",
            "attacker_metaphor": "发起冲锋的战士",
            "defender_metaphor": "在战壕里防守的士兵",
            "win_metaphor": "冲上去了，整个防线才能稳住",
            "ratio_hint": "按大概7:3的比例，大头给进攻方，小头给防守方维持基本盘",
        },
        "micro_individual": {
            "card_title": "精力分配结论卡",
            "resource_unit": "精力/时间",
            "resource_verb": "投入到",
            "metric_name": "综合满意度指数",
            "metric_unit": "",
            "action_context": "在每天的时间安排上",
            "monitor_context": "每周的精力状态和工作/健康指标",
            "attacker_metaphor": "正在加速成长的领域",
            "defender_metaphor": "需要维持基本盘的方面",
            "win_metaphor": "稳住了大局，其他方面才有空间改善",
            "ratio_hint": "按大概6:4的比例，多数精力给回报率最高的维度",
        },
        "social_network": {
            "card_title": "关系处理结论卡",
            "resource_unit": "沟通精力/诚意",
            "resource_verb": "投向",
            "metric_name": "关系改善指数",
            "metric_unit": "",
            "action_context": "在接下来的沟通中",
            "monitor_context": "对方的反应和关系温度变化",
            "attacker_metaphor": "先伸出手的人",
            "defender_metaphor": "还在观望的另一方",
            "win_metaphor": "先破冰，关系才能回暖",
            "ratio_hint": "主动方承担七成的破冰成本，被动方保留三成的回应空间",
        },
        "creative_entertainment": {
            "card_title": "内容投入分配结论卡",
            "resource_unit": "创作资源",
            "resource_verb": "倾斜给",
            "metric_name": "综合影响力指数",
            "metric_unit": "",
            "action_context": "在下一阶段的内容排期中",
            "monitor_context": "关注度数据和粉丝活跃度",
            "attacker_metaphor": "正在上升期的黑马",
            "defender_metaphor": "守成期的老牌IP",
            "win_metaphor": "先把上升期的推上去，整个盘子才能做大",
            "ratio_hint": "按大概7:3的比例，上升期IP拿大头，老牌IP维持基本曝光",
        },
        "enterprise": {
            "card_title": "预算分配结论卡",
            "resource_unit": "预算",
            "resource_verb": "分配给",
            "metric_name": "组织效能指数",
            "metric_unit": "",
            "action_context": "在下一季度的预算编制中",
            "monitor_context": "各部门的KPI达成率和协同效率",
            "attacker_metaphor": "冲在最前面的业务部门",
            "defender_metaphor": "负责稳住基本盘的支撑部门",
            "win_metaphor": "前锋冲开市场，后防才能从容布局",
            "ratio_hint": "按大概6:4的比例，增长型部门拿大头，维持型部门保基本",
        },
        "urban_infrastructure": {
            "card_title": "调度优化结论卡",
            "resource_unit": "运力/服务资源",
            "resource_verb": "调配到",
            "metric_name": "系统负载均衡度",
            "metric_unit": "%",
            "action_context": "在下一周期的调度计划中",
            "monitor_context": "各节点的实时负载率和市民投诉量",
            "attacker_metaphor": "承载压力最大的枢纽节点",
            "defender_metaphor": "负载相对较轻的辅助节点",
            "win_metaphor": "把最堵的地方疏通了，整个系统才能顺畅运转",
            "ratio_hint": "运力优先给负载率最高的节点，降到一个安全值后再均匀分配",
        },
        "meta_civilization": {
            "card_title": "论证策略结论卡",
            "resource_unit": "论证资源/发表机会",
            "resource_verb": "集中到",
            "metric_name": "学术影响力指数",
            "metric_unit": "",
            "action_context": "在下一阶段的学术发表和会议中",
            "monitor_context": "引用率和学界讨论热度",
            "attacker_metaphor": "势头正盛的新范式",
            "defender_metaphor": "仍有影响力的旧范式",
            "win_metaphor": "新范式站稳脚跟，整个领域的认知才能升级",
            "ratio_hint": "按大概7:3的比例，上升期的范式拿主要论证资源",
        },
    }

    # 默认通用语境 / Default generic context
    default_context = {
        "card_title": "资源分配结论卡",
        "resource_unit": "资源",
        "resource_verb": "投入到",
        "metric_name": "综合指数",
        "metric_unit": "",
        "action_context": "在下一步的决策中",
        "monitor_context": "关键指标变化",
        "attacker_metaphor": "势头最强的一方",
        "defender_metaphor": "处于守势的一方",
        "win_metaphor": "让能赢的先赢，稳住大盘",
        "ratio_hint": "按大概7:3的比例",
    }

    return contexts.get(domain_id, default_context)


def _build_one_liner(
    attacker: Optional[Dict],
    defender: Optional[Dict],
    equilibrium: float,
    current: float,
    total_pct: float,
    nash: float,
    lang: Dict[str, str],
    game_type: str,
    participants: List[Any],
) -> str:
    """生成一句话核心策略 / Generate one-line core strategy."""
    if attacker and defender and attacker["role"] == "attacker":
        ratio = abs(attacker["pct"]) / max(abs(attacker["pct"]) + abs(defender["pct"]), 1)
        major_pct = max(60, min(80, int(ratio * 100 + 10)))
        minor_pct = 100 - major_pct
        attacker_name = attacker["name"]
        defender_name = defender["name"]
        # 使用领域语言
        time_hint = "未来一年" if "月" in str(total_pct) else "下一阶段"
        review_hint = "每半年" if "月" in str(total_pct) else "每个周期"
        return (
            f"{time_hint}，把可调配的{lang['resource_unit']}，"
            f"按大概{major_pct}:{minor_pct}的比例，"
            f"大头给{attacker_name}，小头给{defender_name}。"
            f"然后{review_hint}根据实际效果微调一次。"
        )
    elif attacker:
        return (
            f"当前局势下，把{lang['resource_unit']}集中{lang['resource_verb']}"
            f"{attacker['name']}——它是最活跃的变量，先把它推到稳定位。"
        )
    else:
        return f"当前各方势均力敌，保持{lang['resource_unit']}均衡分配，等待信号明确后再倾斜。"


def _build_why_section(
    attacker: Optional[Dict],
    defender: Optional[Dict],
    start: float,
    current: float,
    equilibrium: float,
    total_pct: float,
    nash: float,
    lang: Dict[str, str],
) -> List[str]:
    """生成"为什么"段落 / Generate "why" paragraphs."""
    lines = []
    if attacker and attacker["role"] == "attacker":
        pct_str = f"涨了将近{abs(attacker['pct']):.0f}%" if attacker["pct"] > 0 else f"降了{abs(attacker['pct']):.0f}%"
        direction = "上升" if attacker["pct"] > 0 else "下降"
        lines.append(
            f"系统推演表明，{attacker['name']}现在正处于\"猛烈反攻\"阶段，"
            f"给它的每一份{lang['resource_unit']}，转化成整体提升的效率更高"
            f"（指标{direction}了{abs(attacker['pct']):.0f}%）。"
        )
    if defender and defender["role"] == "defender":
        lines.append(
            f"{defender['name']}目前处于守势，直接砸{lang['resource_unit']}跟{attacker['name'] if attacker else '对手'}"
            f"硬拼效果不好，不如先把势头好的推上一个健康台阶，把整个盘面的\"底盘\"稳住。"
        )
    if equilibrium > 0:
        gap_pct = abs(equilibrium - current) / max(abs(current), 0.01) * 100
        if gap_pct > 5:
            lines.append(
                f"系统算出的稳定平衡点约在{equilibrium:.1f}（这是一个{lang['metric_name']}），"
                f"而现在才{current:.1f}起步，说明总体上{lang['resource_unit']}投入力度还得加大。"
                f"在总和{lang['resource_unit']}有限的情况下，\"先让能赢的赢\"是对所有参与方都负责的做法。"
            )
    return lines


def _build_plain_actions(
    attacker: Optional[Dict],
    defender: Optional[Dict],
    current: float,
    equilibrium: float,
    volatility: float,
    total_pct: float,
    nash: float,
    lang: Dict[str, str],
    game_type: str,
    scenario: GCE_Scenario,
) -> List[str]:
    """生成可操作的具体步骤（人话版）/ Generate plain-language action steps."""
    lines = []

    # 立即行动
    if attacker and defender and attacker["role"] == "attacker":
        ratio = max(60, min(80, int(abs(attacker["pct"]) / max(abs(attacker["pct"]) + abs(defender["pct"]), 1) * 100 + 10)))
        lines.append(
            f"**立即**：{lang['action_context']}，"
            f"把{attacker['name']}的份额拉到总盘的大概七成左右，"
            f"{defender['name']}保留三成用于维持现有水平、避免进一步下滑。"
        )

    # 盯住数字
    lines.append("")
    lines.append("**盯住两个数字**：")
    vol_threshold = max(abs(volatility) * 100, 1.5)
    lines.append(
        f"- 如果{lang['metric_name']}{lang['metric_unit']}的单{'月' if '月' in str(total_pct) else '周期'}变化"
        f"掉到{vol_threshold:.1f}%以下，就开会重新研究是不是哪里出问题了。"
    )
    shock_threshold = max(abs(total_pct) * 0.5, 10)
    lines.append(
        f"- 如果整个轨迹偏离现在预测的方向超过{shock_threshold:.0f}%，"
        f"马上暂停所有大动作，先观察一段时间再说。"
    )

    # 中期目标
    if equilibrium > 0 and abs(equilibrium - current) / max(abs(current), 0.01) > 0.02:
        time_steps = max(10, scenario.time_steps // 3)
        lines.append("")
        lines.append(
            f"**中期目标**：争取在{time_steps}个时间单位左右，"
            f"把{lang['metric_name']}推到{equilibrium * 1.03:.1f}附近。"
            f"到了这个数，就进入更稳固的平衡区了，到时候再重新评估，可能比例会调回更均衡。"
        )

    return lines


def _build_plain_summary(
    attacker: Optional[Dict],
    defender: Optional[Dict],
    total_pct: float,
    nash: float,
    equilibrium: float,
    lang: Dict[str, str],
    game_type: str,
) -> str:
    """生成最直白的总结类比 / Generate plain-language summary with metaphor."""
    if attacker and defender:
        a_name = attacker["name"]
        d_name = defender["name"]
        a_metaphor = lang["attacker_metaphor"]
        d_metaphor = lang["defender_metaphor"]
        win = lang["win_metaphor"]
        return (
            f"现在的局势，就好比{a_name}是那个{a_metaphor}，"
            f"{d_name}还是{d_metaphor}。"
            f"这时你送{lang['resource_unit']}，肯定优先送给冲在最前面的那位。"
            f"不是放弃{d_name}，而是只有{a_name}{win}，"
            f"{d_name}才有机会喘过气来。"
        )
    elif attacker:
        return (
            f"现在的局势，{attacker['name']}是{lang['attacker_metaphor']}。"
            f"顺势而为，先把{lang['resource_unit']}集中在它身上，等信号明确了再调整。"
        )
    else:
        return "各方暂时势均力敌，别急着梭哈，先观察、再行动。"


# ── 模板加载（保留兼容性）/ Template loading (kept for compatibility) ─────

def _load_narrative_template(path: Optional[str]) -> Optional[str]:
    """从YAML文件加载叙事模板 / Load narrative template from YAML file."""
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "template" in data:
                    return str(data["template"])
        except Exception as e:
            logger.warning("Failed to load narrative template: %s", e)
    return None
