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

"""
离线模拟器 —— Lorenz 混沌系统 + 多主体竞价市场。
此模块包含领域规则（Lorenz 方程、竞价算法），仅为环境实现。
这些方程是环境的"物理定律"，不向进化层暴露。

/ Offline simulator — Lorenz chaotic system + multi-agent auction market.
This module contains domain rules (Lorenz equations, auction algorithm) and
is purely an environment implementation. These equations are the "physics" of
the environment and are not exposed to the evolution layer.
"""

from __future__ import annotations

import logging
import math
import random
import time
from typing import Any, Dict, List, Tuple

from gce.environment.GCE_base import GCE_BaseEnvironment, GCE_EventType, GCE_RawEvent

logger = logging.getLogger("gce.environment.GCE_simulator")


def GCE__lorenz_deriv(state: Tuple[float, float, float], sigma: float, rho: float, beta: float) -> Tuple[float, float, float]:
    """Lorenz 系统导数计算 / Lorenz system derivatives."""
    x, y, z = state
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return dx, dy, dz


def GCE__rk4_step(
    state: Tuple[float, float, float],
    dt: float,
    sigma: float,
    rho: float,
    beta: float,
) -> Tuple[float, float, float]:
    """单步 RK4 积分 / Single RK4 integration step."""
    x, y, z = state
    k1x, k1y, k1z = GCE__lorenz_deriv(state, sigma, rho, beta)
    k2x, k2y, k2z = GCE__lorenz_deriv((x + 0.5 * dt * k1x, y + 0.5 * dt * k1y, z + 0.5 * dt * k1z), sigma, rho, beta)
    k3x, k3y, k3z = GCE__lorenz_deriv((x + 0.5 * dt * k2x, y + 0.5 * dt * k2y, z + 0.5 * dt * k2z), sigma, rho, beta)
    k4x, k4y, k4z = GCE__lorenz_deriv((x + dt * k3x, y + dt * k3y, z + dt * k3z), sigma, rho, beta)
    nx = x + (dt / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x)
    ny = y + (dt / 6.0) * (k1y + 2 * k2y + 2 * k3y + k4y)
    nz = z + (dt / 6.0) * (k1z + 2 * k2z + 2 * k3z + k4z)
    return nx, ny, nz


class GCE_MarketAgent:
    """固定策略的市场参与者，用于竞价层 / Fixed-strategy market participant for the auction layer."""

    def __init__(self, agent_id: int, base_price: float, rng: random.Random) -> None:
        self.id = agent_id
        self.strategy_type = rng.choice(["trend", "mean_revert", "random"])
        self.base_price = base_price
        self.memory: List[float] = []
        self.sensitivity = rng.uniform(0.01, 0.2)
        self.noise_level = rng.uniform(0.001, 0.05)
        self._rng = rng

    def GCE_decide(self, price_history: List[float], lorenz_x: float) -> Tuple[float, float]:
        """根据策略返回 (买入价, 卖出价) / Return (bid_price, ask_price) based on strategy.

        bid = 愿意以此价格买入 / willing to buy at this price
        ask = 愿意以此价格卖出 / willing to sell at this price
        """
        ref_price = price_history[-1] if price_history else self.base_price

        if self.strategy_type == "trend":
            if len(price_history) >= 2:
                trend = price_history[-1] - price_history[-2]
            else:
                trend = 0.0
            offset = trend * self.sensitivity
        elif self.strategy_type == "mean_revert":
            if len(price_history) >= 5:
                sma = sum(price_history[-5:]) / 5
                offset = (sma - ref_price) * self.sensitivity
            else:
                offset = 0.0
        else:  # random
            offset = self._rng.gauss(0.0, self.noise_level)

        # Lorenz 分量向定价中注入混沌 / Lorenz component injects chaos into pricing
        offset += lorenz_x * self.noise_level * 0.1

        bid = ref_price + offset - self.noise_level
        ask = ref_price + offset + self.noise_level

        # 确保 bid < ask / Ensure bid < ask
        if bid >= ask:
            bid = ask - abs(self.noise_level * 2)

        return bid, ask


