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

"""在线数据适配器 —— YFinance, CoinGecko 等数据源 / Online data adapters — YFinance, CoinGecko, and other data sources."""

from __future__ import annotations

import logging
from typing import Any, Dict

from gce.environment.GCE_base import GCE_BaseEnvironment

logger = logging.getLogger("gce.environment.GCE_adapters")


class GCE_YFinanceAdapter(GCE_BaseEnvironment):
    """Yahoo Finance 数据适配器，需要网络连接 / Adapter for Yahoo Finance data. Requires internet connectivity."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._stop_flag = False
        self.ticker = config.get("environment", {}).get("online_sources", {}).get("yfinance_ticker", "AAPL")
        self.interval = config.get("environment", {}).get("online_sources", {}).get("poll_interval", 2.0)

    def GCE_start(self, event_queue) -> None:  # type: ignore[no-untyped-def]
        try:
            import yfinance as yf  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("yfinance not installed. Cannot GCE_start GCE_YFinanceAdapter.")
            return

        logger.info("GCE_YFinanceAdapter starting for ticker: %s", self.ticker)
        while not self._stop_flag:
            try:
                ticker = yf.Ticker(self.ticker)
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
                    import time
                    ts = int(time.time() * 1000)
                    price = float(hist["Close"].iloc[-1])
                    event = GCE_RawEvent(
                        source_id="price",
                        event_type=GCE_EventType.NUMERIC,
                        timestamp=ts,
                        value=price,
                    )
                    try:
                        event_queue.put(event, timeout=1.0)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning("YFinance fetch failed: %s", e)
            # 等待下一个轮询间隔 / Wait for next poll interval
            import time as _time
            _time.sleep(self.interval)

    def GCE_stop(self) -> None:
        self._stop_flag = True


class GCE_CoinGeckoAdapter(GCE_BaseEnvironment):
    """CoinGecko API 适配器，需要网络连接 / Adapter for CoinGecko API. Requires internet connectivity."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._stop_flag = False
        self.coin_id = config.get("environment", {}).get("online_sources", {}).get("coingecko_coin", "bitcoin")
        self.interval = config.get("environment", {}).get("online_sources", {}).get("poll_interval", 5.0)

    def GCE_start(self, event_queue) -> None:  # type: ignore[no-untyped-def]
        logger.info("GCE_CoinGeckoAdapter starting for coin: %s", self.coin_id)
        import time as _time
        while not self._stop_flag:
            try:
                import urllib.request
                import json
                url = (
                    f"https://api.coingecko.com/api/v3/simple/price"
                    f"?ids={self.coin_id}&vs_currencies=usd"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "gce/0.1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                    price = float(data[self.coin_id]["usd"])

                from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
                ts = int(_time.time() * 1000)
                event = GCE_RawEvent(
                    source_id="price",
                    event_type=GCE_EventType.NUMERIC,
                    timestamp=ts,
                    value=price,
                )
                try:
                    event_queue.put(event, timeout=1.0)
                except Exception:
                    pass
            except Exception as e:
                logger.warning("CoinGecko fetch failed: %s", e)
            _time.sleep(self.interval)

    def GCE_stop(self) -> None:
        self._stop_flag = True


def GCE_create_environment(config: Dict[str, Any]) -> GCE_BaseEnvironment:
    """工厂函数：根据配置创建环境 / Factory: create environment based on configuration.

    优先尝试在线适配器；失败时回退到 GCE_OfflineSimulator /
    Tries online adapters first; falls back to GCE_OfflineSimulator on failure.
    """
    online_sources = config.get("environment", {}).get("online_sources", [])

    for source in online_sources:
        source_type = source.get("type", "") if isinstance(source, dict) else source
        try:
            if source_type == "yfinance":
                logger.info("Attempting YFinance adapter...")
                return GCE_YFinanceAdapter(config)
            elif source_type == "coingecko":
                logger.info("Attempting CoinGecko adapter...")
                return GCE_CoinGeckoAdapter(config)
        except Exception as e:
            logger.warning("Failed to load adapter '%s': %s", source_type, e)

    # 回退到离线模拟器 / Fallback to offline simulator
    logger.info("Falling back to GCE_OfflineSimulator")
    from gce.environment.GCE_simulator import GCE_OfflineSimulator
    return GCE_OfflineSimulator(config)
