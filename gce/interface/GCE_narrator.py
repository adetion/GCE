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

"""叙事生成器 —— 四幕叙事报告（在线/离线双模式） / Narrative generator — four-act report (online/offline dual mode)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.simulation.GCE_schemas import GCE_Scenario, GCE_SimulationResult

import yaml

logger = logging.getLogger("gce.interface.GCE_narrator")

_SYSTEM_PROMPT = """你是一位顶级战略顾问，擅长博弈论和混沌动力学。你的任务是根据推演数据撰写一份决策报告。报告必须包含以下四部分：
1. 战场全息重构：以相空间视角描述当前博弈场的动力学结构，指出是收敛、震荡还是混沌。
2. 对手心智镜像：基于数据中智能体的预测行为模式，推断各方的可能决策逻辑和敏感点。
3. 博弈树全展开：阐述关键分岔点和可能的结果分支，说明每个分支出现的条件。
4. 策略指令下达：给出最佳行动建议，包括时机、力度和微扰策略。务必使其可以立即执行。
请用犀利清晰的中文回答。"""


def GCE__build_user_message(scenario: GCE_Scenario, result: GCE_SimulationResult) -> str:
    """构建包含所有数值结果的数据丰富的用户消息 / Build the data-rich user message with all numerical results."""
    trajectory_str = ", ".join(f"{v:.3f}" for v in result.consensus_trajectory)
    bifurcation_str = ", ".join(f"t={t}" for t in result.bifurcation_points) if result.bifurcation_points else "无显著分岔点"

    return f"""场景: {scenario.objective}
参与方: {", ".join(p.name for p in scenario.participants)}
预测步数: {scenario.time_steps}

共识轨迹: [{trajectory_str}]
李雅普诺夫指数估计: {result.lyapunov_estimate:.6f}
分岔候选点: {bifurcation_str}

精英博弈元数量: {result.elite_strategies.get('elite_count', 0)}
预测分布统计: {result.elite_strategies.get('prediction_distribution', {})}"""


def GCE_generate_narrative(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    llm_client: GCE_LLMClient,
    offline_mode: bool = False,
    narratives_path: Optional[str] = None,
) -> str:
    """生成四幕叙事报告，LLM可用时优先使用，否则回退到模板 / Generate a four-act narrative report.

    Uses LLM if available; falls back to template-based offline narrative.
    """
    if not offline_mode and llm_client.enabled:
        narrative = GCE__generate_online(scenario, result, llm_client)
        if narrative:
            return narrative
        logger.warning("Online narrative generation failed, using offline template")

    return GCE__generate_offline(scenario, result, narratives_path)


def GCE__generate_online(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    llm_client: GCE_LLMClient,
) -> Optional[str]:
    """通过LLM生成叙事报告 / Generate narrative via LLM."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": GCE__build_user_message(scenario, result)},
    ]
    return llm_client.GCE_generate(messages)


def GCE__generate_offline(
    scenario: GCE_Scenario,
    result: GCE_SimulationResult,
    narratives_path: Optional[str] = None,
) -> str:
    """使用YAML文件中的模板生成叙事报告 / Generate narrative using template from YAML file."""
    # 加载模板（如果可用）/ Load template if available
    template = GCE__load_narrative_template(narratives_path)

    traj = result.consensus_trajectory
    lyap = result.lyapunov_estimate
    bifurcations = result.bifurcation_points

    # 判断动力学状态 / Determine regime
    if lyap > 0.1:
        regime = "混沌发散 (Chaotic Divergent)"
        regime_desc = "系统处于高度不可预测状态，微小扰动将导致截然不同的结果。建议仅关注短周期（<5步）预测，并采取分散化的微扰策略。"
    elif lyap > 0.01:
        regime = "弱混沌/准周期 (Weakly Chaotic)"
        regime_desc = "系统存在可辨识的吸引子结构，中期预测具备参考价值，但需为分岔点附近的结果跳变做好准备。"
    elif lyap > -0.01:
        regime = "边际稳定 (Marginally Stable)"
        regime_desc = "系统对小扰动保持中性，预测轨迹可靠度较高。可在分岔候选点适时介入，引导系统向有利方向演化。"
    else:
        regime = "收敛稳定 (Convergent Stable)"
        regime_desc = "系统具有强吸引子，预测结果高度可信。可沿共识轨迹制定确定性策略，但仍需监控临界点附近的相变。"

    trajectory_str = " → ".join(f"{v:.3f}" for v in traj[:10])
    if len(traj) > 10:
        trajectory_str += f" ... (共{len(traj)}步)"

    bifurcation_str = ", ".join(f"第{t}步" for t in bifurcations[:5]) if bifurcations else "无明显分岔点"
    if len(bifurcations) > 5:
        bifurcation_str += f" ... 等共{len(bifurcations)}个候选点"

    narrative = template.format(
        objective=scenario.objective,
        participants=", ".join(p.name for p in scenario.participants),
        time_steps=scenario.time_steps,
        trajectory_str=trajectory_str,
        lyapunov_estimate=f"{lyap:.6f}",
        regime=regime,
        regime_desc=regime_desc,
        bifurcation_points=bifurcation_str,
        elite_count=result.elite_strategies.get("elite_count", 0),
    )

    return narrative


