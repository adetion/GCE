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

"""场景解析器 —— 在线 (LLM) / 离线 (regex) 双模式 / Scene parser — online (LLM) / offline (regex) dual mode."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.simulation.GCE_schemas import GCE_Participant, GCE_Scenario

logger = logging.getLogger("gce.interface.GCE_parser")

_SYSTEM_PROMPT = """你是一个场景解析器。根据用户描述，提取以下结构化信息，以严格JSON格式返回：
{
  "participants": [{"name": "参与方名称", "initial_position": 0.0, "strategy_hint": "策略提示"}],
  "initial_prices": [100.0, 101.0, ...],
  "time_steps": 30,
  "objective": "用户目标"
}
规则：
- participants: 列出所有参与方，initial_position 用数字表示初始状态（如价格点位、市场份额等）
- initial_prices: 长度为2-20的数值数组，表示初始观察序列
- time_steps: 预测未来多少步，范围5-60
- objective: 用一句话概括用户的问题
仅返回JSON，不要有其他文字。"""


def GCE_parse_scene(
    user_input: str,
    llm_client: GCE_LLMClient,
    offline_mode: bool = False,
) -> Optional[GCE_Scenario]:
    """将用户输入解析为GCE_Scenario / Parse user input into a GCE_Scenario.

    在线模式下使用LLM提取结构化数据，离线模式下使用基于正则的启发式提取 /
    In online mode, uses LLM to GCE_extract structured data.
    In offline mode, uses regex-based heuristic extraction.
    """
    if not offline_mode and llm_client.enabled:
        return GCE__parse_online(user_input, llm_client)
    else:
        return GCE__parse_offline(user_input)


def GCE__parse_online(user_input: str, llm_client: GCE_LLMClient) -> Optional[GCE_Scenario]:
    """使用LLM解析场景描述 / Use LLM to parse the scene description."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    response = llm_client.GCE_generate(messages)
    if response is None:
        logger.warning("LLM parsing failed, falling back to offline")
        return GCE__parse_offline(user_input)

    # 从回复中提取JSON（可能被markdown包裹） / Extract JSON from response (may be wrapped in markdown)
    json_match = re.search(r"\{[\s\S]*\}", response)
    if not json_match:
        logger.warning("No JSON found in LLM response: %s", response[:100])
        return GCE__parse_offline(user_input)

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        logger.warning("JSON parse error: %s", e)
        return GCE__parse_offline(user_input)

    return GCE__build_scenario(data)


def GCE__parse_offline(user_input: str) -> Optional[GCE_Scenario]:
    """离线启发式解析器，使用正则表达式 / Offline heuristic parser using regex."""
    # 提取数字作为初始价格 / Extract numbers as initial_prices
    numbers = re.findall(r"(\d+\.?\d*)", user_input)
    prices = [float(n) for n in numbers[:20]]
    if not prices:
        # 默认初始价格 / Default initial prices
        prices = [100.0, 100.5, 101.0, 100.8, 101.2]

    # 提取可能的参与方名称（大写短语）/ Extract potential participant names (Capitalized phrases)
    names = re.findall(r"([A-Z一-鿿][A-Za-z一-鿿]{1,15})", user_input)
    participants = []
    seen = set()
    for name in names:
        if name not in seen and len(participants) < 5:
            seen.add(name)
            participants.append(GCE_Participant(name=name, initial_position=0.0))

    if not participants:
        participants = [GCE_Participant(name="Entity-A"), GCE_Participant(name="Entity-B")]

    # 提取时间提示（如"30天"、"10步"、"未来20"）/ Extract time hint (e.g. "30天", "10步", "未来20")
    time_match = re.search(r"(\d+)\s*[天步日周月]", user_input)
    time_steps = int(time_match.group(1)) if time_match else 30
    time_steps = max(5, min(60, time_steps))

    # 目标：使用第一句话或完整输入 / Objective: use first sentence or full input
    objective = user_input.split("。")[0].strip()[:100]

    scenario = GCE_Scenario(
        participants=participants,
        initial_prices=prices,
        time_steps=time_steps,
        objective=objective,
    )

    if not GCE__validate_scenario(scenario):
        return None

    return scenario


def GCE__build_scenario(data: Dict[str, Any]) -> Optional[GCE_Scenario]:
    """从解析后的数据字典构建GCE_Scenario / Build a GCE_Scenario from parsed data dict."""
    try:
        participants = [
            GCE_Participant(
                name=p.get("name", f"Entity-{i}"),
                initial_position=float(p.get("initial_position", 0.0)),
                strategy_hint=p.get("strategy_hint", ""),
            )
            for i, p in enumerate(data.get("participants", []))
        ]
        if not participants:
            participants = [GCE_Participant(name="Entity-A"), GCE_Participant(name="Entity-B")]

        initial_prices = [float(v) for v in data.get("initial_prices", [100.0])]
        time_steps = int(data.get("time_steps", 30))
        time_steps = max(5, min(60, time_steps))
        objective = str(data.get("objective", ""))

        scenario = GCE_Scenario(
            participants=participants,
            initial_prices=initial_prices,
            time_steps=time_steps,
            objective=objective,
        )

        if not GCE__validate_scenario(scenario):
            return None

        return scenario
    except (ValueError, TypeError, KeyError) as e:
        logger.warning("Failed to build scenario from parsed data: %s", e)
        return None


def GCE__validate_scenario(scenario: GCE_Scenario) -> bool:
    """验证场景约束条件 / Validate scenario constraints."""
    if not scenario.initial_prices:
        logger.warning("GCE_Scenario has no initial prices")
        return False
    if scenario.time_steps < 1 or scenario.time_steps > 100:
        logger.warning("GCE_Scenario time_steps out of range: %d", scenario.time_steps)
        return False
    if not scenario.participants:
        logger.warning("GCE_Scenario has no participants")
        return False
    return True
