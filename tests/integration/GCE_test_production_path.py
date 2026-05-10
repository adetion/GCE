#
# -*- coding: utf-8 -*-
#
# ... (license header same as all other files) ...

"""生产环境路径验证测试 —— 直接测试 GCE_main.py → GCE_cli.py 完整导入链及核心函数. / Production-path verification — tests GCE_main.py → GCE_cli.py import chain and core functions."""

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
from typing import Any, Dict, List

import pytest

from gce.core.GCE_agent import GCE_agent_main
from gce.core.GCE_breeder import GCE_breeding_loop
from gce.core.GCE_energy import GCE_energy_loop
from gce.core.GCE_gene import GCE_Gene, GCE_serialize_gene, GCE_deserialize_gene
from gce.core.GCE_genetic_ops import FEATURE_COUNT, GCE_random_tree
from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
from gce.interface.GCE_llm_client import GCE_LLMClient
from gce.interface.GCE_parser import GCE_parse_scene
from gce.interface.GCE_narrator import GCE_generate_narrative
from gce.simulation.GCE_engine import GCE_run_simulation
from gce.storage.GCE_database import GCE_init_db
from gce.storage.GCE_repository import (
    GCE_get_active_agents,
    GCE_get_agent_count,
    GCE_insert_agent,
    GCE_insert_prediction,
    GCE_update_prediction_real_value,
)


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SCENARIOS = [
    {
        "industry": "Finance / 金融",
        "name": "Tech_Stock_Competition",
        "input": "苹果和微软在AI云服务市场展开为期90天的价格竞争，初始价格分别为每单位API调用0.15美元和0.12美元，目标是最大化市场份额。",
    },
    {
        "industry": "Energy / 能源",
        "name": "Oil_Price_War",
        "input": "OPEC与北美页岩油生产商在原油市场进行60天的产量博弈，当前油价为每桶75美元和73美元，目标是维持利润同时争夺市场份额。",
    },
    {
        "industry": "E-Commerce / 电商",
        "name": "Holiday_Pricing_Battle",
        "input": "京东和拼多多在双十一购物节期间进行45天的价格博弈，某品类商品起价分别为299元和279元，目标是最大化GMV。",
    },
    {
        "industry": "Telecom / 电信",
        "name": "5G_Spectrum_Auction",
        "input": "中国移动、中国电信和中国联通参与5G频谱拍卖，为期30天，初始出价分别为每MHz 1.5亿元、1.3亿元和1.4亿元，目标是获得关键频段。",
    },
    {
        "industry": "Pharma / 医药",
        "name": "Drug_Pricing_Negotiation",
        "input": "三家跨国药企就某抗癌药物进入医保目录进行120天的定价谈判，初始报价分别为每疗程8万元、6.5万元和7.2万元，目标是最大化进入医保后的总利润。",
    },
    {
        "industry": "Real Estate / 房地产",
        "name": "Land_Auction_Competition",
        "input": "万科、碧桂园和保利在一线城市核心地块展开90天的竞拍博弈，起拍价分别为每平方米8万元、7.5万元和7.8万元，目标是获取最优开发地块。",
    },
]


