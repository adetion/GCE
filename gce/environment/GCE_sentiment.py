#
# -*- coding: utf-8 -*-
#
# Gaming Chaos Engine V0.1.0 – A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# ... (license header identical to all other project files) ...

"""舆情分析模块 — LLM 驱动的全球舆情与市场情绪分析 / Sentiment analysis — LLM-driven global sentiment analysis.

利用 DeepSeek LLM 基于其训练知识分析场景涉及实体/行业的当前舆情背景。
将舆情量化后注入博弈模型，调制策略扰动幅度。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gce.environment.sentiment")

_SENTIMENT_SYSTEM_PROMPT = """你是一位全球舆情与金融市场情绪分析专家。基于你的知识库，分析以下场景所涉及实体、行业和博弈类型的当前舆情背景。

## 分析要求
1. 基于你对相关实体/行业的了解，判断当前全球舆论和市场情绪的方向和强度
2. 识别影响该博弈格局的关键舆情主题（政策变动、技术突破、竞争格局变化、宏观经济因素等）
3. 评估市场整体的风险偏好和波动预期
4. 为每个参与实体给出个体情绪分数

## 输出格式
严格返回以下JSON，不要有其他文字：
{
  "overall_sentiment": "positive" | "neutral" | "negative",
  "sentiment_score": -1.0到1.0之间的浮点数（-1=极度悲观, 0=中性, 1=极度乐观）,
  "key_themes": ["主题1", "主题2", "主题3"],
  "market_mood": "risk-on" | "risk-off" | "cautious",
  "volatility_expectation": "low" | "moderate" | "high",
  "entity_sentiments": {"实体名": 情绪分数, ...},
  "summary": "一句话总结当前舆情态势及其对博弈格局的影响"
}

## 注意事项
- 如果你对某个实体没有足够了解，给出中性分数（0.0）
- 情绪分数不应极端（绝对值不超过0.8），除非有明确的极端事件
- key_themes 应具体而非泛泛（如"AI监管收紧"而非"政策"）"""


def GCE_analyze_sentiment(
    scenario_text: str,
    entity_names: List[str],
    llm_client: Any,  # GCE_LLMClient
    domain_id: str = "",
) -> Dict[str, Any]:
    """使用 LLM 分析当前舆情 / Analyze current sentiment using LLM.

    Args:
        scenario_text: 用户输入的完整场景描述
        entity_names: 场景涉及的所有实体名称列表
        llm_client: LLM 客户端（可为 None，此时返回中性舆情）
        domain_id: 可选的领域模板 ID，用于注入领域特定的舆情分析角度

    Returns:
        sentiment_context 字典，包含整体情绪、分数、主题、风险偏好等
    """
    if llm_client is None or not getattr(llm_client, 'enabled', False):
        return _neutral_sentiment(entity_names)

    # 获取领域舆情分析角度 / Get domain-specific sentiment analysis angle
    domain_addition = ""
    if domain_id:
        from gce.interface.GCE_domain_templates import GCE_get_template_by_id
        template = GCE_get_template_by_id(domain_id)
        if template and template.sentiment_prompt_additions:
            domain_addition = f"\n\n领域分析角度: {template.sentiment_prompt_additions}"

    user_message = f"""场景描述：{scenario_text}

涉及实体：{", ".join(entity_names) if entity_names else "未指定"}

