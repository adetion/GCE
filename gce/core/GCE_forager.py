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

"""觅食器 —— 事件滑动窗口 + 特征提取 + 掩码选择 / Forager -- event sliding window + feature extraction + mask selection."""

from __future__ import annotations

import math
from collections import deque
from typing import List, Optional

from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent

# 特征池定义（共36个特征） / Feature pool definition (36 features total)
# 索引 0-19:  price_lag1 至 price_lag20 / Indices 0-19:  price_lag1 through price_lag20
# 索引 20-24: volume_lag1 至 volume_lag5 / Indices 20-24: volume_lag1 through volume_lag5
# 索引 25-29: spread_lag1 至 spread_lag5 / Indices 25-29: spread_lag1 through spread_lag5
# 索引 30: price_sma5 / Index 30: price_sma5
# 索引 31: price_sma10 / Index 31: price_sma10
# 索引 32: price_sma20 / Index 32: price_sma20
# 索引 33: price_volatility5 / Index 33: price_volatility5
# 索引 34: volume_volatility5 / Index 34: volume_volatility5
# 索引 35: sentiment_score / Index 35: sentiment_score

FEATURE_COUNT = 36


class GCE_Forager:
    """维护最近事件的滑动窗口并提取特征向量 / Maintains a sliding window of recent events and extracts feature vectors.

    特征选择由博弈元的基因掩码控制（每个特征对应一个位） /
    Feature selection is controlled by the agent's gene mask (bit per feature).
    """

    def __init__(self, mask: int, window_size: int = 20) -> None:
        self.mask = mask
        self.window_size = window_size
        self._window: deque[GCE_RawEvent] = deque(maxlen=window_size)

    def GCE_update(self, event: GCE_RawEvent) -> None:
        """向滑动窗口添加一个事件 / Add an event to the sliding window."""
        self._window.append(event)

    def GCE_extract(self) -> Optional[List[float]]:
        """从当前窗口提取特征向量 / Extract feature vector from the current window.

        如果窗口尚未填满则返回 None。仅返回掩码位已设置的特征 /
        Returns None if the window is not yet full.
        Returns only the features whose mask bits are set.
        """
        if len(self._window) < self.window_size:
            return None

        # 计算所有原始特征 / Compute all raw features
        raw = self.GCE__compute_all_features()

        # 应用掩码：若第 i 位被置位，则包含特征 i / Apply mask: if bit i is set, include feature i
        result = []
        for i in range(FEATURE_COUNT):
            if (self.mask >> i) & 1:
                result.append(raw[i])

        # 若掩码为 0，未选择任何特征 —— 返回小的常量列表 / If mask is 0, no features are selected — return small constant list
        if not result:
            result = [0.0]

        return result

    def GCE__compute_all_features(self) -> List[float]:
        """从滑动窗口计算全部 36 个特征 / Compute all 36 features from the sliding window."""
        feats: List[float] = [0.0] * FEATURE_COUNT

        # 提取数值系列 / Extract numeric values
        prices = self.GCE__extract_series("price")
        volumes = self.GCE__extract_series("volume")
        spreads = self.GCE__extract_series("spread")

        # 价格滞后特征 (0-19) / Price lags (0-19)
        for i in range(min(20, len(prices))):
            feats[i] = prices[-1 - i] if i < len(prices) else 0.0

        # 成交量滞后特征 (20-24) / Volume lags (20-24)
        for i in range(min(5, len(volumes))):
            feats[20 + i] = volumes[-1 - i] if i < len(volumes) else 0.0

        # 价差滞后特征 (25-29) / Spread lags (25-29)
        for i in range(min(5, len(spreads))):
            feats[25 + i] = spreads[-1 - i] if i < len(spreads) else 0.0

        # 简单移动平均特征 (30-32) / SMA features (30-32)
        feats[30] = GCE__simple_moving_average(prices, 5)
        feats[31] = GCE__simple_moving_average(prices, 10)
        feats[32] = GCE__simple_moving_average(prices, 20)

        # 价格波动率 (33) / Price volatility (33)
        feats[33] = GCE__volatility(prices, 5)

        # 成交量波动率 (34) / Volume volatility (34)
        feats[34] = GCE__volatility(volumes, 5)

        # 情绪评分 (35)：从文本事件中粗略估算 / Sentiment score (35): crude proxy from text events
        feats[35] = self.GCE__extract_sentiment()

        return feats

    def GCE__extract_series(self, source_prefix: str) -> List[float]:
        """从匹配 source_id 前缀的事件中提取数值 / Extract numeric values from events matching a source_id prefix.

        环境可以使用 source_id（如 'price'、'volume'、'spread'）标记事件 /
        The environment can tag events with source_id like 'price', 'volume', 'spread'.
        """
        values = []
        for event in self._window:
            if event.event_type == GCE_EventType.NUMERIC and event.value is not None:
                # 在模拟器中，所有数值事件都代表价格。如果元数据中存在成交量/价差，则从中提取；
                # 否则为简单起见，全部视为 'price' /
                # In the simulator, all numeric events represent the price.
                # We derive volume/spread from metadata if present,
                # or treat them all as 'price' for simplicity.
                if source_prefix == "price":
                    values.append(event.value)
                elif source_prefix == "volume":
                    vol = event.metadata.get("volume")
                    if vol is not None:
                        values.append(float(vol))
                elif source_prefix == "spread":
                    spread = event.metadata.get("spread")
                    if spread is not None:
                        values.append(float(spread))
        return values

    def GCE__extract_sentiment(self) -> float:
        """从文本事件中粗略估算情绪指标 / Crude sentiment proxy from text events."""
        text_events = [e for e in self._window if e.event_type == GCE_EventType.TEXT and e.text]
        if not text_events:
            return 0.0
        # 简单启发式：将大写与小写字母的比例作为噪声信号 / Simple heuristic: count uppercase vs lowercase ratio as a noisy signal
        total = sum(1 for e in text_events for c in (e.text or "") if c.isalpha())
        if total == 0:
            return 0.0
        upper = sum(1 for e in text_events for c in (e.text or "") if c.isupper())
        return (upper / total - 0.5) * 2.0  # 缩放到大约 [-1, 1] / Scale to roughly [-1, 1]


def GCE__simple_moving_average(series: List[float], window: int) -> float:
    """计算简单移动平均 / Compute simple moving average."""
    if not series or window <= 0:
        return 0.0
    actual = min(window, len(series))
    return sum(series[-actual:]) / actual


def GCE__volatility(series: List[float], window: int) -> float:
    """计算波动率（标准差） / Compute volatility (standard deviation)."""
    if len(series) < 2:
        return 0.0
    actual = min(window, len(series))
    subset = series[-actual:]
    mean = sum(subset) / actual
    variance = sum((x - mean) ** 2 for x in subset) / actual
    return math.sqrt(variance)
