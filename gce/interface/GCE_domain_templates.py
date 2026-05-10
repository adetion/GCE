#
# -*- coding: utf-8 -*-
#
# Gaming Chaos Engine V0.1.0 - A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# ... (license header identical to all other project files) ...

"""领域模板系统 —— 为 N 维应用光谱提供定制化解析参考参数 / Domain template system — customized parsing reference for N-dimensional application spectrum.

每个领域模板描述该领域中"要找什么类型的东西"（实体类型、数值语义、博弈结构），
作为解析器的参考参数。模板绝不包含具体数值、实体名称或领域公式。

Every domain template describes WHAT KIND of thing to look for in that domain
(entity types, value semantics, game structure), serving as reference for the parser.
Templates NEVER contain concrete values, entity names, or domain-specific formulas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gce.interface.domain_templates")


@dataclass
class DomainTemplate:
    """领域模板 —— 解析参考参数，绝不包含硬编码数据 / Domain template — parsing reference, never hardcoded data."""

    domain_id: str
    display_name: str
    description: str

    # 匹配关键词 / Matching keywords
    keyword_triggers: List[str] = field(default_factory=list)

    # 实体提取指引（参考参数） / Entity extraction hints (reference only)
    entity_type_hints: str = ""

    # 数值语义（参考参数） / Value semantics (reference only)
    value_semantics: str = ""

    # 博弈类型偏好 / Game type preference
    game_type_preference: str = ""

    # 解析器提示词补充 / Parser prompt additions
    parsing_prompt_additions: str = ""

    # 舆情分析提示词补充 / Sentiment prompt additions
    sentiment_prompt_additions: str = ""

    # 叙事提示词补充 / Narrative prompt additions
    narrative_prompt_additions: str = ""

    # 规则回退术语替换表 / Rule-based fallback term overrides
    narrative_term_overrides: Dict[str, str] = field(default_factory=dict)

    # 大白话结论卡生成指引 / Plain-language conclusion card guidance
    plain_language_additions: str = ""

    # 优先级 / Priority
    priority: int = 0


# ── 通用哨兵模板 / Generic sentinel template ──────────────────────────────

_GENERIC_TEMPLATE = DomainTemplate(
    domain_id="",
    display_name="通用 (Generic)",
    description="默认模板——无领域特定指引，行为与 v0.1.0 完全一致",
    priority=-999,
)


# ── 领域模板注册表 / Domain template registry ─────────────────────────────

_DOMAIN_TEMPLATES: List[DomainTemplate] = [
    # ── 1. 个人存在与内在宇宙 / Micro-Individual ─────────────────────────
    DomainTemplate(
        domain_id="micro_individual",
        display_name="个人存在与内在宇宙 (Micro-Individual)",
        description="个人人生战略、日常决策、家庭财务、生物节律优化",
        keyword_triggers=[
            # 人生规划
            "人生规划", "职业发展", "职业路径", "人生选择", "人生战略",
            "无悔策略", "生涯规划", "个人成长", "自我提升",
            # 日常决策
            "日常决策", "时间管理", "精力分配", "习惯养成", "目标管理",
            "学习路径", "技能树", "知识体系",
            # 家庭财务
            "家庭财务", "家庭预算", "个人理财", "消费决策", "购物策略",
            "零花钱", "储蓄计划", "财务自由",
            # 健康与生物节律
            "生物节律", "生物钟", "睡眠优化", "饮食计划", "健身方案",
            "可穿戴设备", "昼夜节律", "褪黑素", "季节性情感障碍",
            # 心理与潜意识
            "潜意识", "梦境解析", "自我谈判", "心理调适", "焦虑",
            "内在冲突", "显意识",
            # 通用个人语境
            "个人选择", "自我管理", "独处时光", "个人效率",
            # 职业/事业发展
            "职业转型", "转行", "跳槽", "求职", "职业规划", "职业发展",
            "职场方向", "工作与生活", "副业", "自由职业", "创业",
            "深耕", "现有领域", "后端工程师", "产品经理", "岗位",
            "事业", "工作满意度",
        ],
        entity_type_hints=(
            "参与方是个人生活中的不同需求、角色、目标或时间分配维度，"
            "名称如'工作'、'健康'、'家庭'、'学习'、'社交'、'休闲'。"
            "也可能是不同人生阶段的自我（现在的我 vs 未来的我）或不同价值观之间的内在博弈。"
        ),
        value_semantics=(
            "数值代表时间分配比例、精力投入指数、优先级权重或满意度评分（0-100 或相对分数），"
            "不是货币价格。时间步通常代表天、周或月。"
        ),
        game_type_preference="negotiation",
        parsing_prompt_additions=(
            "领域上下文：这是一个个人决策场景。\n"
            "- 参与方是个人生活中的不同维度（工作、健康、家庭、学习等），不是公司或组织\n"
            "- initial_position 表示精力/时间分配比例（0-100），不是价格\n"
            "- initial_prices 应理解为时间序列上的精力分配数据\n"
            "- objective 概括个人面临的选择困境或优化目标"
        ),
        sentiment_prompt_additions=(
            "分析角度应为个人发展领域的最新趋势：时间管理方法论、远程工作趋势、"
            "心理健康意识上升、终身学习理念普及、数字健康工具的兴起。"
            "不要分析金融市场指标，而是分析影响个人决策的社会文化趋势。"
        ),
        narrative_prompt_additions=(
            "报告应使用个人发展术语（精力分配、习惯养成、边际收益、机会成本），"
            "而非金融术语。'四幕'可理解为'阶段一至四'。"
            "策略建议应聚焦于个人可执行的具体行动，而非组织层面的决策。"
        ),
        narrative_term_overrides={
            "博弈混沌": "人生混沌",
            "均衡价格": "最优分配点",
            "市场份额": "时间占比",
            "竞争对手": "替代选项",
            "价格竞争": "优先序竞争",
            "定价谈判": "取舍协商",
            "拍卖竞价": "优先序拍卖",
            "产量竞争": "投入产出竞争",
            "价格战": "顾此失彼",
            "降价抢量": "牺牲某个维度",
            "市场趋势": "生活趋势",
            "市场正在": "局面正在",
            "市场价格": "精力交换率",
            "价格": "精力投入",
            "降价": "减少投入",
            "利润": "满足感收益",
            "成本": "时间代价",
            "出价": "投入程度",
            "止损": "调整底线",
            "调价": "调整投入",
        },
        priority=0,
    ),

    # ── 2. 人际关系的量子纠缠 / Social Network ──────────────────────────
    DomainTemplate(
        domain_id="social_network",
        display_name="人际关系的量子纠缠 (Social Network)",
        description="求婚表白时机、家族遗产纠纷、邻里冲突、职场政治、社交破冰",
        keyword_triggers=[
            # 亲密关系
            "求婚", "表白", "分手", "复合", "恋爱", "约会", "婚姻",
            "情感共振", "亲密关系", "两性博弈",
            # 家族
            "家族遗产", "遗产分配", "继承", "亲属", "婆媳", "亲子",
            "家庭矛盾", "家庭会议", "亲戚", "血缘",
            # 邻里
            "邻里", "邻居", "噪音", "物业", "上下楼", "小区", "业主",
            "邻里纠纷", "社区矛盾",
            # 职场
            "同事关系", "职场政治", "办公室政治", "职场盟友", "权力结构",
            "职场竞争", "晋升博弈", "派系",
            # 社交
            "社交破冰", "陌生人社交", "社交场合", "搭讪", "社交策略",
            "聚会", "人脉", "社交网络",
            # 信任与合作
            "信任", "裂痕", "协作", "合作分歧", "和解", "破冰",
            "沟通", "误会", "冷战", "冰点", "修复关系",
            "团队协作", "合作伙伴", "搭档", "联盟",
            # 通用
            "人际关系", "人际博弈", "社交博弈", "关系维护", "人情",
        ],
        entity_type_hints=(
            "参与方是具体的人、家庭成员、派系或社交群体，名称通常为人名、亲属称谓或角色标签。"
            "在多边关系场景中，参与方可能包括第三方（共同朋友、调解人等）。"
        ),
        value_semantics=(
            "数值代表关系亲密度、情感评分、信任指数、妥协意愿或利益分配份额，"
            "不是货币价格。也可能代表时间轴上的关系温度或冲突强度。"
        ),
        game_type_preference="negotiation",
        parsing_prompt_additions=(
            "领域上下文：这是一个人际关系场景。\n"
            "- 参与方是具体的人或群体（如家庭成员、邻居、同事），不是公司\n"
            "- initial_position 表示关系亲密度、立场强度或利益诉求值\n"
            "- initial_prices 应理解为关系状态的历史数据序列\n"
            "- 注意提取情感相关的时间节点和关键事件"
        ),
        sentiment_prompt_additions=(
            "分析角度应为人际关系和社会心理领域的最新趋势：社交媒体对人际关系的影响、"
            "代际价值观差异、城市化对邻里关系的冲击、职场文化的变迁。"
            "分析社会情绪如何影响个体间博弈的策略选择。"
        ),
        narrative_prompt_additions=(
            "报告应使用人际关系和社会心理学术语（关系亲密度、信任指数、情感账户、"
            "社会资本），而非金融术语。"
            "策略建议应聚焦于沟通技巧、时机选择和关系修复方案。"
        ),
        narrative_term_overrides={
            "博弈混沌": "关系混沌",
            "均衡价格": "关系平衡点",
            "市场份额": "情感占比",
            "竞争对手": "其他关系方",
            "价格竞争": "关系竞争",
            "定价谈判": "调解协商",
            "拍卖竞价": "关系竞价",
            "产量竞争": "关系投入竞争",
            "价格战": "关系恶化螺旋",
            "降价抢量": "示弱退让",
            "对抗市场趋势": "对抗关系恶化趋势",
            "市场信号": "社交信号",
            "价格": "关系投入",
            "降价": "妥协让步",
            "利润": "关系收益",
            "成本": "情感成本",
            "出价": "主动示好",
            "止损": "设定底线",
            "调价": "调整姿态",
        },
        priority=0,
    ),

    # ── 3. 创意与娱乐的无限游戏 / Creative Entertainment ─────────────────
    DomainTemplate(
        domain_id="creative_entertainment",
        display_name="创意与娱乐的无限游戏 (Creative Entertainment)",
        description="生成式游戏引擎、虚拟偶像、互动叙事、音乐混音、内容生产",
        keyword_triggers=[
            # 游戏
            "游戏引擎", "游戏剧情", "NPC", "玩家社区", "游戏生态",
            "游戏设计", "超文本游戏", "沙盒游戏", "互动叙事",
            # 虚拟偶像
            "虚拟偶像", "虚拟主播", "Vtuber", "偶像养成", "粉丝经济",
            "数字人", "虚拟形象",
            # 内容创作
            "剧本", "小说", "互动小说", "叙事引擎", "故事生成",
            "情节走向", "读者评论", "共创", "UGC",
            # 音乐/影视
            "音乐混音", "生成音乐", "电影剧本", "影视制作",
            "创意生产", "内容平台", "文化产品",
            # 通用
            "创意博弈", "娱乐产业", "文化产业", "内容竞争", "IP",
            "版权", "流量", "注意力", "粉丝", "热度",
        ],
        entity_type_hints=(
            "参与方是创意实体：IP、角色、内容创作者、平台、粉丝群体。"
            "名称通常为作品名、角色名、创作者名或平台名。"
            "在互动叙事场景中，参与方可能是剧情中的不同角色或势力。"
        ),
        value_semantics=(
            "数值代表关注度/流量指数、创作投入度、角色人气值、剧情分歧权重，"
            "不是货币价格。在拍卖场景中可能代表注意力竞价或 IP 授权报价。"
        ),
        game_type_preference="auction",
        parsing_prompt_additions=(
            "领域上下文：这是一个创意/娱乐产业场景。\n"
            "- 参与方是创意实体（IP、角色、创作者、平台），不是传统企业\n"
            "- initial_position 表示人气值、关注度或创作资源投入量\n"
            "- initial_prices 应理解为创意指标的历史序列（热度、评分等）\n"
            "- 注意识别粉丝群体和社区作为隐性参与方"
        ),
        sentiment_prompt_additions=(
            "分析角度应为创意产业和数字内容领域的最新趋势：AI 生成内容的冲击、"
            "粉丝经济演变、注意力经济的竞争格局、跨媒体叙事趋势。"
            "分析社区情绪和粉丝文化的波动对创意决策的影响。"
        ),
        narrative_prompt_additions=(
            "报告应使用创意产业术语（关注度、粉丝黏性、内容迭代、叙事分支），"
            "而非金融术语。'四幕'可理解为'篇章一至四'或'叙事弧'。"
            "策略建议应兼顾艺术价值和商业可持续性。"
        ),
        narrative_term_overrides={
            "博弈混沌": "创意混沌",
            "均衡价格": "内容定位最优解",
            "市场份额": "受众占比",
            "竞争对手": "竞品内容",
            "价格竞争": "内容竞争",
            "定价谈判": "内容协商",
            "拍卖竞价": "注意力竞价",
            "产量竞争": "内容产出竞争",
            "价格战": "流量争夺战",
            "降价抢量": "降质冲量",
            "对抗市场趋势": "对抗行业趋势",
            "市场信号": "流量信号",
            "市场价格": "关注度基准",
            "价格": "关注度指数",
            "降价": "降低创作投入",
            "利润": "影响力收益",
            "成本": "创作成本",
            "出价": "资源投入",
            "止损": "设定底线",
            "调价": "调整策略",
        },
        priority=0,
    ),

    # ── 4. 组织与管理的细胞级优化 / Enterprise ───────────────────────────
    DomainTemplate(
        domain_id="enterprise",
        display_name="组织与管理的细胞级优化 (Enterprise)",
        description="董事会政治、知识管理、人才保留、创新孵化、会议效率",
        keyword_triggers=[
            # 董事会/治理
            "董事会", "股东会", "投票博弈", "公司治理", "高管",
            "董事", "股权", "表决权", "关键摇摆人",
            # 人才
            "人才流失", "离职", "留任", "满意度", "员工",
            "人才管理", "招聘", "绩效", "晋升",
            # 知识/创新
            "知识管理", "信息茧房", "组织学习", "知识传播",
            "创新孵化", "研发", "跨学科", "创意管理",
            # 会议/效率
            "会议效率", "会议管理", "决策效率", "组织效率",
            # 内部博弈
            "内部博弈", "部门博弈", "资源分配", "预算争夺",
            "组织架构", "汇报线", "内部竞争",
            # 通用
            "企业管理", "组织行为", "企业文化", "内部沟通",
        ],
        entity_type_hints=(
            "参与方是企业内部的部门、团队、项目组或个人（高管、董事）。"
            "名称通常为部门名、团队名或人名。"
            "在资源分配场景中，各参与方竞争有限的预算、人力或关注度。"
        ),
        value_semantics=(
            "数值代表预算分配额度、人力编制、项目优先级评分、决策投票权重，"
            "不是市场价格。时间步通常代表周、月或季度。"
        ),
        game_type_preference="negotiation",
        parsing_prompt_additions=(
            "领域上下文：这是一个组织内部管理场景。\n"
            "- 参与方是企业内部的部门、团队或个人\n"
            "- initial_position 表示预算份额、人力编制或决策权重\n"
            "- initial_prices 应理解为资源分配的历史数据\n"
            "- 注意提取组织层级和汇报关系作为博弈约束"
        ),
        sentiment_prompt_additions=(
            "分析角度应为组织管理领域的最新趋势：远程办公对组织凝聚力的影响、"
            "Z世代员工的价值观变化、敏捷组织的兴起、AI 对中层管理的冲击。"
            "分析组织内部的情绪流动和信息传播模式。"
        ),
        narrative_prompt_additions=(
            "报告应使用组织管理术语（资源分配、组织效能、人才密度、创新速率），"
            "而非金融术语。策略建议应符合组织行为学原理。"
        ),
        narrative_term_overrides={
            "博弈混沌": "组织混沌",
            "均衡价格": "最优资源分配点",
            "市场份额": "组织权重",
            "竞争对手": "其他部门/团队",
            "价格竞争": "预算竞争",
            "定价谈判": "资源协商",
            "拍卖竞价": "预算竞标",
            "产量竞争": "产能竞争",
            "价格战": "预算消耗战",
            "降价抢量": "缩减预算抢份额",
            "对抗市场趋势": "对抗组织惯性",
            "市场信号": "组织信号",
            "价格": "资源分配",
            "降价": "削减预算",
            "利润": "组织效能",
            "成本": "管理成本",
            "出价": "资源申请",
            "止损": "设定底线",
            "调价": "调整分配",
        },
        priority=0,
    ),

    # ── 5. 城市与基础设施的神经末梢 / Urban Infrastructure ──────────────
    DomainTemplate(
        domain_id="urban_infrastructure",
        display_name="城市与基础设施的神经末梢 (Urban Infrastructure)",
        description="垃圾清运调度、微气候调节、人流疏导、空间激活、殡葬协调",
        keyword_triggers=[
            # 垃圾/环卫
            "垃圾", "清运", "垃圾桶", "废弃物", "环卫", "回收",
            "废物管理", "垃圾处理",
            # 气候/环境
            "微气候", "城市热岛", "遮阳", "喷雾", "绿化",
            "空气质量", "噪音地图",
            # 人流/交通
            "人流", "人群", "拥挤", "踩踏", "疏导", "瓶颈",
            "机场", "商场", "公交站", "地铁", "排队", "动线",
            "轨道交通", "运力", "负载率", "早高峰", "晚高峰",
            "公共交通", "拥堵", "交通预算", "线路规划", "超载",
            "交通调度", "路网", "枢纽", "站点",
            # 城市空间
            "城市空间", "公共空间", "负空间", "空间激活", "快闪",
            "桥洞", "天台", "临时用途", "场所营造",
            # 殡葬
            "殡葬", "告别", "身后事", "丧葬", "临终",
            # 通用
            "城市管理", "基础设施", "公共服务", "市政", "网格化",
            "智慧城市", "数字孪生",
        ],
        entity_type_hints=(
            "参与方是城市系统的组成部分：区域、设施、服务节点、功能区。"
            "名称通常为地名、设施名或系统名。"
            "在资源调度场景中，各节点竞争有限的服务能力。"
        ),
        value_semantics=(
            "数值代表容量、流量、密度、服务效率或资源消耗率，"
            "不是货币价格。可能是垃圾装满度（%）、人流密度（人/m²）、空间利用率等。"
        ),
        game_type_preference="output_competition",
        parsing_prompt_additions=(
            "领域上下文：这是一个城市基础设施运营场景。\n"
            "- 参与方是城市系统的功能节点（区域、设施、服务点）\n"
            "- initial_position 表示容量、流量或负载率\n"
            "- initial_prices 应理解为运营指标的时间序列\n"
            "- 数值通常带有物理单位（%, m², 人/小时 等）"
        ),
        sentiment_prompt_additions=(
            "分析角度应为城市运营和公共管理领域的最新趋势：智慧城市技术部署、"
            "市民满意度评价体系、环境可持续性压力、公共服务均等化要求。"
            "分析市民情绪和投诉作为实时反馈信号。"
        ),
        narrative_prompt_additions=(
            "报告应使用城市运营术语（负载率、服务半径、响应时间、覆盖率），"
            "而非金融术语。策略建议应聚焦于调度优化和资源配置效率。"
        ),
        narrative_term_overrides={
            "博弈混沌": "城市混沌",
            "均衡价格": "最优负载均衡点",
            "市场份额": "服务覆盖率",
            "竞争对手": "其他区域/节点",
            "价格竞争": "服务效率竞争",
            "定价谈判": "资源调配协商",
            "拍卖竞价": "服务竞价",
            "产量竞争": "吞吐量竞争",
            "价格战": "超负荷运转",
            "降价抢量": "超载抢单",
            "对抗市场趋势": "对抗系统惯性",
            "价格": "服务负载",
            "降价": "降低负载",
            "利润": "运营效率",
            "成本": "运营成本",
            "出价": "资源调配",
            "止损": "设定阈值",
            "调价": "调整调度",
        },
        priority=0,
    ),

    # ── 6. 生态与地球的免疫系统 / Planetary Ecology ─────────────────────
    DomainTemplate(
        domain_id="planetary_ecology",
        display_name="生态与地球的免疫系统 (Planetary Ecology)",
        description="跨境污染追责、濒危物种保护、野火管理、珊瑚礁干预、气候博弈",
        keyword_triggers=[
            # 污染
            "污染", "排放", "碳", "空气污染", "温室气体", "污染源",
            "追责", "跨境污染", "碳排放权",
            # 物种/生态
            "物种", "濒危", "灭绝", "保护", "种群", "栖息地",
            "生物多样性", "生态系统", "中华鲟", "候鸟", "迁徙",
            # 野火
            "野火", "山火", "防火", "以火攻火", "燃烧",
            # 海洋/珊瑚
            "珊瑚", "白化", "海洋", "酸化",
            # 地球工程
            "地球工程", "人工云", "气候干预", "生态修复",
            # 通用
            "生态博弈", "环境保护", "自然资源", "可持续发展",
            "国家公园", "生态补偿", "环境", "气候",
        ],
        entity_type_hints=(
            "参与方是生态实体（物种、生态系统、栖息地）或相关人类组织（国家、NGO、社区）。"
            "名称通常为物种名、地名或组织名。"
            "在多物种博弈中，各物种竞争有限的生态资源（栖息地、食物、水源）。"
        ),
        value_semantics=(
            "数值代表种群数量、栖息地面积（km²）、污染浓度（ppm）、保护资金投入，"
            "不是市场价格。可能是碳排放配额或生态补偿金额。"
        ),
        game_type_preference="output_competition",
        parsing_prompt_additions=(
            "领域上下文：这是一个生态环境场景。\n"
            "- 参与方是生态实体或保护主体（物种、栖息地、国家、NGO）\n"
            "- initial_position 表示种群数量、栖息地面积或污染指数\n"
            "- initial_prices 应理解为生态指标的时间序列\n"
            "- 数值通常带有生态学单位（只/km²、ppm、公顷 等）"
        ),
        sentiment_prompt_additions=(
            "分析角度应为生态环境领域的最新趋势：全球气候政策动向、生物多样性公约进展、"
            "公众环保意识变化、绿色金融发展、极端气候事件频率。"
            "分析各国在环境议题上的立场博弈和舆论压力。"
        ),
        narrative_prompt_additions=(
            "报告应使用生态学术语（种群数量、栖息地、生物多样性指数、生态承载力），"
            "而非金融术语。策略建议应兼顾生态保护效果和经济社会可行性。"
        ),
        narrative_term_overrides={
            "博弈混沌": "生态混沌",
            "均衡价格": "生态承载力均衡",
            "市场份额": "栖息地占比",
            "竞争对手": "竞争物种/地区",
            "价格竞争": "生态位竞争",
            "定价谈判": "保护协商",
            "拍卖竞价": "保护资金竞标",
            "产量竞争": "种群恢复竞争",
            "价格战": "灭绝竞赛",
            "降价抢量": "种群锐减",
            "对抗市场趋势": "对抗自然演替趋势",
            "市场信号": "生态信号",
            "价格": "种群数量",
            "降价": "种群缩减",
            "利润": "生态效益",
            "成本": "保护成本",
            "出价": "保护投入",
            "止损": "濒危警戒线",
            "调价": "调整保护方案",
        },
        priority=0,
    ),

    # ── 7. 元认知与文明演化 / Meta-Civilization ─────────────────────────
    DomainTemplate(
        domain_id="meta_civilization",
        display_name="元认知与文明演化 (Meta-Civilization)",
        description="科学发现的叙事博弈、伦理共识形成、语言演化、反事实历史推演",
        keyword_triggers=[
            # 科学
            "科学发现", "科学范式", "学术博弈", "学说", "理论竞争",
            "科学界", "同行评议", "引用", "科研",
            # 伦理
            "伦理", "道德", "共识", "价值观", "权利",
            "社会规范", "禁忌", "伦理困境",
            # 语言
            "语言演化", "语义", "网络新词", "词汇", "词典",
            "话语权", "叙事", "框架",
            # 历史
            "反事实历史", "历史推演", "如果", "历史博弈",
            "文明演化", "文明兴衰",
            # 科技治理
            "AI安全", "AI治理", "人工智能", "对齐", "监管",
            "有效利他", "长期主义", "政策", "伦理委员会",
            "技术风险", "全球治理", "条约", "倡议",
            # 学术/思想竞争
            "学派", "学说", "主义", "辩论", "学术争论",
            # 通用
            "元认知", "范式转移", "意识形态", "思想市场",
            "观念竞争", "文化演化", "集体意识",
        ],
        entity_type_hints=(
            "参与方是抽象实体：思想流派、理论范式、价值体系、话语体系。"
            "名称通常为学说名、主义名或概念标签。"
            "在历史反事实场景中，参与方是国家、文明或历史人物。"
        ),
        value_semantics=(
            "数值代表学说接受度、引用影响力、话语份额、范式强度指数，"
            "不是货币价格。可能是时间轴上的思想传播率或共识达成度。"
        ),
        game_type_preference="negotiation",
        parsing_prompt_additions=(
            "领域上下文：这是一个思想/文明层面的抽象博弈场景。\n"
            "- 参与方是思想流派、理论范式或价值体系，不是有形实体\n"
            "- initial_position 表示学说接受度或话语影响力指数\n"
            "- initial_prices 应理解为思想传播度的历史序列\n"
            "- 博弈结果不是价格变化，而是共识形成或范式转移"
        ),
        sentiment_prompt_additions=(
            "分析角度应为思想市场的最新趋势：学术出版改革、开放科学运动、"
            "社交媒体对科学传播的影响、意识形态极化的加剧、跨学科融合趋势。"
            "分析全球知识生产格局的变化和不同文明的对话动态。"
        ),
        narrative_prompt_additions=(
            "报告应使用思想史和科学哲学（范式、共识、传播力、说服力），"
            "而非金融术语。'四幕'可理解为'论题-反题-合题-新范式'的辩证过程。"
        ),
        narrative_term_overrides={
            "博弈混沌": "范式混沌",
            "均衡价格": "共识稳定点",
            "市场份额": "话语份额",
            "竞争对手": "对立学说/范式",
            "价格竞争": "范式竞争",
            "定价谈判": "范式协商",
            "拍卖竞价": "学术影响力竞价",
            "产量竞争": "论文产出竞争",
            "价格战": "学术论战",
            "降价抢量": "降低标准追求引用量",
            "对抗市场趋势": "对抗学术惯性",
            "市场信号": "学术信号",
            "价格": "接受度/影响力",
            "降价": "接受度下降",
            "利润": "说服力增益",
            "成本": "论证成本",
            "出价": "论证投入",
            "止损": "捍卫核心主张",
            "调价": "调整论证策略",
        },
        priority=0,
    ),
]


# ── 模板注册与管理 / Template registry and management ─────────────────────

def GCE_classify_domain(
    user_input: str,
    llm_client: Any = None,  # Optional GCE_LLMClient
) -> DomainTemplate:
    """根据用户输入匹配最合适的领域模板 / Classify user input into best-matching domain template.

    两阶段匹配 / Two-stage matching:
      1. 关键词打分（始终执行，离线可用）
      2. LLM 歧义确认（仅在线模式且前两名接近时触发）

    Args:
        user_input: 用户原始输入文本
        llm_client: 可选的 LLM 客户端，仅在在线歧义确认时使用

    Returns:
        匹配的 DomainTemplate，无匹配时返回通用模板
    """
    if not user_input or not user_input.strip():
        return _GENERIC_TEMPLATE

    # 第一阶段：关键词打分 / Stage 1: keyword scoring
    scores: Dict[str, float] = {}
    for template in _DOMAIN_TEMPLATES:
        if not template.keyword_triggers:
            continue
        matches = sum(1 for kw in template.keyword_triggers if kw in user_input)
        if matches > 0:
            scores[template.domain_id] = matches / len(template.keyword_triggers)

    if not scores:
        logger.debug("No domain keywords matched, using generic template")
        return _GENERIC_TEMPLATE

    # 按分数排序 / Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_id, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0

    # 明确获胜：第一名分数 >= 第二名的 2 倍 / Clear winner
    if best_score >= second_score * 2.0 or len(ranked) == 1:
        for t in _DOMAIN_TEMPLATES:
            if t.domain_id == best_id:
                logger.debug("Domain classified: %s (score=%.3f)", best_id, best_score)
                return t

    # 第二阶段：LLM 歧义确认 / Stage 2: LLM disambiguation (online only)
    if llm_client is not None and getattr(llm_client, "enabled", False):
        top_candidates = [
            t for t in _DOMAIN_TEMPLATES
            if t.domain_id in [rid for rid, _ in ranked[:3]]
        ]
        llm_choice = _llm_disambiguate(user_input, top_candidates, llm_client)
        if llm_choice:
            return llm_choice

    # 回退到关键词胜者 / Fallback to keyword winner
    for t in _DOMAIN_TEMPLATES:
        if t.domain_id == best_id:
            return t

    return _GENERIC_TEMPLATE


def _llm_disambiguate(
    user_input: str,
    candidates: List[DomainTemplate],
    llm_client: Any,
) -> Optional[DomainTemplate]:
    """使用 LLM 在歧义领域间确认 / Use LLM to disambiguate between close-matching domains."""
    options = "\n".join(
        f"- {t.domain_id}: {t.description}"
        for t in candidates[:3]
    )
    prompt = (
        f"用户输入：{user_input}\n\n"
        f"请判断上述输入最可能属于以下哪个领域（仅回复领域ID）：\n{options}\n\n"
        f"如果无法确定，回复 'generic'。仅回复ID，不要解释。"
    )
    try:
        messages = [
            {"role": "system", "content": "你是一个文本领域分类器。仅回复领域ID。"},
            {"role": "user", "content": prompt},
        ]
        response = llm_client.GCE_generate(messages)
        if response:
            response = response.strip().lower()
            for t in candidates:
                if t.domain_id in response:
                    return t
    except Exception as e:
        logger.debug("LLM domain disambiguation failed: %s", e)
    return None


def GCE_get_template_by_id(domain_id: str) -> DomainTemplate:
    """通过 ID 查找领域模板 / Look up domain template by ID."""
    if not domain_id:
        return _GENERIC_TEMPLATE
    for template in _DOMAIN_TEMPLATES:
        if template.domain_id == domain_id:
            return template
    return _GENERIC_TEMPLATE


def GCE_register_domain(template: DomainTemplate) -> None:
    """注册新领域模板（用户扩展入口） / Register a new domain template (user extension point)."""
    # 避免重复 / Avoid duplicates
    for i, existing in enumerate(_DOMAIN_TEMPLATES):
        if existing.domain_id == template.domain_id:
            _DOMAIN_TEMPLATES[i] = template
            logger.info("Domain template updated: %s", template.domain_id)
            return
    _DOMAIN_TEMPLATES.append(template)
    logger.info("Domain template registered: %s", template.domain_id)


def GCE_list_domains() -> List[Dict[str, str]]:
    """列出所有已注册领域模板 / List all registered domain templates."""
    return [
        {"domain_id": t.domain_id, "display_name": t.display_name, "description": t.description}
        for t in _DOMAIN_TEMPLATES
    ]
