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

"""命令行交互界面 —— 主循环 / CLI interactive interface — main loop."""

from __future__ import annotations

import logging
import multiprocessing
import os
import random
import signal
import sys
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from gce.core.GCE_agent import GCE_agent_main
from gce.core.GCE_breeder import GCE_breeding_loop
from gce.core.GCE_energy import GCE_energy_loop
from gce.core.GCE_gene import GCE_Gene, GCE_random_tree
from gce.core.GCE_genetic_ops import FEATURE_COUNT
from gce.environment.GCE_adapters import GCE_create_environment
from gce.environment.GCE_base import GCE_BaseEnvironment
from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.interface.GCE_parser import GCE_parse_scene
from gce.interface.GCE_narrator import GCE_generate_narrative
from gce.simulation.GCE_engine import GCE_run_simulation
from gce.storage.GCE_cleanup import GCE_cleanup_loop
from gce.storage.GCE_database import GCE_init_db, GCE_migrate_db
from gce.storage.GCE_repository import (
    GCE_get_active_agents,
    GCE_get_agent_count,
    GCE_insert_agent,
    GCE_serialize_gene,
    GCE_update_prediction_real_value,
    GCE_insert_event,
)
from gce.utils.GCE_config import GCE_load_config, GCE_validate_config
from gce.utils.GCE_logging import GCE_setup_logging

logger = logging.getLogger("gce.interface.GCE_cli")


def GCE_main(config_path: str = "config.yaml") -> None:
    """CLI主入口点 / Main entry point for the CLI."""
    # 加载并校验配置 / Load & validate config
    config = GCE_load_config(config_path)
    GCE_validate_config(config)

    # 配置日志 / Setup logging
    GCE_setup_logging(config)

    db_path = config.get("database", {}).get("path", "gcds_data.db")

    # 初始化数据库 / Initialize database
    GCE_init_db(db_path)
    GCE_migrate_db(db_path)

    # 配置LLM客户端 / Setup LLM client
    llm_client = GCE_LLMClient(config)
    online_mode = llm_client.enabled
    mode_str = "在线模式 (LLM增强)" if online_mode else "离线模式"
    logger.info("博弈混沌引擎 v0.1.0 启动 (%s)", mode_str)

    # 共享状态 / Shared state
    shutdown_flag = threading.Event()
    agent_processes: Dict[str, multiprocessing.Process] = {}

    # 设置信号处理器以进行优雅关闭 / Setup signal handlers for graceful shutdown
    def GCE__shutdown(signum, frame) -> None:  # type: ignore[no-untyped-def]
        logger.info("Received signal %d, shutting down...", signum)
        shutdown_flag.set()
    signal.signal(signal.SIGINT, GCE__shutdown)
    signal.signal(signal.SIGTERM, GCE__shutdown)

    # 事件总线 / Event bus
    event_queue: multiprocessing.Queue[Any] = multiprocessing.Queue(maxsize=10000)

    # --- 启动子系统 / Start subsystems ---

    # 1. 环境进程 / Environment process
    env = GCE_create_environment(config)
    env_process = multiprocessing.Process(
        target=env.GCE_start,
        args=(event_queue,),
        name="Environment",
        daemon=True,
    )
    env_process.start()

    # 2. 初始化种群（或从数据库恢复）/ Initialize population (or recover from DB)
    GCE__initialize_population(db_path, config)

    # 3. 从活跃智能体启动进程 / Launch agent processes from active agents
    GCE__launch_agents(db_path, config, event_queue, agent_processes)

    # 4. 能量管理线程 / Energy manager thread
    energy_thread = threading.Thread(
        target=GCE_energy_loop,
        args=(db_path, config, shutdown_flag, agent_processes),
        name="EnergyManager",
        daemon=True,
    )
    energy_thread.start()

    # 5. 繁殖线程 / Breeder thread
    rng = random.Random()
    breeder_thread = threading.Thread(
        target=GCE_breeding_loop,
        args=(db_path, config, shutdown_flag, rng),
        name="Breeder",
        daemon=True,
    )
    breeder_thread.start()

    # 6. 清理线程 / Cleanup thread
    cleanup_thread = threading.Thread(
        target=GCE_cleanup_loop,
        args=(db_path, config, shutdown_flag),
        name="Cleanup",
        daemon=True,
    )
    cleanup_thread.start()

    # --- CLI 主循环 / CLI Loop ---
    print("╔══════════════════════════════════════╗")
    print("║   博弈混沌引擎 (GCE) v0.1.0  ║")
    print(f"║   模式: {mode_str:<27}║")
    print("║   输入场景描述开始推演              ║")
    print("║   输入 'quit' 退出                  ║")
    print("║   输入 'status' 查看种群状态        ║")
    print("╚══════════════════════════════════════╝")

    try:
        while not shutdown_flag.is_set():
            try:
                user_input = input("\n> ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                break

            if user_input.lower() == "status":
                GCE__show_status(db_path, llm_client)
                continue

            # 解析场景 / Parse scenario
            print("解析场景...")
            scenario = GCE_parse_scene(user_input, llm_client, offline_mode=not online_mode)
            if scenario is None:
                print("无法解析场景，请使用更清晰的描述，或开启在线模式。")
                continue

            # 运行推演 / Run simulation
            print(f"推演中（{scenario.time_steps}步，{len(scenario.participants)}个参与方）...")
            result = GCE_run_simulation(scenario, db_path, config)
            if result is None:
                print("推演失败：没有可用的精英博弈元。请等待种群进化后重试。")
                continue

            # 生成叙事报告 / Generate narrative
            print("生成报告...")
            narratives_path = config.get("narratives_path", "narratives.yaml")
            narrative = GCE_generate_narrative(
                scenario, result, llm_client,
                offline_mode=not online_mode,
                narratives_path=narratives_path,
            )
            print("\n" + narrative)

    finally:
        # 优雅关闭 / Graceful shutdown
        logger.info("Shutting down...")
        shutdown_flag.set()

        # 停止环境进程 / Stop environment
        env.GCE_stop()
        env_process.join(timeout=5.0)
        if env_process.is_alive():
            env_process.terminate()

        # 停止所有智能体进程 / Stop all agent processes
        for agent_id, proc in list(agent_processes.items()):
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=2.0)
        agent_processes.clear()

        # 等待线程结束 / Wait for threads
        for t in [energy_thread, breeder_thread, cleanup_thread]:
            t.join(timeout=3.0)

        event_queue.close()
        logger.info("System shutdown complete")


