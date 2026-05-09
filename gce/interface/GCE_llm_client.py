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

"""大模型客户端 —— DeepSeek API 封装 (OpenAI 兼容) / LLM client — DeepSeek API wrapper (OpenAI-compatible)."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gce.interface.llm")


class GCE_LLMClient:
    """OpenAI兼容的LLM客户端，用于场景解析与叙事生成 / OpenAI-compatible LLM client for scene parsing and narrative generation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化LLM客户端，从配置中读取参数 / Initialize LLM client from configuration."""
        llm_cfg = config.get("llm", {})
        self.enabled = llm_cfg.get("enabled", False)
        self.api_key = llm_cfg.get("api_key", "")
        self.base_url = llm_cfg.get("base_url", "https://api.deepseek.com/v1")
        self.model = llm_cfg.get("model", "deepseek-chat")
        self.temperature = llm_cfg.get("temperature", 0.7)
        self.max_tokens = llm_cfg.get("max_tokens", 2048)
        self.timeout = llm_cfg.get("timeout", 30.0)

        self._call_count = 0
        self._total_latency = 0.0

        if self.enabled and not self.api_key:
            logger.warning("LLM enabled but no API key provided. Disabling LLM.")
            self.enabled = False

    def GCE_generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """调用LLM接口生成回复，失败返回None / Call the LLM with a list of messages. Returns None on failure."""
        if not self.enabled:
            return None

        GCE_start = time.monotonic()
        try:
            import openai

            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            elapsed = time.monotonic() - GCE_start
            self._call_count += 1
            self._total_latency += elapsed
            logger.info("LLM call #%d: %.2fs (avg %.2fs)",
                        self._call_count, elapsed,
                        self._total_latency / self._call_count)

            content = resp.choices[0].message.content
            return content.strip() if content else None
        except ImportError:
            logger.warning("openai package not installed. LLM disabled.")
            self.enabled = False
            return None
        except Exception as e:
            elapsed = time.monotonic() - GCE_start
            logger.warning("LLM call failed (%.2fs): %s", elapsed, e)
            return None

    @property
    def GCE_stats(self) -> Dict[str, Any]:
        """返回LLM调用统计信息 / Return LLM call statistics."""
        return {
            "calls": self._call_count,
            "total_latency": self._total_latency,
            "avg_latency": self._total_latency / max(self._call_count, 1),
        }
