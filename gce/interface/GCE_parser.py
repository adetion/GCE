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

from gce.environment.GCE_sentiment import GCE_analyze_sentiment
from gce.interface.GCE_domain_templates import GCE_classify_domain
from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.simulation.GCE_schemas import GCE_Participant, GCE_Scenario

logger = logging.getLogger("gce.interface.GCE_parser")

# 博弈类型检测关键词 / Game-type detection keywords
_GAME_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "price_war": ["价格竞争", "价格战", "价格博弈", "定价博弈", "价格", "定价", "降价"],
    "auction": ["拍卖", "竞拍", "竞标", "频谱", "出价", "报价", "竞拍博弈"],
    "negotiation": ["谈判", "协商", "定价谈判", "医保谈判"],
    "output_competition": ["产量博弈", "产量竞争", "产能", "供给"],
}


def _detect_game_type_from_input(user_input: str) -> str:
    """从完整输入文本检测博弈类型 / Detect game type from full input text."""
    scores: Dict[str, int] = {}
    for game_type, keywords in _GAME_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in user_input)
        if score > 0:
            scores[game_type] = score
    if not scores:
        return "price_war"
    return max(scores, key=lambda k: scores[k])

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
    # 领域分类 / Domain classification
    domain_template = GCE_classify_domain(user_input, llm_client if not offline_mode else None)

    if not offline_mode and llm_client.enabled:
        return GCE__parse_online(user_input, llm_client, domain_template)
    else:
        return GCE__parse_offline(user_input, domain_template)


def GCE__parse_online(
    user_input: str,
    llm_client: GCE_LLMClient,
    domain_template: Any = None,
) -> Optional[GCE_Scenario]:
    """使用LLM解析场景描述 / Use LLM to parse the scene description."""
    # 注入领域上下文到 system prompt / Inject domain context into system prompt
    system_prompt = _SYSTEM_PROMPT
    if domain_template is not None and domain_template.domain_id:
        additions = domain_template.parsing_prompt_additions
        if additions:
            system_prompt = _SYSTEM_PROMPT + "\n\n## 领域上下文 / Domain Context\n" + additions

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    response = llm_client.GCE_generate(messages)
    if response is None:
        logger.warning("LLM parsing failed, falling back to offline")
        return GCE__parse_offline(user_input, domain_template)

    # 从回复中提取JSON（可能被markdown包裹） / Extract JSON from response (may be wrapped in markdown)
    json_match = re.search(r"\{[\s\S]*\}", response)
    if not json_match:
        logger.warning("No JSON found in LLM response: %s", response[:100])
        return GCE__parse_offline(user_input, domain_template)

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        logger.warning("JSON parse error: %s", e)
        return GCE__parse_offline(user_input, domain_template)

    scenario = GCE__build_scenario(data, user_input, domain_template)
    if scenario is None:
        return None

    # 在线模式下运行舆情分析 / Run sentiment analysis in online mode
    entity_names = [p.name for p in scenario.participants]
    scenario.sentiment_context = GCE_analyze_sentiment(
        user_input, entity_names, llm_client,
        domain_id=scenario.domain_id,
    )

    return scenario


