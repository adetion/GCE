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

"""多行业实际案例测试 —— 6 个不同行业的博弈场景推演. / Multi-industry case tests — strategic scenario simulation across 6 industries."""

from __future__ import annotations

import json
import math
import multiprocessing
import os
import statistics
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from gce.core.GCE_agent import GCE_agent_main
from gce.core.GCE_breeder import GCE_breeding_loop
from gce.core.GCE_energy import GCE_energy_loop
from gce.core.GCE_gene import GCE_Gene, GCE_serialize_gene
from gce.core.GCE_genetic_ops import FEATURE_COUNT, GCE_random_tree
from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.interface.GCE_narrator import GCE_generate_narrative
from gce.interface.GCE_parser import GCE_parse_scene
from gce.simulation.GCE_engine import GCE_run_simulation
from gce.storage.GCE_database import GCE_init_db
from gce.storage.GCE_repository import (
    GCE_get_active_agents,
    GCE_get_agent_gene_blob,
    GCE_insert_agent,
    GCE_insert_prediction,
    GCE_update_prediction_real_value,
)


# ── 6 industry scenarios (Chinese input, as the system is Chinese-oriented) ──

INDUSTRY_SCENARIOS: List[Dict[str, str]] = [
    {
        "industry": "Finance / 金融",
        "name": "Tech Stock Competition",
        "input": "苹果和微软在AI云服务市场展开为期90天的价格竞争，初始价格分别为每单位API调用0.15美元和0.12美元，目标是最大化市场份额。",
    },
    {
        "industry": "Energy / 能源",
        "name": "Oil Price War",
        "input": "OPEC与北美页岩油生产商在原油市场进行60天的产量博弈，当前油价为每桶75美元和73美元，目标是维持利润同时争夺市场份额。",
    },
    {
        "industry": "E-Commerce / 电商",
        "name": "Holiday Pricing Battle",
        "input": "京东和拼多多在双十一购物节期间进行45天的价格博弈，某品类商品起价分别为299元和279元，目标是最大化GMV。",
    },
    {
        "industry": "Telecom / 电信",
        "name": "5G Spectrum Auction",
        "input": "中国移动、中国电信和中国联通参与5G频谱拍卖，为期30天，初始出价分别为每MHz 1.5亿元、1.3亿元和1.4亿元，目标是获得关键频段。",
    },
    {
        "industry": "Pharma / 医药",
        "name": "Drug Pricing Negotiation",
        "input": "三家跨国药企就某抗癌药物进入医保目录进行120天的定价谈判，初始报价分别为每疗程8万元、6.5万元和7.2万元，目标是最大化进入医保后的总利润。",
    },
    {
        "industry": "Real Estate / 房地产",
        "name": "Land Auction Competition",
        "input": "万科、碧桂园和保利在一线城市核心地块展开90天的竞拍博弈，起拍价分别为每平方米8万元、7.5万元和7.8万元，目标是获取最优开发地块。",
    },
]


def GCE__make_lorenz_events(n: int, start_ts: int = 0) -> List[GCE_RawEvent]:
    """Generate Lorenz-attractor price events for agent training. / 生成 Lorenz 吸引子价格事件用于智能体训练."""
    sigma, rho, beta = 10.0, 28.0, 2.6666667
    x, y, z = 1.0, 1.0, 1.0
    dt = 0.01
    events = []
    for i in range(n):
        # RK4 step
        dx1, dy1, dz1 = sigma * (y - x), x * (rho - z) - y, x * y - beta * z
        mx1, my1, mz1 = x + 0.5 * dt * dx1, y + 0.5 * dt * dy1, z + 0.5 * dt * dz1
        dx2 = sigma * (my1 - mx1)
        dy2 = mx1 * (rho - mz1) - my1
        dz2 = mx1 * my1 - beta * mz1
        mx2 = x + 0.5 * dt * dx2
        my2 = y + 0.5 * dt * dy2
        mz2 = z + 0.5 * dt * dz2
        dx3 = sigma * (my2 - mx2)
        dy3 = mx2 * (rho - mz2) - my2
        dz3 = mx2 * my2 - beta * mz2
        mx3 = x + dt * dx3
        my3 = y + dt * dy3
        mz3 = z + dt * dz3
        dx4 = sigma * (my3 - mx3)
        dy4 = mx3 * (rho - mz3) - my3
        dz4 = mx3 * my3 - beta * mz3
        x += (dt / 6.0) * (dx1 + 2*dx2 + 2*dx3 + dx4)
        y += (dt / 6.0) * (dy1 + 2*dy2 + 2*dy3 + dy4)
        z += (dt / 6.0) * (dz1 + 2*dz2 + 2*dz3 + dz4)

        price = 100.0 + x * 0.5  # Scale Lorenz x to price around 100
        volume = abs(y) * 10 + 1.0
        spread = abs(z) * 0.1 + 0.01

        events.append(GCE_RawEvent(
            source_id="price",
            event_type=GCE_EventType.NUMERIC,
            timestamp=start_ts + i,
            value=price,
            metadata={"volume": str(volume), "spread": str(spread), "lorenz_x": str(x)},
        ))
    return events


