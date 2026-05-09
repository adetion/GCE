#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Gaming Chaos Engine V0.1.0
#
# Copyright (C) 2026  Adetion
#
# Contact:
#   Email: i126@126.com
#   Website: wop.cc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ─────────────────────────────────────
# 中文参考 (非法律文本，仅供参考)
#
# 博弈混沌引擎 V0.1.0
# 版权所有 (C) 2026  Adetion
#
# 联系方式：
#   邮箱：i126@126.com
#   网站：wop.cc
#
# 本程序为自由软件；您可以在自由软件基金会发布的
# GNU 通用公共许可证（第3版或更高版本）条款下
# 重新发布和/或修改它。
#
# 本程序发布的目的是希望它能有用，但不提供任何担保，
# 甚至不保证适销性或特定用途的适用性。
# 详细信息请参阅 GNU 通用公共许可证。
#
# 您应该已经随本程序收到一份 GNU 通用公共许可证的副本；
# 如果没有，请参阅 <https://www.gnu.org/licenses/>
"""博弈混沌引擎 (GCE) v0.1.0 —— 主入口 / Gaming Chaos Engine (GCE) v0.1.0 — main entry point."""

import argparse
import os
import sys

# 将项目根目录添加到路径 / Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gce.interface.GCE_cli import GCE_main as cli_main


def GCE_main() -> None:
    """解析命令行参数并启动主程序 / Parse CLI arguments and launch the main program."""
    parser = argparse.ArgumentParser(
        description="博弈混沌引擎 (Gaming Chaos Engine)",
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--offline", "-o",
        action="store_true",
        help="Force offline mode (disable LLM)",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset the database on startup",
    )

    args = parser.parse_args()

    if args.reset_db:
        from gce.utils.GCE_config import GCE_load_config
        config = GCE_load_config(args.config)
        db_path = config.get("database", {}).get("path", "gcds_data.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Database {db_path} removed.")

    # 如果指定了离线模式，覆盖设置 / Override offline mode if specified
    if args.offline:
        os.environ["GCE_FORCE_OFFLINE"] = "1"

    cli_main(config_path=args.config)


if __name__ == "__main__":
    GCE_main()