def GCE__parse_offline(
    user_input: str,
    domain_template: Any = None,
) -> Optional[GCE_Scenario]:
    """离线启发式解析器，使用正则表达式 / Offline heuristic parser using regex.

    针对中文输入优化：从语境中提取参与方名称、价格数字和时间步。
    Optimized for Chinese input: extract participant names, prices, and time steps from context.
    """
    # ── 提取参与方名称 / Extract participant names ──
    # 策略：从"X和Y"、"X、Y和Z"等中文列表结构中提取 / Strategy: extract from Chinese list patterns
    participants: List[GCE_Participant] = []
    seen_names: set = set()

    # 模式1: "X和Y在...展开" — X和Y是主体 / Pattern 1: "X和Y在..."
    subject_match = re.search(r"(.+?)(?:在|参与|进行|展开)", user_input)
    if subject_match:
        subject_part = subject_match.group(1)
        # 从主体部分拆分出各参与方 / Split subject part into individual participants
        # 分割符：和、与、、(顿号)、以及
        name_candidates = re.split(r"[和与、]|以及", subject_part)
        for nc in name_candidates:
            nc = nc.strip()
            # 过滤太短、太长或包含非名称特征词的片段
            if 2 <= len(nc) <= 12 and nc not in seen_names:
                # 排除明显的非名称短语 / Exclude obvious non-name phrases
                if not re.search(r"(市场|进行|展开|为期|初始|当前|目标|在|的)", nc):
                    seen_names.add(nc)
                    participants.append(GCE_Participant(name=nc, initial_position=0.0))

    # 模式2: 如果没找到，尝试匹配大写字母缩写 / Fallback: try uppercase acronyms
    if not participants:
        caps = re.findall(r"([A-Z]{2,8})", user_input)
        for c in caps:
            if c not in seen_names and len(participants) < 5:
                seen_names.add(c)
                participants.append(GCE_Participant(name=c, initial_position=0.0))

    if not participants:
        participants = [GCE_Participant(name="Entity-A"), GCE_Participant(name="Entity-B")]

    # ── 提取价格数字 / Extract price numbers ──
    # 优先匹配带单位的数字（元/美元/万元/亿元/每...）——这些更可能是价格
    # Prefer numbers with currency units — more likely to be prices
    price_candidates = re.findall(
        r"(\d+\.?\d*)\s*(?:元|美元|万元|亿元|港元|欧元|日元|每|美金|人民币)",
        user_input,
    )
    if price_candidates:
        prices = [float(p) for p in price_candidates[:10]]
    else:
        # 无单位时提取所有数字，但过滤日期相关 / No units: extract all numbers, filter date-related
        all_numbers = re.findall(r"(\d+\.?\d*)", user_input)
        # 排除明显的日期/时间数字（后跟"天""日""周""月""年"）/ Exclude numbers before time units
        time_numbers = set(re.findall(r"(\d+\.?\d*)\s*[天日周月年步]", user_input))
        prices = []
        for n in all_numbers:
            if n not in time_numbers:
                prices.append(float(n))
        if not prices:
            prices = [float(n) for n in all_numbers[:5]] if all_numbers else [100.0, 100.5, 101.0, 100.8, 101.2]

    # 限制价格数量 / Cap price count
    prices = prices[:10]

    # ── 提取时间步 / Extract time steps ──
    time_match = re.search(r"(\d+)\s*[天步日周月]", user_input)
    time_steps = int(time_match.group(1)) if time_match else 30
    time_steps = max(5, min(60, time_steps))

    # ── 提取目标 / Extract objective ──
    # 以第一个句号或"目标是"为标志 / Use first period or "目标是" as delimiter
    objective_match = re.search(r"目标[是为](.+?)(?:[。，]|$)", user_input)
    if objective_match:
        objective = objective_match.group(1).strip()[:100]
    else:
        objective = user_input.split("。")[0].strip()[:100]

    # 确定博弈类型：领域模板优先 / Determine game type: template preference first
    game_type = ""
    domain_id = ""
    if domain_template is not None and domain_template.domain_id:
        domain_id = domain_template.domain_id
        game_type = domain_template.game_type_preference or _detect_game_type_from_input(user_input)
    else:
        game_type = _detect_game_type_from_input(user_input)

    scenario = GCE_Scenario(
        participants=participants,
        initial_prices=prices,
        time_steps=time_steps,
        objective=objective,
        raw_input=user_input,
        game_type=game_type,
        domain_id=domain_id,
    )

    if not GCE__validate_scenario(scenario):
        return None

    return scenario


def GCE__build_scenario(
    data: Dict[str, Any],
    raw_input: str = "",
    domain_template: Any = None,
) -> Optional[GCE_Scenario]:
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

        # 确定博弈类型和领域 / Determine game type and domain
        game_type = ""
        domain_id = ""
        if domain_template is not None and domain_template.domain_id:
            domain_id = domain_template.domain_id
            game_type = domain_template.game_type_preference or _detect_game_type_from_input(raw_input or objective)
        else:
            game_type = _detect_game_type_from_input(raw_input or objective)

        scenario = GCE_Scenario(
            participants=participants,
            initial_prices=initial_prices,
            time_steps=time_steps,
            objective=objective,
            raw_input=raw_input or objective,
            game_type=game_type,
            domain_id=domain_id,
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