class GCE_OfflineSimulator(GCE_BaseEnvironment):
    """环境模拟器：Lorenz 吸引子 + 多主体竞价市场 / Environment simulator: Lorenz attractor + multi-agent auction market."""

    def __init__(self, config: Dict[str, Any]) -> None:
        sim_cfg = config.get("environment", {}).get("simulator", {})
        lorenz = sim_cfg.get("lorenz", {})
        self.sigma = lorenz.get("sigma", 10.0)
        self.rho = lorenz.get("rho", 28.0)
        self.beta = lorenz.get("beta", 2.6666667)
        self.num_market_agents = sim_cfg.get("num_market_agents", 10)
        self.tick_interval = sim_cfg.get("tick_interval", 0.5)
        self.dt = sim_cfg.get("lorenz_dt", 0.01)
        self.substeps_per_tick = sim_cfg.get("substeps_per_tick", 50)

        self._stop_flag = False
        self._rng = random.Random(config.get("environment", {}).get("seed"))

        # 新闻模板（无语义含义，仅噪声模式） / News templates (no semantic meaning, just noise patterns)
        self._news_templates = [
            "BREAKING: Major shift detected in sector {sector}",
            "RUMOR: Unverified reports of {event} at {location}",
            "ALERT: {entity} announces unexpected {action}",
            "UPDATE: {metric} shows {direction} movement of {magnitude}%",
            "ANALYST: Technical patterns suggest {outcome} scenario",
            "REPORT: {entity} quarterly {metric} {direction} by {magnitude}%",
        ]
        self._sectors = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self._events = ["merger", "acquisition", "restructuring", "expansion", "contraction"]
        self._locations = ["Region-X", "Zone-Y", "Sector-Z", "Area-W"]
        self._entities = ["Entity-1", "Entity-2", "Entity-3", "Entity-4", "Entity-5"]
        self._actions = ["policy change", "strategic pivot", "capital reallocation"]
        self._metrics = ["efficiency", "output", "volatility", "liquidity", "sentiment"]
        self._directions = ["upward", "downward", "lateral"]
        self._outcomes = ["bullish", "bearish", "neutral", "volatile"]

    def GCE_start(self, event_queue) -> None:  # type: ignore[no-untyped-def]
        logger.info("GCE_OfflineSimulator starting (sigma=%.1f, rho=%.1f, agents=%d)",
                     self.sigma, self.rho, self.num_market_agents)

        # 用小随机扰动初始化 Lorenz 状态 / Initialize Lorenz state with small random perturbation
        state: Tuple[float, float, float] = (
            self._rng.uniform(-1.0, 1.0),
            self._rng.uniform(-1.0, 1.0),
            self._rng.uniform(15.0, 25.0),
        )

        # 初始化市场参与者 / Initialize market agents
        base_price = self._rng.uniform(90.0, 110.0)
        agents = [
            GCE_MarketAgent(i, base_price, self._rng)
            for i in range(self.num_market_agents)
        ]

        price_history: List[float] = [base_price]
        start_time = int(time.time() * 1000)
        tick_count = 0
        current_ts = start_time

        while not self._stop_flag:
            # 对每个 tick 进行 Lorenz 子步积分 / Integrate Lorenz for substeps_per_tick
            for _ in range(self.substeps_per_tick):
                state = GCE__rk4_step(state, self.dt, self.sigma, self.rho, self.beta)

            lx, ly, lz = state

            # 市场竞价 / Market auction
            bids = []
            asks = []
            for agent in agents:
                bid, ask = agent.GCE_decide(price_history, lx)
                bids.append(bid)
                asks.append(ask)

            # 撮合：找到排序后的买入和卖出交集 / Match: find intersection of sorted bids and asks
            bids.sort(reverse=True)
            asks.sort()
            # 简单清算：价格为最优买卖报价的加权中点 / Simple clearing: price is weighted midpoint of best bid/ask
            best_bid = bids[0]
            best_ask = asks[0]
            if best_bid >= best_ask:
                clearing_price = (best_bid + best_ask) / 2
            else:
                clearing_price = best_ask

            # 从 Lorenz Z 分量添加噪声 / Add noise from Lorenz Z component
            clearing_price += lz * 0.01

            volume = sum(1 for b, a in zip(bids, asks) if b >= a)
            spread = best_ask - best_bid

            price_history.append(clearing_price)
            if len(price_history) > 1000:
                price_history = price_history[-500:]

            # 发出价格事件 / Emit price event
            current_ts = start_time + int(tick_count * self.tick_interval * 1000)
            event = GCE_RawEvent(
                source_id="price",
                event_type=GCE_EventType.NUMERIC,
                timestamp=current_ts,
                value=clearing_price,
                metadata={
                    "volume": str(volume),
                    "spread": str(round(spread, 6)),
                    "lorenz_x": str(round(lx, 6)),
                },
            )
            try:
                event_queue.put(event, timeout=1.0)
            except Exception:
                logger.warning("Event queue full, dropping event at tick %d", tick_count)

            # 偶尔发出文本事件（每个 tick 有 10% 的概率） / Occasionally emit a text event (10% chance per tick)
            if self._rng.random() < 0.1:
                text_event = GCE_RawEvent(
                    source_id="news",
                    event_type=GCE_EventType.TEXT,
                    timestamp=current_ts,
                    text=self.GCE__generate_news(),
                )
                try:
                    event_queue.put(text_event, timeout=0.5)
                except Exception:
                    pass

            tick_count += 1
            time.sleep(self.tick_interval)

        logger.info("GCE_OfflineSimulator stopped after %d ticks", tick_count)

    def GCE_stop(self) -> None:
        self._stop_flag = True

    def GCE__generate_news(self) -> str:
        template = self._rng.choice(self._news_templates)
        return template.format(
            sector=self._rng.choice(self._sectors),
            event=self._rng.choice(self._events),
            location=self._rng.choice(self._locations),
            entity=self._rng.choice(self._entities),
            action=self._rng.choice(self._actions),
            metric=self._rng.choice(self._metrics),
            direction=self._rng.choice(self._directions),
            magnitude=round(self._rng.uniform(0.1, 9.9), 1),
            outcome=self._rng.choice(self._outcomes),
        )
