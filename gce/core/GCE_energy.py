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

"""能量管理器 —— 独立线程，评估预测、更新能量、淘汰死亡博弈元 / Energy manager -- independent thread, evaluates predictions, updates energy, eliminates dead agents."""

from __future__ import annotations

import logging
import os
import signal
import time
from typing import Any, Dict, List, Optional

from gce.storage.GCE_repository import (
    GCE_get_agents_above_energy,
    GCE_get_agents_below_energy,
    GCE_get_unprocessed_predictions,
    GCE_mark_prediction_processed,
    GCE_set_agent_status,
    GCE_update_energy,
)

logger = logging.getLogger("gce.core.GCE_energy")


def GCE_energy_loop(
    db_path: str,
    config: Dict[str, Any],
    shutdown_flag,  # type: ignore[no-untyped-def]
    agent_processes: Dict[str, Any],
) -> None:
    """能量管理器线程 / Energy manager thread.

    每个 tick 执行：
    1. 根据实际值评估待处理的预测
    2. 基于预测准确度奖励/惩罚能量
    3. 淘汰能量 <= 0 的博弈元
    4. 标记能量 >= 阈值的博弈元用于繁殖 /
    Each tick:
    1. Evaluate pending predictions against actual values.
    2. Award/penalize energy based on prediction accuracy.
    3. Kill agents with energy <= 0.
    4. Flag agents with energy >= threshold for breeding.
    """
    evo_cfg = config.get("evolution", {})
    base_reward = evo_cfg.get("base_reward", 10.0)
    error_scale = evo_cfg.get("error_scale", 2.0)
    reproduce_threshold = evo_cfg.get("reproduce_threshold", 200.0)
    energy_tick = evo_cfg.get("energy_tick_seconds", 1.0)

    while not shutdown_flag.is_set():
        try:
            # 1. 处理待处理的预测 / Process pending predictions
            pending = GCE_get_unprocessed_predictions(db_path)
            for pred in pending:
                pred_id = pred["id"]
                agent_id = pred["agent_id"]
                predicted = pred.get("predicted_value")
                real = pred.get("real_value")

                if predicted is None or real is None:
                    GCE_mark_prediction_processed(db_path, pred_id, 0.0)
                    continue

                error = abs(predicted - real)
                reward = base_reward * max(0.0, 1.0 - error / error_scale)
                GCE_update_energy(db_path, agent_id, reward)
                GCE_mark_prediction_processed(db_path, pred_id, reward)
                logger.debug("Agent %s prediction %d: error=%.4f reward=%.4f",
                             agent_id, pred_id, error, reward)

            # 2. 淘汰已死亡的博弈元 / Eliminate dead agents
            dead = GCE_get_agents_below_energy(db_path, 0.0)
            for ag in dead:
                agent_id = ag["id"]
                pid = ag.get("process_pid")
                GCE_set_agent_status(db_path, agent_id, "dead")
                GCE__kill_agent_process(agent_id, pid, agent_processes)
                logger.info("Agent %s eliminated (energy=%.2f)", agent_id, ag["energy"])

            # 3. 繁殖候选：能量高于阈值的博弈元 / Breeding candidates: agents above threshold
            candidates = GCE_get_agents_above_energy(db_path, reproduce_threshold)
            if candidates:
                logger.debug("Breeding candidates: %d agents above %.1f energy",
                             len(candidates), reproduce_threshold)

        except Exception:
            logger.exception("Energy manager error")

        shutdown_flag.wait(timeout=energy_tick)

    logger.info("Energy manager stopped")


def GCE__kill_agent_process(agent_id: str, pid: Optional[int], agent_processes: Dict[str, Any]) -> None:
    """向博弈元进程发送 SIGTERM 信号并清理进程表 / Send SIGTERM to an agent process and clean up the process table."""
    if pid is None:
        proc = agent_processes.pop(agent_id, None)
        if proc and proc.is_alive():
            pid = proc.pid
        else:
            return

    try:
        if pid is not None:
            os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # 已经死亡 / Already dead
    except Exception:
        logger.exception("Failed to kill agent %s (pid=%s)", agent_id, pid)

    agent_processes.pop(agent_id, None)
