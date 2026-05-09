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

"""配置加载、验证与环境变量替换 / Configuration loading, validation, and environment variable substitution."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

_ENV_VAR_RE = re.compile(r"\$\{(\w+)\}")


def GCE__replace_env_vars(value: Any) -> Any:
    """递归替换配置值中的${VAR}模式 / Recursively replace ${VAR} patterns in config values."""
    if isinstance(value, str):
        def GCE__replacer(m: re.Match) -> str:
            var_name = m.group(1)
            env_val = os.environ.get(var_name, "")
            if not env_val:
                print(f"WARNING: Environment variable '{var_name}' not set, using empty string.")
            return env_val

        return _ENV_VAR_RE.sub(GCE__replacer, value)
    if isinstance(value, dict):
        return {k: GCE__replace_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [GCE__replace_env_vars(v) for v in value]
    return value


def GCE_load_config(path: str | Path) -> Dict[str, Any]:
    """加载YAML配置文件并替换环境变量 / Load YAML config file and replace environment variables."""
    path = Path(path)
    if not path.exists():
        print(f"FATAL: Config file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        print(f"FATAL: Config file is empty: {path}")
        sys.exit(1)

    return GCE__replace_env_vars(raw)


def GCE_validate_config(config: Dict[str, Any]) -> None:
    """校验配置参数取值范围，遇到致命错误则退出 / Validate config value ranges. Exits on fatal errors."""
    errors: list[str] = []

    # 进化参数校验 / evolution section
    evo = config.get("evolution", {})
    if evo.get("population_initial", 0) <= 0:
        errors.append("evolution.population_initial must be > 0")
    if evo.get("max_population", 0) <= 0:
        errors.append("evolution.max_population must be > 0")
    if evo.get("initial_energy", 0) <= 0:
        errors.append("evolution.initial_energy must be > 0")
    if evo.get("reproduce_threshold", 0) <= 0:
        errors.append("evolution.reproduce_threshold must be > 0")
    if evo.get("reproduction_cost", 0) < 0:
        errors.append("evolution.reproduction_cost must be >= 0")
    if evo.get("max_depth", 0) < 2:
        errors.append("evolution.max_depth must be >= 2")
    if evo.get("min_nodes", 0) < 1:
        errors.append("evolution.min_nodes must be >= 1")
    if evo.get("max_nodes", 0) < evo.get("min_nodes", 0):
        errors.append("evolution.max_nodes must be >= evolution.min_nodes")
    if not (0.0 <= evo.get("crossover_rate", 0) <= 1.0):
        errors.append("evolution.crossover_rate must be in [0, 1]")
    if not (0.0 <= evo.get("mutation_rate_base", 0) <= 1.0):
        errors.append("evolution.mutation_rate_base must be in [0, 1]")

    # 环境参数校验 / environment section
    env = config.get("environment", {})
    sim = env.get("simulator", {})
    if sim.get("tick_interval", 0) <= 0:
        errors.append("environment.simulator.tick_interval must be > 0")
    if sim.get("num_market_agents", 0) < 2:
        errors.append("environment.simulator.num_market_agents must be >= 2")

    # 数据库参数校验 / database section
    db = config.get("database", {})
    if not db.get("path"):
        errors.append("database.path must not be empty")

    # 仿真参数校验 / simulation section
    sim_cfg = config.get("simulation", {})
    if sim_cfg.get("elite_count", 0) < 1:
        errors.append("simulation.elite_count must be >= 1")
    if sim_cfg.get("future_steps", 0) < 1:
        errors.append("simulation.future_steps must be >= 1")
    if sim_cfg.get("perturbation_epsilon", 0) <= 0:
        errors.append("simulation.perturbation_epsilon must be > 0")
    if sim_cfg.get("divergence_threshold", 0) <= 0:
        errors.append("simulation.divergence_threshold must be > 0")

    # 日志参数校验 / logging section
    log_cfg = config.get("logging", {})
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_cfg.get("level", "INFO").upper() not in valid_levels:
        errors.append(f"logging.level must be one of {valid_levels}")

    if errors:
        for e in errors:
            print(f"FATAL: {e}")
        sys.exit(1)