_DEFAULT_TEMPLATE = """═══════════════════════════════
  博弈混沌推演决策报告
═══════════════════════════════

【场景】{objective}
【参与方】{participants}
【推演步数】{time_steps} 步

━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、战场全息重构
━━━━━━━━━━━━━━━━━━━━━━━━━━━

动力学状态: {regime}

{regime_desc}

共识轨迹 (前段): [{trajectory_str}]
李雅普诺夫指数估计: {lyapunov_estimate}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、对手心智镜像
━━━━━━━━━━━━━━━━━━━━━━━━━━━

基于 {elite_count} 个精英博弈元的预测行为模式分析，各参与方的决策逻辑呈现出以下特征:

- 参与方的策略空间在相空间中形成了可辨识的吸引域，表明存在某种形式的纳什均衡结构。
- 精英博弈元的预测分布离散度反映了当前信息不对称程度。高离散度意味着各方对局势的解读存在显著分歧，这本身构成可利用的信息优势。
- 建议关注预测分布中偏离共识最远的博弈元——它们可能代表对手的非常规策略。

━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、博弈树全展开
━━━━━━━━━━━━━━━━━━━━━━━━━━━

分岔候选点: {bifurcation_points}

关键结果分支:

1. 若在分岔点之前采取主动干预，系统大概率被引导至收敛区域，形成稳定的纳什均衡。
2. 若不干预，系统将自然演化至混沌区域，结果的不可预测性急剧增加。
3. 在分岔点恰当时机的微扰（幅度约为当前波动率的1-2倍）可将系统切换至不同的吸引盆。

每个分支的出现概率取决于当前系统状态与分岔点的距离。距离越近，干预成本越低，成功率越高。

━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、策略指令下达
━━━━━━━━━━━━━━━━━━━━━━━━━━━

【即时行动】
1. 在下一个分岔候选点到来之前（约1-3步），部署监测指标，确认系统是否确实接近相变边界。
2. 准备微扰策略：对系统中最敏感的维度施加小幅调整（建议幅度 0.5-1.0 个单位），观察响应。

【中期布局】
3. 若李雅普诺夫指数持续为正，采用"频繁小额干预"策略，以维持系统在可控吸引域内。
4. 若指数转负，转为"阶段性大额干预"策略，引导系统收敛至有利均衡。

【风险管控】
5. 设定止损边界：若共识轨迹偏离预期超过2个标准差，立即撤回干预并重新评估。
6. 保持至少3个博弈元的策略多样性，确保在任何分岔方向上都存在适应性策略储备。

═══════════════════════════════
  报告结束 | 建议复核周期: 每 {time_steps} 步
═══════════════════════════════"""


def GCE__load_narrative_template(path: Optional[str]) -> str:
    """从YAML文件加载叙事模板，失败则使用默认模板 / Load narrative template from YAML file, or use default."""
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "template" in data:
                    return str(data["template"])
        except Exception as e:
            logger.warning("Failed to load narrative template: %s, using default", e)
    return _DEFAULT_TEMPLATE
