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

"""博弈元主循环 —— 独立进程入口 / Agent main loop -- independent process entry point."""

from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import time
from queue import Empty
from typing import Any, Dict

from gce.core.GCE_forager import GCE_Forager
from gce.core.GCE_gene import GCE_Gene
from gce.core.GCE_predictor import GCE_Predictor
from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
from gce.storage.GCE_repository import (
    GCE_get_agent_energy,
    GCE_insert_prediction,
)

logger = logging.getLogger("gce.core.GCE_agent")


def GCE_agent_main(
    agent_id: str,
    gene: GCE_Gene,
    env_queue: multiprocessing.Queue,  # type: ignore[type-arg]
    db_path: str,
    config: Dict[str, Any],
) -> None:
    """单个博弈元进程的入口点 / Entry point for a single agent process.

    循环：消费事件 -> 觅食器更新 -> 提取特征 -> 预测 -> 存储 /
    Loop: consume event -> forager update -> extract features -> predict -> store.
    当能量降至 0 或收到关闭信号时退出 / Exits when energy reaches 0 or shutdown signal is received.
    """
    # 在子进程中屏蔽中断信号 / Suppress interrupt in child processes
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, lambda signum, frame: GCE__handle_shutdown())

    tick_interval = config.get("environment", {}).get("simulator", {}).get("tick_interval", 0.5)
    window_size = config.get("evolution", {}).get("window_size", 20)

    forager = GCE_Forager(mask=gene.mask, window_size=window_size)
    predictor = GCE_Predictor(tree=gene.tree)

    energy = config.get("evolution", {}).get("initial_energy", 100.0)
    running = True

    logger.debug("Agent %s started (mask=0x%x, nodes=%d)",
                 agent_id, gene.mask, gene.tree.GCE_to_dict())

    while running and energy > 0.0:
        try:
            event = env_queue.get(timeout=1.0)
        except Empty:
            # 无事件可用 —— 检查能量并继续循环 / No event available — check energy and continue
            energy = GCE__refresh_energy(db_path, agent_id)
            if energy <= 0.0:
                logger.info("Agent %s energy depleted, exiting", agent_id)
                break
            continue
        except EOFError:
            logger.info("Agent %s event queue closed, exiting", agent_id)
            break

        try:
            forager.GCE_update(event)

            features = forager.GCE_extract()
            if features is None:
                energy = GCE__refresh_energy(db_path, agent_id)
                if energy <= 0.0:
                    break
                time.sleep(tick_interval)
                continue

            # 预测下一个时间戳的值 / Predict next timestamp's value
            next_ts = event.timestamp + int(tick_interval * 1000)
            result = predictor.GCE_predict(features)
            if result is not None:
                pred_value, conf = result
                GCE_insert_prediction(
                    db_path,
                    agent_id,
                    next_ts,
                    pred_value,
                    conf,
                )

            time.sleep(tick_interval)
            energy = GCE__refresh_energy(db_path, agent_id)
        except Exception:
            logger.exception("Agent %s error in GCE_main loop", agent_id)
            time.sleep(tick_interval)
            energy = GCE__refresh_energy(db_path, agent_id)

    logger.info("Agent %s exiting (energy=%.2f)", agent_id, energy)


_shutdown_requested = False


def GCE__handle_shutdown() -> None:
    """处理关闭信号，设置关闭标志 / Handle shutdown signal by setting the shutdown flag."""
    global _shutdown_requested
    _shutdown_requested = True


def GCE__refresh_energy(db_path: str, agent_id: str) -> float:
    """从数据库获取当前能量值，含错误处理 / Fetch current energy from database, with error handling."""
    try:
        return GCE_get_agent_energy(db_path, agent_id)
    except Exception:
        return -1.0  # 数据库错误时强制退出 / Force exit on DB error
