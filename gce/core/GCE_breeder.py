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

"""繁殖调度器 —— 独立线程，锦标赛选择、交叉、变异 / Breeding scheduler -- independent thread, tournament selection, crossover, mutation."""

from __future__ import annotations

import logging
import random
import time
import uuid
from typing import Any, Dict, List, Optional

from gce.core.GCE_gene import GCE_deserialize_gene, GCE_serialize_gene
from gce.core.GCE_genetic_ops import GCE_crossover, GCE_mutate
from gce.storage.GCE_repository import (
    GCE_get_active_agents,
    GCE_get_agent_count,
    GCE_get_agent_gene_blob,
    GCE_set_agent_energy,
    GCE_set_agent_status,
    GCE_insert_agent,
)

logger = logging.getLogger("gce.core.GCE_breeder")


def GCE_breeding_loop(
    db_path: str,
    config: Dict[str, Any],
    shutdown_flag,  # type: ignore[no-untyped-def]
    rng: Optional[random.Random] = None,
) -> None:
    """繁殖器线程 / Breeder thread.

    定期通过锦标赛选择选出父代，执行交叉和变异，并创建子代博弈元 /
    Periodically selects parents via tournament selection, performs crossover
    and mutation, and creates child agents.
    """
    if rng is None:
        rng = random.Random()

    evo_cfg = config.get("evolution", {})
    reproduce_threshold = evo_cfg.get("reproduce_threshold", 200.0)
    reproduction_cost = evo_cfg.get("reproduction_cost", 80.0)
    initial_energy = evo_cfg.get("initial_energy", 100.0)
    max_population = evo_cfg.get("max_population", 2000)
    tournament_size = evo_cfg.get("tournament_size", 2)
    crossover_rate = evo_cfg.get("crossover_rate", 0.7)
    breeding_interval = evo_cfg.get("breeding_interval_seconds", 2.0)
    max_depth = evo_cfg.get("max_depth", 8)

    while not shutdown_flag.is_set():
        try:
            GCE__breed_one_generation(
                db_path, config, rng, reproduce_threshold, reproduction_cost,
                initial_energy, max_population, tournament_size, crossover_rate,
                max_depth,
            )
        except Exception:
            logger.exception("Breeder error")

        shutdown_flag.wait(timeout=breeding_interval)

    logger.info("Breeder stopped")


def GCE__breed_one_generation(
    db_path: str,
    config: Dict[str, Any],
    rng: random.Random,
    reproduce_threshold: float,
    reproduction_cost: float,
    initial_energy: float,
    max_population: int,
    tournament_size: int,
    crossover_rate: float,
    max_depth: int,
) -> None:
    """执行一轮繁殖 / Perform one round of breeding."""
    # 获取候选者（能量 >= 阈值的博弈元） / Get candidates (agents with energy >= threshold)
    active = GCE_get_active_agents(db_path)
    candidates = [a for a in active if a["energy"] >= reproduce_threshold]

    if len(candidates) < 2:
        return

    # 检查种群数量限制 / Check population limit
    current_count = len(active)
    if current_count >= max_population:
        GCE__cull_low_energy(db_path, active, max_population)

    # 随机打乱 / Shuffle for randomness
    rng.shuffle(candidates)

    # 父代配对，每个 tick 最多生成 5 个新子代 / Pairs of parents, cap at 5 new children per tick
    num_pairs = min(len(candidates) // 2, 5)
    for i in range(num_pairs):
        parent1 = GCE__tournament_select(candidates, tournament_size, rng)
        parent2 = GCE__tournament_select(candidates, tournament_size, rng)

        if parent1["id"] == parent2["id"]:
            continue

        # 反序列化基因 / Deserialize genes
        gene1_blob = GCE_get_agent_gene_blob(db_path, parent1["id"])
        gene2_blob = GCE_get_agent_gene_blob(db_path, parent2["id"])
        if gene1_blob is None or gene2_blob is None:
            continue

        gene1 = GCE_deserialize_gene(gene1_blob)
        gene2 = GCE_deserialize_gene(gene2_blob)

        # 交叉 / Crossover
        if rng.random() < crossover_rate:
            child_gene, _ = GCE_crossover(gene1, gene2, max_depth)
        else:
            child_gene = GCE_deserialize_gene(gene1_blob)  # 克隆父代1 / Clone parent1

        # 变异 / Mutate
        child_gene = GCE_mutate(child_gene, config)

        # 创建子代 / Create child
        child_id = f"agent-{uuid.uuid4().hex[:12]}"
        birth_time = int(time.time() * 1000)
        generation = max(parent1["generation"], parent2["generation"]) + 1

        GCE_insert_agent(
            db_path,
            child_id,
            GCE_serialize_gene(child_gene),
            initial_energy,
            birth_time,
            parent_id=f"{parent1['id']},{parent2['id']}",
            generation=generation,
        )

        # 从父代扣除繁殖成本 / Deduct breeding cost from parents
        GCE_set_agent_energy(db_path, parent1["id"], parent1["energy"] - reproduction_cost / 2)
        GCE_set_agent_energy(db_path, parent2["id"], parent2["energy"] - reproduction_cost / 2)

        logger.debug("Bred child %s (gen=%d) from %s + %s",
                     child_id, generation, parent1["id"][:16], parent2["id"][:16])


def GCE__tournament_select(
    candidates: List[Dict[str, Any]],
    tournament_size: int,
    rng: random.Random,
) -> Dict[str, Any]:
    """从随机锦标赛中选择最佳博弈元 / Select best agent from a random tournament."""
    pool = rng.sample(candidates, min(tournament_size, len(candidates)))
    return max(pool, key=lambda a: a["energy"])


def GCE__cull_low_energy(
    db_path: str,
    active: List[Dict[str, Any]],
    max_population: int,
) -> None:
    """移除低能量博弈元为新博弈元腾出空间 / Remove low-energy agents to make room for new ones."""
    excess = len(active) - max_population + 10  # 额外缓冲 / Extra buffer
    if excess <= 0:
        return

    # 按能量升序排序 / Sort by energy ascending
    sorted_agents = sorted(active, key=lambda a: a["energy"])
    to_cull = sorted_agents[:excess]

    for ag in to_cull:
        GCE_set_agent_status(db_path, ag["id"], "dead")
        logger.debug("Culled agent %s (energy=%.2f) to maintain population limit",
                     ag["id"], ag["energy"])