def GCE__initialize_population(db_path: str, config: Dict[str, Any]) -> None:
    """在数据库为空时初始化智能体种群 / Initialize the agent population if the database is empty."""
    count = GCE_get_agent_count(db_path)
    if count > 0:
        logger.info("Recovering %d active agents from database", count)
        return

    evo_cfg = config.get("evolution", {})
    pop_initial = evo_cfg.get("population_initial", 100)
    initial_energy = evo_cfg.get("initial_energy", 100.0)
    max_depth = evo_cfg.get("max_depth", 8)
    feature_count = evo_cfg.get("feature_count", FEATURE_COUNT)
    rng = random.Random(config.get("environment", {}).get("seed"))

    logger.info("Initializing population of %d agents", pop_initial)
    birth_time = int(time.time() * 1000)

    for i in range(pop_initial):
        agent_id = f"agent-{uuid.uuid4().hex[:12]}"
        # 随机掩码：选择约60%的特征 / Random mask: select ~60% of features
        mask = 0
        for bit in range(feature_count):
            if rng.random() < 0.6:
                mask |= (1 << bit)

        tree = GCE_random_tree(depth=rng.randint(2, max_depth), feature_count=feature_count)
        gene = GCE_Gene(mask=mask, tree=tree, mutation_rate=rng.uniform(0.05, 0.3))

        GCE_insert_agent(
            db_path,
            agent_id,
            GCE_serialize_gene(gene),
            initial_energy,
            birth_time,
            generation=0,
        )

    logger.info("Population initialized: %d agents", pop_initial)


def GCE__launch_agents(
    db_path: str,
    config: Dict[str, Any],
    event_queue: multiprocessing.Queue,  # type: ignore[type-arg]
    agent_processes: Dict[str, multiprocessing.Process],
) -> None:
    """为所有活跃智能体启动进程 / Launch processes for all active agents."""
    active = GCE_get_active_agents(db_path)

    from gce.core.GCE_gene import GCE_deserialize_gene

    for agent in active:
        gene_blob = agent["gene_blob"]
        if gene_blob is None:
            continue
        gene = GCE_deserialize_gene(gene_blob)

        proc = multiprocessing.Process(
            target=GCE_agent_main,
            args=(agent["id"], gene, event_queue, db_path, config),
            name=f"Agent-{agent['id'][:12]}",
            daemon=True,
        )
        proc.start()
        agent_processes[agent["id"]] = proc

    logger.info("Launched %d agent processes", len(agent_processes))


def GCE__show_status(db_path: str, llm_client: GCE_LLMClient) -> None:
    """显示当前系统状态 / Display current system status."""
    active = GCE_get_active_agents(db_path)
    count = len(active)
    if count == 0:
        print("种群为空，等待初始化...")
        return

    energies = [a["energy"] for a in active]
    generations = [a["generation"] for a in active]
    avg_energy = sum(energies) / count
    max_energy = max(energies)
    min_energy = min(energies)
    max_gen = max(generations)
    avg_gen = sum(generations) / count

    print(f"种群规模: {count}")
    print(f"能量范围: {min_energy:.1f} ~ {max_energy:.1f} (均 {avg_energy:.1f})")
    print(f"代数范围: 0 ~ {max_gen} (均 {avg_gen:.1f})")
    llm_stats = llm_client.GCE_stats
    if llm_stats["calls"] > 0:
        print(f"LLM调用: {llm_stats['calls']}次 (均 {llm_stats['avg_latency']:.2f}s)")
    else:
        print("LLM调用: 0次")