class GCE_TestProductionPath:
    """验证生产代码路径的端到端工作. / Verify production code path works end-to-end."""

    def GCE_test_gce_main_imports(self):
        """GCE_main.py 入口点及所有生产模块可成功导入. / GCE_main.py entry point and all production modules import successfully."""
        # Test the exact import chain that GCE_main.py uses
        from gce.interface.GCE_cli import GCE_main as cli_main
        assert cli_main is not None

        # Verify key functions are accessible
        from gce.utils.GCE_config import GCE_load_config, GCE_validate_config
        from gce.utils.GCE_logging import GCE_setup_logging
        from gce.environment.GCE_adapters import GCE_create_environment
        from gce.storage.GCE_cleanup import GCE_cleanup_loop
        assert True  # All imports succeeded

    def GCE_test_production_pipeline_with_evolution(self, tmp_path):
        """完整体验生产流水线：初始化种群 → 进化 → 场景推演 → 叙事生成. / Full production pipeline: init population → evolve → simulate → narrate."""
        db_path = str(tmp_path / "prod_test.db")
        reports_dir = os.path.join(PROJECT_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        config = {
            "evolution": {
                "population_initial": 30,
                "max_population": 100,
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
            "logging": {"level": "ERROR", "file": str(tmp_path / "prod.log")},
            "simulation": {
                "elite_count": 8,
                "future_steps": 30,
                "perturbation_epsilon": 0.001,
                "divergence_threshold": 0.5,
            },
            "narratives_path": os.path.join(PROJECT_DIR, "narratives.yaml"),
        }

        # Phase 1: Initialize database (production code path: GCE_init_db)
        GCE_init_db(db_path)

        # Phase 2: Create initial population (production code path: GCE_cli.GCE__initialize_population)
        import random as _random
        rng = _random.Random(42)
        birth_time = int(time.time() * 1000)
        for i in range(config["evolution"]["population_initial"]):
            agent_id = f"prod-agent-{i}"
            mask = 0
            for bit in range(FEATURE_COUNT):
                if rng.random() < 0.6:
                    mask |= (1 << bit)
            tree = GCE_random_tree(depth=rng.randint(2, 4), feature_count=FEATURE_COUNT)
            gene = GCE_Gene(mask=mask, tree=tree, mutation_rate=rng.uniform(0.05, 0.3))
            GCE_insert_agent(db_path, agent_id, GCE_serialize_gene(gene), 100.0, birth_time, generation=0)

        assert GCE_get_agent_count(db_path) == 30, "Initial population should be 30"

        # Phase 3: Run mini-evolution (production code path: GCE_agent_main, GCE_energy_loop, GCE_breeding_loop)
        event_queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=1000)
        shutdown_flag = threading.Event()

        # Lorenz event feed
        def GCE__make_lorenz_events(n: int) -> List[GCE_RawEvent]:
            sigma, rho, beta = 10.0, 28.0, 2.6666667
            x, y, z = 1.0, 1.0, 1.0
            dt = 0.01
            events = []
            for step in range(n):
                dx1, dy1, dz1 = sigma * (y - x), x * (rho - z) - y, x * y - beta * z
                mx1, my1, mz1 = x + 0.5*dt*dx1, y + 0.5*dt*dy1, z + 0.5*dt*dz1
                dx2 = sigma*(my1 - mx1)
                dy2 = mx1*(rho - mz1) - my1
                dz2 = mx1*my1 - beta*mz1
                mx2 = x + 0.5*dt*dx2
                my2 = y + 0.5*dt*dy2
                mz2 = z + 0.5*dt*dz2
                dx3 = sigma*(my2 - mx2)
                dy3 = mx2*(rho - mz2) - my2
                dz3 = mx2*my2 - beta*mz2
                mx3 = x + dt*dx3
                my3 = y + dt*dy3
                mz3 = z + dt*dz3
                dx4 = sigma*(my3 - mx3)
                dy4 = mx3*(rho - mz3) - my3
                dz4 = mx3*my3 - beta*mz3
                x += (dt/6)*(dx1 + 2*dx2 + 2*dx3 + dx4)
                y += (dt/6)*(dy1 + 2*dy2 + 2*dy3 + dy4)
                z += (dt/6)*(dz1 + 2*dz2 + 2*dz3 + dz4)
                events.append(GCE_RawEvent(
                    source_id="price",
                    event_type=GCE_EventType.NUMERIC,
                    timestamp=step,
                    value=100.0 + x * 0.5,
                    metadata={"volume": str(abs(y)*10 + 1), "spread": str(abs(z)*0.1 + 0.01), "lorenz_x": str(x)},
                ))
            return events

        events = GCE__make_lorenz_events(500)
        for e in events[:30]:
            event_queue.put(e)

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
                    idx = 0
                time.sleep(0.03)

        feed_thread = threading.Thread(target=GCE__feed_events, daemon=True)
        feed_thread.start()

        # Launch agent processes (production code path)
        agent_processes: Dict[str, multiprocessing.Process] = {}
        active = GCE_get_active_agents(db_path)
        for agent_data in active:
            agent_id = agent_data["id"]
            gene = GCE_deserialize_gene(agent_data["gene_blob"])
            proc = multiprocessing.Process(
                target=GCE_agent_main,
                args=(agent_id, gene, event_queue, db_path, config),
                daemon=True,
            )
            proc.start()
            agent_processes[agent_id] = proc

        # Energy + breeder threads (production code path)
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

        # Evolve
        time.sleep(6.0)

        # Verify population survived
        active_count = GCE_get_agent_count(db_path)
        assert active_count > 0, "All agents died during evolution"

        # Phase 4: Run all 6 scenarios through production pipeline
        results = []
        for scenario_def in SCENARIOS:
            # Parse (production code path: GCE_parse_scene)
            scenario = GCE_parse_scene(scenario_def["input"], None, offline_mode=True)
            assert scenario is not None, f"Failed to parse: {scenario_def['name']}"

            # Simulate (production code path: GCE_run_simulation)
            result = GCE_run_simulation(scenario, db_path, config)
            assert result is not None, f"Simulation failed: {scenario_def['name']}"

            # Narrate (production code path: GCE_generate_narrative)
            llm_client = GCE_LLMClient({"llm": {"enabled": False}})
            narrative = GCE_generate_narrative(
                scenario, result, llm_client, offline_mode=True,
                narratives_path=config["narratives_path"],
            )
            assert narrative is not None, f"Narrative failed: {scenario_def['name']}"
            assert len(narrative) > 100, f"Narrative too short: {len(narrative)}"
            assert "战场全息重构" in narrative, "Missing Act I"
            assert "对手心智镜像" in narrative, "Missing Act II"
            assert "博弈树全展开" in narrative, "Missing Act III"
            assert "策略指令下达" in narrative, "Missing Act IV"

            results.append({
                "industry": scenario_def["industry"],
                "name": scenario_def["name"],
                "input": scenario_def["input"],
                "lyapunov": result.lyapunov_estimate,
                "bifurcations": len(result.bifurcation_points),
                "narrative_length": len(narrative),
                "four_acts": True,
            })

            # Save narrative
            safe_name = scenario_def["name"]
            narr_path = os.path.join(reports_dir, "narratives", f"PROD_{safe_name}.txt")
            with open(narr_path, "w", encoding="utf-8") as f:
                f.write(f"Production-Path Verified / 生产路径已验证\n")
                f.write(f"Industry: {scenario_def['industry']}\n")
                f.write(f"Scenario: {scenario_def['name']}\n")
                f.write(f"Lyapunov: {result.lyapunov_estimate:.4f}\n")
                f.write("=" * 70 + "\n\n")
                f.write(narrative)

        # Save JSON
        json_path = os.path.join(reports_dir, "production_test_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Cleanup
        shutdown_flag.set()
        for proc in agent_processes.values():
            proc.terminate()
            proc.join(timeout=2.0)
        for t in [feed_thread, energy_thread, breeder_thread]:
            t.join(timeout=2.0)
        event_queue.close()

        # Assertions
        assert len(results) == 6, f"Expected 6 results, got {len(results)}"
        for r in results:
            assert r["four_acts"], f"Missing acts in {r['name']}"
            assert r["narrative_length"] > 100, f"Short narrative in {r['name']}"

    def GCE_test_gce_main_module_imports_correctly(self):
        """验证 GCE_main.py 自身无语法错误且可导入. / Verify GCE_main.py has no syntax errors and can be imported."""
        # This tests the actual file that users run
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "GCE_main",
            os.path.join(PROJECT_DIR, "GCE_main.py"),
        )
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        # Just verify it loads without error
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"GCE_main.py failed to load: {e}")

        assert hasattr(module, "GCE_main"), "GCE_main.py should export GCE_main function"