请基于你的知识分析上述实体和行业在当前时间点（2026年5月）的舆情背景。{domain_addition}"""

    messages = [
        {"role": "system", "content": _SENTIMENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        response = llm_client.GCE_generate(messages)
        if response is None:
            logger.warning("LLM sentiment analysis returned None, using neutral")
            return _neutral_sentiment(entity_names)

        # 从回复中提取 JSON
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            logger.warning("No JSON found in sentiment response: %s", response[:100])
            return _neutral_sentiment(entity_names)

        data = json.loads(json_match.group())

        # 构建标准化输出
        sentiment_context = {
            "overall_sentiment": str(data.get("overall_sentiment", "neutral")),
            "sentiment_score": float(data.get("sentiment_score", 0.0)),
            "key_themes": list(data.get("key_themes", [])),
            "market_mood": str(data.get("market_mood", "cautious")),
            "volatility_expectation": str(data.get("volatility_expectation", "moderate")),
            "entity_sentiments": dict(data.get("entity_sentiments", {})),
            "summary": str(data.get("summary", "无舆情数据")),
            "source": "llm",
        }

        # 确保所有实体有情绪分数
        for name in entity_names:
            if name not in sentiment_context["entity_sentiments"]:
                sentiment_context["entity_sentiments"][name] = sentiment_context["sentiment_score"]

        # 裁剪极端值
        sentiment_context["sentiment_score"] = max(-0.8, min(0.8, sentiment_context["sentiment_score"]))
        for name in sentiment_context["entity_sentiments"]:
            sentiment_context["entity_sentiments"][name] = max(
                -0.8, min(0.8, sentiment_context["entity_sentiments"][name])
            )

        logger.info(
            "Sentiment analyzed: %s (score=%.2f, mood=%s, themes=%s)",
            sentiment_context["overall_sentiment"],
            sentiment_context["sentiment_score"],
            sentiment_context["market_mood"],
            sentiment_context["key_themes"],
        )
        return sentiment_context

    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        logger.warning("Failed to parse sentiment response: %s", e)
        return _neutral_sentiment(entity_names)
    except Exception as e:
        logger.warning("Sentiment analysis failed: %s", e)
        return _neutral_sentiment(entity_names)


def _neutral_sentiment(entity_names: List[str]) -> Dict[str, Any]:
    """返回中性舆情（无影响）/ Return neutral sentiment (no impact)."""
    return {
        "overall_sentiment": "neutral",
        "sentiment_score": 0.0,
        "key_themes": [],
        "market_mood": "cautious",
        "volatility_expectation": "moderate",
        "entity_sentiments": {name: 0.0 for name in entity_names} if entity_names else {},
        "summary": "无可用舆情数据，推演仅基于博弈模型内在动力学。",
        "source": "fallback",
    }


def GCE_compute_sentiment_bias(
    sentiment_context: Dict[str, Any],
    game_type: str,
    player_name: str,
) -> float:
    """根据舆情和博弈类型计算策略偏置 / Compute strategy bias from sentiment and game type.

    偏置值用于调制智能体扰动：combined_pert = agent_pert * (1.0 + bias)

    Args:
        sentiment_context: GCE_analyze_sentiment 的输出
        game_type: 博弈类型 (price_war, auction, negotiation, output_competition)
        player_name: 当前参与方名称

    Returns:
        偏置值，范围 [-0.5, 0.5]。正值 → 放大扰动，负值 → 缩小扰动
    """
    score = sentiment_context.get("sentiment_score", 0.0)
    entity_scores = sentiment_context.get("entity_sentiments", {})
    market_mood = sentiment_context.get("market_mood", "cautious")
    vol_expect = sentiment_context.get("volatility_expectation", "moderate")

    # 个体情绪偏置
    player_score = entity_scores.get(player_name, score)

    # 基础偏置 = 个体情绪 × 整体情绪的方向一致性
    base_bias = player_score * 0.3

    # 博弈类型调整
    if game_type == "price_war":
        # 负面情绪 → 恐慌降价（正偏置=放大扰动=加速降价）
        # 正面情绪 → 竞争缓和（负偏置=缩小扰动）
        base_bias *= -1.0
    elif game_type == "auction":
        # 正面情绪 → 出价激进（正偏置）
        # 负面情绪 → 出价保守（负偏置）
        pass  # 保持原方向
    elif game_type == "negotiation":
        # 正面情绪 → 卖方更坚持、买方更配合
        # 根据玩家身份调整——简化处理：卖方偏置反向
        pass  # 保持原方向
    elif game_type == "output_competition":
        # 正面情绪 → 扩产积极
        pass

    # 市场情绪放大器
    if market_mood == "risk-on":
        base_bias *= 1.3
    elif market_mood == "risk-off":
        base_bias *= 1.2  # 恐慌也放大影响
        base_bias = -abs(base_bias)  # 但方向向下

    # 波动预期放大器
    if vol_expect == "high":
        base_bias *= 1.25
    elif vol_expect == "low":
        base_bias *= 0.75

    # 截断
    return max(-0.5, min(0.5, base_bias))