def GCE__setup_evolution(db_path: str, tmp_dir: str) -> Tuple[Dict[str, Any], multiprocessing.Queue, threading.Event, Dict[str, multiprocessing.Process], List[threading.Thread]]:
    """Initialize DB, create agents, launch evolution subsystems. / 初始化数据库、创建智能体、启动进化子系统."""

    config = {
        "evolution": {
            "population_initial": 50,
            "max_population": 200,
            "initial_energy": 100.0,
            "reproduce_threshold": 150.0,
            "reproduction_cost": 50.0,
            "base_reward": 10.0,
            "error_scale": 2.0,
            "tournament_size": 2,
            "crossover_rate": 0.7,
            "mutation_rate_base": 0.2,
            "mask_flip_rate": 0.05,
            "max_depth": 6,
            "min_nodes": 3,
            "max_nodes": 40,
            "feature_count": FEATURE_COUNT,
            "window_size": 10,
            "energy_tick_seconds": 0.1,
            "breeding_interval_seconds": 0.2,
        },
        "environment": {"simulator": {"tick_interval": 0.05}},
        "logging": {"level": "ERROR", "file": os.path.join(tmp_dir, "case_test.log")},
        "simulation": {
            "elite_count": 8,
            "future_steps": 30,
            "perturbation_epsilon": 0.001,
            "divergence_threshold": 0.5,
        },
        "narratives_path": os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "narratives.yaml",
        ),
    }

    GCE_init_db(db_path)

    # Create initial population
    import random as _random
    rng = _random.Random(42)
    birth_time = int(time.time() * 1000)
    for i in range(config["evolution"]["population_initial"]):
        agent_id = f"case-agent-{i}"
        mask = 0
        for bit in range(FEATURE_COUNT):
            if rng.random() < 0.6:
                mask |= (1 << bit)
        tree = GCE_random_tree(depth=rng.randint(2, 4), feature_count=FEATURE_COUNT)
        gene = GCE_Gene(mask=mask, tree=tree, mutation_rate=rng.uniform(0.05, 0.3))
        GCE_insert_agent(db_path, agent_id, GCE_serialize_gene(gene), 100.0, birth_time, generation=0)

    # Event queue
    event_queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=2000)

    # Generate Lorenz events and feed them
    events = GCE__make_lorenz_events(500)
    for e in events[:30]:
        event_queue.put(e)

    shutdown_flag = threading.Event()

    def GCE__feed_events():
        idx = 30
        while not shutdown_flag.is_set():
            if idx < len(events):
                try:
                    event_queue.put(events[idx], timeout=0.5)
                    idx += 1
                except Exception:
                    pass
            else:
                idx = 0  # Loop the Lorenz data
            time.sleep(0.03)

    feed_thread = threading.Thread(target=GCE__feed_events, daemon=True)
    feed_thread.start()

    # Launch agent processes
    agent_processes: Dict[str, multiprocessing.Process] = {}
    active = GCE_get_active_agents(db_path)
    for agent_data in active:
        agent_id = agent_data["id"]
        from gce.core.GCE_gene import GCE_deserialize_gene
        gene = GCE_deserialize_gene(agent_data["gene_blob"])

        proc = multiprocessing.Process(
            target=GCE_agent_main,
            args=(agent_id, gene, event_queue, db_path, config),
            daemon=True,
        )
        proc.start()
        agent_processes[agent_id] = proc

    # Start energy manager and breeder
    energy_thread = threading.Thread(
        target=GCE_energy_loop,
        args=(db_path, config, shutdown_flag, agent_processes),
        daemon=True,
    )
    energy_thread.start()

    breeder_thread = threading.Thread(
        target=GCE_breeding_loop,
        args=(db_path, config, shutdown_flag, rng),
        daemon=True,
    )
    breeder_thread.start()

    threads = [feed_thread, energy_thread, breeder_thread]
    return config, event_queue, shutdown_flag, agent_processes, threads


