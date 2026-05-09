#
# -*- coding: utf-8 -*-
#
#
# Gaming Chaos Engine V0.1.0 – A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# Contact:
#   Email: i126@126.com
#   Website: wop.cc
#
# LICENSE TERMS
# =============
# This software and associated documentation files (the "Software") are
# proprietary and protected by copyright law. The copyright holder
# grants you a limited, non-exclusive, non-transferable license to use,
# copy, and modify the Software solely for non-commercial, personal
# purposes, subject to the following conditions:
#
# 1. You must retain the above copyright notice, this list of conditions,
#    and the following disclaimer in all copies or substantial portions
#    of the Software.
# 2. You may not use the Software, or any derivative works based upon it,
#    for any commercial purpose without obtaining a separate commercial
#    license from the copyright holder.
# 3. Redistribution of the Software or derivative works, whether in
#    source or binary form, is prohibited without prior written
#    permission, except as part of non-commercial personal use.
#
# "Commercial purpose" includes, but is not limited to: using the
# Software (a) in any product or service sold or made available for a
# fee; (b) as part of any commercial activity intended to generate
# revenue, including internal business operations; (c) by any entity
# that is a for-profit organization or operates in a commercial context.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# For commercial licensing inquiries, please contact:
#   Email: i126@126.com
#   Website: wop.cc
#
# ─────────────────────────────────────
#
# 博弈混沌引擎 V0.1.0 – 用于博弈与仿真的混沌引擎
# 版权所有 (C) 2026  Adetion
# 保留所有权利。
#
# 联系方式：
#   邮箱：i126@126.com
#   网站：wop.cc
#
# 许可条款
# ========
# 本软件及相关文档（以下简称"软件"）为专有软件，受版权法保护。
# 版权持有人授予您一项有限的、非排他的、不可转让的许可，允许您
# 仅为个人非商业目的使用、复制和修改本软件，但必须遵守以下条件：
#
# 1. 您必须在软件的所有副本或重要部分中保留上述版权声明、本条件
#    列表以及随附的免责声明。
# 2. 未经版权持有人事先书面授权，您不得将本软件或其衍生作品用于
#    任何商业目的。如需商用，必须单独获得商用许可。
# 3. 除个人非商业使用场景外，禁止以源代码或二进制形式再分发本软件
#    或其衍生作品，除非事先获得书面许可。
#
# "商业目的"包括但不限于：(a) 将软件用于任何收费产品或服务中；
# (b) 作为任何以营利或产生收入为目的的商业活动的一部分，包括内部
# 业务运营；(c) 由营利性实体或在商业环境中运营的实体使用。
#
# 本软件按"原样"提供，不提供任何明示或暗示的保证，包括但不限于
# 对适销性、特定目的适用性和非侵权的保证。在任何情况下，版权
# 持有人均不对因使用或无法使用本软件而产生的任何索赔、损害或
# 其他责任负责，无论是合同、侵权还是其他方面。
#
# 如需获取商业许可，请联系：
#   邮箱：i126@126.com
#   网站：wop.cc

"""推演引擎 —— 精英博弈元短期迭代预测. / Simulation engine — short-term iterative forecasting using elite agents."""

from __future__ import annotations

import logging
import statistics
from typing import Any, Callable, Dict, List, Optional

from gce.core.GCE_forager import GCE_Forager
from gce.core.GCE_gene import GCE_deserialize_gene
from gce.core.GCE_predictor import GCE_Predictor
from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
from gce.simulation.GCE_lyapunov import GCE_estimate_lyapunov, GCE_perturbation_analysis
from gce.simulation.GCE_schemas import GCE_Scenario, GCE_SimulationResult
from gce.storage.GCE_repository import GCE_get_elite_agents, GCE_get_agent_gene_blob

logger = logging.getLogger("gce.simulation.GCE_engine")


