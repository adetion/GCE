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

"""数据访问层 —— 所有 CRUD 操作，含重试逻辑. / Data access layer — all CRUD operations with retry logic."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from gce.storage.GCE_database import GCE_get_connection
from gce.utils.GCE_retry import GCE_retry_on_lock


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_insert_agent(
    db_path: str,
    agent_id: str,
    gene_blob: bytes,
    energy: float,
    birth_time: int,
    parent_id: Optional[str] = None,
    generation: int = 0,
    process_pid: Optional[int] = None,
) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO agents (id, gene_blob, energy, birth_time,
               parent_id, generation, status, process_pid)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?)""",
            (agent_id, gene_blob, energy, birth_time, parent_id, generation, process_pid),
        )
        conn.commit()
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_update_energy(db_path: str, agent_id: str, reward: float) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            "UPDATE agents SET energy = energy + ? WHERE id = ?",
            (reward, agent_id),
        )
        conn.commit()
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_set_agent_status(db_path: str, agent_id: str, status: str) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            "UPDATE agents SET status = ? WHERE id = ?",
            (status, agent_id),
        )
        conn.commit()
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_set_agent_energy(db_path: str, agent_id: str, energy: float) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            "UPDATE agents SET energy = ? WHERE id = ?",
            (energy, agent_id),
        )
        conn.commit()
    finally:
        conn.close()


def GCE_get_agent_energy(db_path: str, agent_id: str) -> float:
    conn = GCE_get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT energy FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return row["energy"] if row else 0.0
    finally:
        conn.close()


def GCE_get_agent_gene_blob(db_path: str, agent_id: str) -> Optional[bytes]:
    conn = GCE_get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT gene_blob FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return row["gene_blob"] if row else None
    finally:
        conn.close()


def GCE_get_active_agents(db_path: str) -> List[Dict[str, Any]]:
    conn = GCE_get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM agents WHERE status = 'active'"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def GCE_get_agents_below_energy(db_path: str, threshold: float) -> List[Dict[str, Any]]:
    conn = GCE_get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM agents WHERE energy <= ? AND status = 'active'",
            (threshold,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def GCE_get_agents_above_energy(db_path: str, threshold: float) -> List[Dict[str, Any]]:
    conn = GCE_get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM agents WHERE energy >= ? AND status = 'active'",
            (threshold,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def GCE_get_elite_agents(db_path: str, count: int) -> List[Dict[str, Any]]:
    conn = GCE_get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM agents WHERE status = 'active' ORDER BY energy DESC LIMIT ?",
            (count,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def GCE_get_agent_count(db_path: str) -> int:
    conn = GCE_get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM agents WHERE status = 'active'"
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_insert_prediction(
    db_path: str,
    agent_id: str,
    event_timestamp: int,
    predicted_value: float,
    confidence: float = 1.0,
    publish_time: Optional[int] = None,
) -> int:
    if publish_time is None:
        publish_time = int(time.time() * 1000)
    conn = GCE_get_connection(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO predictions (agent_id, event_timestamp, predicted_value,
               confidence, publish_time)
               VALUES (?, ?, ?, ?, ?)""",
            (agent_id, event_timestamp, predicted_value, confidence, publish_time),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def GCE_get_unprocessed_predictions(db_path: str) -> List[Dict[str, Any]]:
    conn = GCE_get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE processed = 0 AND real_value IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_mark_prediction_processed(
    db_path: str, prediction_id: int, accuracy: float
) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            "UPDATE predictions SET processed = 1, accuracy = ? WHERE id = ?",
            (accuracy, prediction_id),
        )
        conn.commit()
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_update_prediction_real_value(
    db_path: str, event_timestamp: int, real_value: float
) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            "UPDATE predictions SET real_value = ? WHERE event_timestamp = ? AND processed = 0",
            (real_value, event_timestamp),
        )
        conn.commit()
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_insert_event(
    db_path: str,
    source_id: str,
    event_type: str,
    timestamp: int,
    value: Optional[float] = None,
    text: Optional[str] = None,
) -> None:
    conn = GCE_get_connection(db_path)
    try:
        conn.execute(
            """INSERT OR IGNORE INTO raw_events (source_id, event_type, value, text, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (source_id, event_type, value, text, timestamp),
        )
        conn.commit()
    finally:
        conn.close()


def GCE_get_recent_events(db_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    conn = GCE_get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM raw_events ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def GCE_get_latest_event_timestamp(db_path: str) -> Optional[int]:
    conn = GCE_get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT MAX(timestamp) as ts FROM raw_events"
        ).fetchone()
        return row["ts"] if row else None
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_delete_old_predictions(db_path: str, before_timestamp: int) -> int:
    conn = GCE_get_connection(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM predictions WHERE publish_time < ? AND processed = 1",
            (before_timestamp,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_delete_old_events(db_path: str, before_timestamp: int) -> int:
    conn = GCE_get_connection(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM raw_events WHERE timestamp < ?",
            (before_timestamp,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


@GCE_retry_on_lock(max_retries=5, base_delay=0.01)
def GCE_bulk_insert_predictions(
    db_path: str, rows: List[Tuple[str, int, float, float, int]]
) -> None:
    """批量插入预测记录. 每条元组: (agent_id, event_timestamp, value, confidence, publish_time). / Batch insert predictions. Each tuple: (agent_id, event_timestamp, value, confidence, publish_time)."""
    conn = GCE_get_connection(db_path)
    try:
        conn.executemany(
            """INSERT INTO predictions (agent_id, event_timestamp, predicted_value,
               confidence, publish_time) VALUES (?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