def GCE__run_single_case(
    scenario_input: str,
    db_path: str,
    config: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Run one scenario through the full pipeline. / 对一个场景运行完整流水线."""

    # Parse
    scenario = GCE_parse_scene(scenario_input, None, offline_mode=True)
    if scenario is None:
        return None

    # Simulate
    result = GCE_run_simulation(scenario, db_path, config)
    if result is None:
        return None

    # Narrate
    llm_client = GCE_LLMClient({"llm": {"enabled": False}})
    narratives_path = config.get("narratives_path")
    narrative = GCE_generate_narrative(scenario, result, llm_client, offline_mode=True, narratives_path=narratives_path)

    return {
        "scenario": {
            "participants": [{"name": p.name, "position": p.initial_position} for p in scenario.participants],
            "initial_prices": scenario.initial_prices,
            "time_steps": scenario.time_steps,
            "objective": scenario.objective,
        },
        "result": {
            "consensus_trajectory": result.consensus_trajectory,
            "trajectory_summary": {
                "start": result.consensus_trajectory[0] if result.consensus_trajectory else None,
                "end": result.consensus_trajectory[-1] if result.consensus_trajectory else None,
                "min": min(result.consensus_trajectory) if result.consensus_trajectory else None,
                "max": max(result.consensus_trajectory) if result.consensus_trajectory else None,
                "mean": statistics.mean(result.consensus_trajectory) if result.consensus_trajectory else None,
                "trend": "上升 / Up" if result.consensus_trajectory and result.consensus_trajectory[-1] > result.consensus_trajectory[0] else "下降 / Down",
            },
            "lyapunov_estimate": result.lyapunov_estimate,
            "chaos_regime": (
                "混沌发散 / Chaotic Divergent" if result.lyapunov_estimate > 0.1
                else "弱混沌/准周期 / Weakly Chaotic" if result.lyapunov_estimate > 0.01
                else "临界稳定 / Marginally Stable" if result.lyapunov_estimate > -0.01
                else "收敛稳定 / Convergent Stable"
            ),
            "bifurcation_points": result.bifurcation_points,
            "bifurcation_count": len(result.bifurcation_points),
            "elite_strategies": result.elite_strategies,
        },
        "narrative": narrative,
        "narrative_length": len(narrative) if narrative else 0,
    }


def GCE__cleanup(shutdown_flag: threading.Event, agent_processes: Dict[str, multiprocessing.Process], threads: List[threading.Thread], event_queue: multiprocessing.Queue):
    """Gracefully shut down evolution subsystems. / 优雅关闭进化子系统."""
    shutdown_flag.set()
    for proc in agent_processes.values():
        proc.terminate()
        proc.join(timeout=2.0)
    for t in threads:
        t.join(timeout=2.0)
    event_queue.close()


def main():
    """Run all 6 industry case tests. / 运行全部 6 个行业案例测试."""
    import argparse
    parser = argparse.ArgumentParser(description="GCE Multi-Industry Case Tests")
    parser.add_argument("--evolution-seconds", type=float, default=5.0,
                        help="Seconds to run evolution before testing scenarios (default: 5.0)")
    parser.add_argument("--reports-dir", type=str, default=None,
                        help="Directory for JSON results and narrative files (default: ./reports)")
    args = parser.parse_args()

    # Determine reports directory
    if args.reports_dir:
        reports_dir = os.path.abspath(args.reports_dir)
    else:
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    print("=" * 70)
    print("GCE Multi-Industry Case Tests / 多行业实际案例测试")
    print("=" * 70)
    print(f"Evolution duration: {args.evolution_seconds}s")
    print(f"Number of scenarios: {len(INDUSTRY_SCENARIOS)}")
    print(f"Reports directory: {reports_dir}")
    print()

    # Setup
    tmp_dir = tempfile.mkdtemp(prefix="gce_case_")
    db_path = os.path.join(tmp_dir, "case_test.db")

    print(f"Temp directory: {tmp_dir}")
    print("Setting up evolution environment...")
    config, event_queue, shutdown_flag, agent_processes, threads = GCE__setup_evolution(db_path, tmp_dir)

    # Run evolution
    print(f"Running evolution for {args.evolution_seconds}s...")
    time.sleep(args.evolution_seconds)

    # Check population
    active = GCE_get_active_agents(db_path)
    total_energy = sum(a["energy"] for a in active)
    avg_energy = total_energy / len(active) if active else 0
    print(f"Population after evolution: {len(active)} active agents, avg energy = {avg_energy:.1f}")
    print()

    # Run cases
    results = []
    for i, case in enumerate(INDUSTRY_SCENARIOS):
        print(f"[{i+1}/{len(INDUSTRY_SCENARIOS)}] {case['industry']} — {case['name']}")
        print(f"  Input: {case['input'][:80]}...")

        output = GCE__run_single_case(case["input"], db_path, config)

        if output is None:
            print(f"  FAILED: No output generated")
            results.append({"case": case, "status": "failed", "output": None})
            continue

        regime = output["result"]["chaos_regime"]
        lyap = output["result"]["lyapunov_estimate"]
        bif_count = output["result"]["bifurcation_count"]
        trend = output["result"]["trajectory_summary"]["trend"]
        nar_len = output["narrative_length"]

        print(f"  Regime: {regime}")
        print(f"  Lyapunov: {lyap:.4f} | Bifurcations: {bif_count} | Trend: {trend}")
        print(f"  Narrative: {nar_len} chars, contains 4 acts: "
              f"第一幕={'战场全息重构' in (output['narrative'] or '')}, "
              f"第二幕={'对手心智镜像' in (output['narrative'] or '')}, "
              f"第三幕={'博弈树全展开' in (output['narrative'] or '')}, "
              f"第四幕={'策略指令下达' in (output['narrative'] or '')}")
        print()

        results.append({"case": case, "status": "success", "output": output})

    # Cleanup
    print("Shutting down evolution subsystems...")
    GCE__cleanup(shutdown_flag, agent_processes, threads, event_queue)

    # Summary
    print()
    print("=" * 70)
    print("Results Summary / 结果汇总")
    print("=" * 70)
    for r in results:
        case = r["case"]
        status = r["status"]
        if status == "success":
            o = r["output"]
            print(f"  {case['industry']} | {o['result']['chaos_regime']} | "
                  f"Lyap={o['result']['lyapunov_estimate']:.4f} | "
                  f"Bif={o['result']['bifurcation_count']} | "
                  f"Narrative={o['narrative_length']}chars")
        else:
            print(f"  {case['industry']} | FAILED")

    # Write detailed JSON output to reports directory
    json_path = os.path.join(reports_dir, "case_results.json")
    serializable = []
    for r in results:
        entry = {
            "industry": r["case"]["industry"],
            "name": r["case"]["name"],
            "input": r["case"]["input"],
            "status": r["status"],
        }
        if r["status"] == "success" and r["output"]:
            o = r["output"]
            entry["scenario"] = o["scenario"]
            entry["result"] = o["result"]
            entry["narrative"] = o["narrative"]
            entry["narrative_length"] = o["narrative_length"]
        serializable.append(entry)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    print(f"JSON results written to: {json_path}")

    # Write individual narrative files to reports directory
    narratives_dir = os.path.join(reports_dir, "narratives")
    os.makedirs(narratives_dir, exist_ok=True)
    for r in results:
        if r["status"] == "success" and r["output"] and r["output"]["narrative"]:
            safe_name = r["case"]["name"].replace(" ", "_").replace("/", "_")
            filepath = os.path.join(narratives_dir, f"{safe_name}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Industry: {r['case']['industry']}\n")
                f.write(f"Scenario: {r['case']['name']}\n")
                f.write(f"Input: {r['case']['input']}\n")
                f.write(f"Chaos Regime: {r['output']['result']['chaos_regime']}\n")
                f.write(f"Lyapunov: {r['output']['result']['lyapunov_estimate']:.4f}\n")
                f.write(f"Bifurcation Points: {r['output']['result']['bifurcation_points']}\n")
                f.write("=" * 70 + "\n\n")
                f.write(r["output"]["narrative"])
    print(f"Individual narratives written to: {narratives_dir}")

    # Return failure if any case failed
    failed = sum(1 for r in results if r["status"] == "failed")
    if failed > 0:
        print(f"\n{failed} case(s) FAILED")
        sys.exit(1)

    print("\nAll case tests completed successfully.")


if __name__ == "__main__":
    main()
