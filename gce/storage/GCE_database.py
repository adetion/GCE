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

"""SQLite 数据库初始化和连接管理. / SQLite database initialization and connection management."""

from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict

DDL_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        gene_blob BLOB NOT NULL,
        energy REAL NOT NULL DEFAULT 100.0,
        birth_time INTEGER NOT NULL,
        parent_id TEXT,
        generation INTEGER DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'active'
            CHECK(status IN ('active','dead','paused')),
        process_pid INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        event_timestamp INTEGER NOT NULL,
        predicted_value REAL,
        confidence REAL DEFAULT 1.0,
        publish_time INTEGER NOT NULL,
        real_value REAL,
        accuracy REAL,
        processed INTEGER DEFAULT 0,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )""",
    """CREATE TABLE IF NOT EXISTS raw_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT,
        event_type TEXT,
        value REAL,
        text TEXT,
        timestamp INTEGER UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_pred_agent_time ON predictions(agent_id, event_timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_pred_processed ON predictions(processed)",
    "CREATE INDEX IF NOT EXISTS idx_agent_energy ON agents(energy, status)",
    "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON raw_events(timestamp)",
]

SCHEMA_VERSION = 1


def GCE_get_connection(db_path: str) -> sqlite3.Connection:
    """创建并返回一个新的独立 SQLite 连接. / Create and return a new, independent SQLite connection.

    每个调用者（线程/进程）应调用此函数以获取自己的连接. / Each caller (thread/process) should call this to get its own connection.
    """
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def GCE_init_db(db_path: str) -> None:
    """初始化数据库：创建表、索引并设置模式版本. / Initialize database: create tables, indexes, and set schema version."""
    conn = GCE_get_connection(db_path)
    try:
        for stmt in DDL_STATEMENTS:
            conn.execute(stmt)

        # 模式版本追踪 / Schema version tracking
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        conn.commit()
    finally:
        conn.close()


def GCE_get_schema_version(conn: sqlite3.Connection) -> int:
    """从数据库读取当前模式版本. / Read current schema version from database."""
    row = conn.execute(
        "SELECT value FROM config WHERE key = 'schema_version'"
    ).fetchone()
    if row is None:
        return 0
    return int(row["value"])


def GCE_migrate_db(db_path: str) -> None:
    """必要时运行模式迁移. / Run schema migrations if needed."""
    conn = GCE_get_connection(db_path)
    try:
        current = GCE_get_schema_version(conn)
        if current < SCHEMA_VERSION:
            # 未来的迁移在此处添加 / Future migrations go here
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
            conn.commit()
    finally:
        conn.close()