def GCE_run_simulation(
    scenario: GCE_Scenario,
    db_path: str,
    config: Dict[str, Any],
) -> Optional[GCE_SimulationResult]:
    """使用精英智能体运行沙盒推演. / Run a sandbox simulation using elite agents.

    1. 按能量选择 K 个精英智能体. / Select K elite agents by energy.
    2. 用 scenario.initial_prices 初始化虚拟环境. / Initialize a virtual environment from scenario.initial_prices.
    3. 对未来每一步，让每个精英独立 GCE_predict. / For each future step, have each elite GCE_predict independently.
    4. 形成共识轨迹（精英预测的中位数）. / Form consensus trajectory (median of elite predictions).
    5. 计算李雅普诺夫指数和分叉点. / Compute Lyapunov exponent and bifurcation points.

    如果没有精英智能体可用，返回 None. / Returns None if no elite agents are available.
    """
    sim_cfg = config.get("simulation", {})
    elite_count = sim_cfg.get("elite_count", 10)
    future_steps = scenario.time_steps
    epsilon = sim_cfg.get("perturbation_epsilon", 0.001)
    divergence_threshold = sim_cfg.get("divergence_threshold", 0.5)
    window_size = config.get("evolution", {}).get("window_size", 20)

    # 1. 获取精英智能体 / Get elite agents
    elites = GCE_get_elite_agents(db_path, elite_count)
    if not elites:
        logger.warning("No active agents available for simulation")
        return None

    # 反序列化精英基因 / Deserialize elite genes
    elite_predictors: List[GCE_Predictor] = []
    elite_masks: List[int] = []
    for agent in elites:
        blob = GCE_get_agent_gene_blob(db_path, agent["id"])
        if blob is None:
            continue
        gene = GCE_deserialize_gene(blob)
        elite_predictors.append(GCE_Predictor(tree=gene.tree))
        elite_masks.append(gene.mask)

    if not elite_predictors:
        logger.warning("No elite genes could be deserialized")
        return None

    # 2. 用场景初始价格初始化虚拟环境 / Initialize virtual environment with scenario's initial prices
    # 从初始价格构建虚拟事件历史 / We build a virtual event history from initial_prices
    virtual_history: List[GCE_RawEvent] = []
    base_ts = 0  # 虚拟时间戳 / Virtual timestamp
    for i, price in enumerate(scenario.initial_prices):
        virtual_history.append(GCE_RawEvent(
            source_id="price",
            event_type=GCE_EventType.NUMERIC,
            timestamp=base_ts + i,
            value=price,
        ))

    # 3. 向前推演 / Simulate forward
    consensus_trajectory: List[float] = []
    all_elite_predictions: Dict[int, List[float]] = {}

    # 使用最后一个价格作为当前值 / Use the last price as the current
    current_prices = list(scenario.initial_prices)

    for step in range(future_steps):
        step_predictions: List[float] = []

        for i, predictor in enumerate(elite_predictors):
            mask = elite_masks[i]

            # 用虚拟历史构建采集器 / Build forager with the virtual history
            forager = GCE_Forager(mask=mask, window_size=window_size)
            for event in virtual_history:
                forager.GCE_update(event)

            features = forager.GCE_extract()
            if features is None:
                continue

            result = predictor.GCE_predict(features)
            if result is not None:
                pred_value, _ = result
                step_predictions.append(pred_value)
                all_elite_predictions.setdefault(i, []).append(pred_value)

        if step_predictions:
            consensus = statistics.median(step_predictions)
        else:
            # 没有有效预测：沿用上一个已知价格 / No valid prediction: carry forward last known price
            consensus = consensus_trajectory[-1] if consensus_trajectory else scenario.initial_prices[-1]

        consensus_trajectory.append(consensus)
        current_prices.append(consensus)

        # 为此预测价格创建一个虚拟事件 / Create a virtual event for this predicted price
        virtual_history.append(GCE_RawEvent(
            source_id="price",
            event_type=GCE_EventType.NUMERIC,
            timestamp=base_ts + len(scenario.initial_prices) + step,
            value=consensus,
        ))

    # 4. 李雅普诺夫估计 / Lyapunov estimation
    lyap = GCE_estimate_lyapunov(consensus_trajectory, tau=1, dim=3)

    # 5. 微扰分析 / Perturbation analysis
    def GCE__sim_from_state(state: List[float], steps: int) -> List[float]:
        """从给定初始状态重新 GCE_simulate. / Re-GCE_simulate from a given initial state."""
        local_history = list(virtual_history[:len(scenario.initial_prices)])
        traj: List[float] = []
        for s in range(steps):
            preds: List[float] = []
            for i, predictor in enumerate(elite_predictors):
                mask = elite_masks[i]
                forager = GCE_Forager(mask=mask, window_size=window_size)
                for evt in local_history:
                    forager.GCE_update(evt)
                feats = forager.GCE_extract()
                if feats is None:
                    continue
                res = predictor.GCE_predict(feats)
                if res is not None:
                    preds.append(res[0])
            pred = statistics.median(preds) if preds else (traj[-1] if traj else state[-1])
            traj.append(pred)
            local_history.append(GCE_RawEvent(
                source_id="price",
                event_type=GCE_EventType.NUMERIC,
                timestamp=0,
                value=pred,
            ))
        return traj

    # 针对扰动，从场景适配初始状态 / For perturbation, adapt initial state from scenario
    init_state = scenario.initial_prices[:3] if len(scenario.initial_prices) >= 3 else scenario.initial_prices + [scenario.initial_prices[-1]] * (3 - len(scenario.initial_prices))

    def GCE__initial_state_fn() -> List[float]:
        return init_state

    bifurcations = GCE_perturbation_analysis(
        GCE_initial_state=GCE__initial_state_fn,
        simulate_fn=GCE__sim_from_state,
        epsilon=epsilon,
        threshold=divergence_threshold,
        steps=future_steps,
    )

    # 构建精英策略摘要 / Build elite strategy summary
    strategy_summary: Dict[str, Any] = {
        "elite_count": len(elite_predictors),
        "prediction_distribution": {
            f"agent_{i}": {
                "mean": statistics.mean(preds) if preds else 0.0,
                "stdev": statistics.stdev(preds) if len(preds) >= 2 else 0.0,
            }
            for i, preds in all_elite_predictions.items()
        },
    }

    return GCE_SimulationResult(
        consensus_trajectory=consensus_trajectory,
        lyapunov_estimate=lyap,
        bifurcation_points=bifurcations,
        elite_strategies=strategy_summary,
    )
