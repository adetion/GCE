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

"""数据访问层 CRUD 操作测试 / Data access layer CRUD operation tests."""

from __future__ import annotations

import os
import tempfile
import time

import pytest

from gce.storage.GCE_database import GCE_get_connection, GCE_init_db
from gce.storage.GCE_repository import (
    GCE_get_active_agents,
    GCE_get_agent_count,
    GCE_get_agent_energy,
    GCE_get_agent_gene_blob,
    GCE_get_agents_above_energy,
    GCE_get_agents_below_energy,
    GCE_get_elite_agents,
    GCE_insert_agent,
    GCE_insert_prediction,
    GCE_set_agent_status,
    GCE_update_energy,
    GCE_update_prediction_real_value,
)


def GCE__make_temp_db() -> str:
    """Create a temporary directory, initialize the DB, and return the db path."""
    tmpdir = tempfile.mkdtemp(prefix="gce_test_repo_")
    db_path = os.path.join(tmpdir, "repo.db")
    GCE_init_db(db_path)
    return db_path


def GCE__cleanup_db(db_path: str) -> None:
    """Remove the temporary directory containing the database."""
    tmpdir = os.path.dirname(db_path)
    if os.path.isdir(tmpdir):
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmpdir)


def GCE__dummy_blob() -> bytes:
    """Return a dummy gene BLOB for testing."""
    return b"test_gene_blob_data"


def GCE__now_ms() -> int:
    """Return current time in milliseconds."""
    return int(time.time() * 1000)


class GCE_TestInsertAgent:

    def GCE_test_insert_agent_creates_row(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "agent-1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute("SELECT * FROM agents WHERE id = ?", ("agent-1",)).fetchone()
                assert row is not None
                assert row["id"] == "agent-1"
                assert row["energy"] == pytest.approx(100.0)
                assert row["status"] == "active"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_insert_agent_with_parent_and_generation(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(
                db_path, "agent-2", GCE__dummy_blob(), 50.0, GCE__now_ms(),
                parent_id="agent-1", generation=3,
            )
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute("SELECT * FROM agents WHERE id = ?", ("agent-2",)).fetchone()
                assert row is not None
                assert row["parent_id"] == "agent-1"
                assert row["generation"] == 3
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_insert_agent_replace_existing(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "agent-3", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_insert_agent(db_path, "agent-3", b"updated_blob", 200.0, GCE__now_ms())
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute("SELECT * FROM agents WHERE id = ?", ("agent-3",)).fetchone()
                assert row is not None
                assert row["energy"] == pytest.approx(200.0)
                assert row["gene_blob"] == b"updated_blob"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestAgentCount:

    def GCE_test_get_agent_count_zero(self):
        db_path = GCE__make_temp_db()
        try:
            count = GCE_get_agent_count(db_path)
            assert count == 0
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agent_count_one(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "a1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            count = GCE_get_agent_count(db_path)
            assert count == 1
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agent_count_many(self):
        db_path = GCE__make_temp_db()
        try:
            for i in range(5):
                GCE_insert_agent(db_path, f"a{i}", GCE__dummy_blob(), 100.0, GCE__now_ms())
            count = GCE_get_agent_count(db_path)
            assert count == 5
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agent_count_excludes_dead(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "a1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_insert_agent(db_path, "a2", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_set_agent_status(db_path, "a2", "dead")
            count = GCE_get_agent_count(db_path)
            assert count == 1  # only a1 is active
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestActiveAgents:

    def GCE_test_get_active_agents_returns_active_only(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "active-1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_insert_agent(db_path, "active-2", GCE__dummy_blob(), 200.0, GCE__now_ms())
            GCE_insert_agent(db_path, "dead-1", GCE__dummy_blob(), 50.0, GCE__now_ms())
            GCE_set_agent_status(db_path, "dead-1", "dead")
            active = GCE_get_active_agents(db_path)
            active_ids = {a["id"] for a in active}
            assert active_ids == {"active-1", "active-2"}
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_active_agents_empty(self):
        db_path = GCE__make_temp_db()
        try:
            active = GCE_get_active_agents(db_path)
            assert active == []
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestAgentEnergy:

    def GCE_test_get_agent_energy_returns_correct_value(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "e1", GCE__dummy_blob(), 150.0, GCE__now_ms())
            energy = GCE_get_agent_energy(db_path, "e1")
            assert energy == pytest.approx(150.0)
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agent_energy_nonexistent_returns_zero(self):
        db_path = GCE__make_temp_db()
        try:
            energy = GCE_get_agent_energy(db_path, "no-such-agent")
            assert energy == 0.0
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_update_energy_adds_reward(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "e2", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_update_energy(db_path, "e2", 25.0)
            energy = GCE_get_agent_energy(db_path, "e2")
            assert energy == pytest.approx(125.0)
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_update_energy_negative_reward(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "e3", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_update_energy(db_path, "e3", -30.0)
            energy = GCE_get_agent_energy(db_path, "e3")
            assert energy == pytest.approx(70.0)
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestEnergyThresholds:

    def GCE_test_get_agents_above_energy(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "high-1", GCE__dummy_blob(), 300.0, GCE__now_ms())
            GCE_insert_agent(db_path, "high-2", GCE__dummy_blob(), 250.0, GCE__now_ms())
            GCE_insert_agent(db_path, "low-1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            high = GCE_get_agents_above_energy(db_path, 200.0)
            high_ids = {a["id"] for a in high}
            assert high_ids == {"high-1", "high-2"}
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agents_above_energy_includes_exact_threshold(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "exact", GCE__dummy_blob(), 200.0, GCE__now_ms())
            high = GCE_get_agents_above_energy(db_path, 200.0)
            assert len(high) == 1
            assert high[0]["id"] == "exact"
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agents_below_energy(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "high-1", GCE__dummy_blob(), 300.0, GCE__now_ms())
            GCE_insert_agent(db_path, "low-1", GCE__dummy_blob(), 50.0, GCE__now_ms())
            GCE_insert_agent(db_path, "low-2", GCE__dummy_blob(), 10.0, GCE__now_ms())
            low = GCE_get_agents_below_energy(db_path, 100.0)
            low_ids = {a["id"] for a in low}
            assert low_ids == {"low-1", "low-2"}
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agents_below_energy_includes_exact_threshold(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "exact", GCE__dummy_blob(), 50.0, GCE__now_ms())
            low = GCE_get_agents_below_energy(db_path, 50.0)
            assert len(low) == 1
            assert low[0]["id"] == "exact"
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestAgentStatus:

    def GCE_test_set_agent_status_changes_status(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "s1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_set_agent_status(db_path, "s1", "dead")
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute("SELECT status FROM agents WHERE id = ?", ("s1",)).fetchone()
                assert row is not None
                assert row["status"] == "dead"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_set_agent_status_paused(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "s2", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_set_agent_status(db_path, "s2", "paused")
            # Paused agents are not active, so active count should be 0
            count = GCE_get_agent_count(db_path)
            assert count == 0
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_set_agent_status_reactivate(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "s3", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_set_agent_status(db_path, "s3", "dead")
            GCE_set_agent_status(db_path, "s3", "active")
            count = GCE_get_agent_count(db_path)
            assert count == 1
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestPredictions:

    def GCE_test_insert_prediction_adds_record(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "p-agent", GCE__dummy_blob(), 100.0, GCE__now_ms())
            ts = GCE__now_ms()
            pred_id = GCE_insert_prediction(db_path, "p-agent", ts, 42.5)
            assert pred_id > 0
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT * FROM predictions WHERE id = ?", (pred_id,)
                ).fetchone()
                assert row is not None
                assert row["agent_id"] == "p-agent"
                assert row["predicted_value"] == pytest.approx(42.5)
                assert row["confidence"] == pytest.approx(1.0)
                assert row["processed"] == 0
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_insert_prediction_with_custom_confidence(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "p-agent2", GCE__dummy_blob(), 100.0, GCE__now_ms())
            ts = GCE__now_ms()
            pred_id = GCE_insert_prediction(db_path, "p-agent2", ts, 99.9, confidence=0.85)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT confidence FROM predictions WHERE id = ?", (pred_id,)
                ).fetchone()
                assert row is not None
                assert row["confidence"] == pytest.approx(0.85)
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_update_prediction_real_value(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "p-agent3", GCE__dummy_blob(), 100.0, GCE__now_ms())
            ts = GCE__now_ms()
            GCE_insert_prediction(db_path, "p-agent3", ts, 50.0)
            GCE_update_prediction_real_value(db_path, ts, 55.0)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT real_value FROM predictions WHERE event_timestamp = ?",
                    (ts,),
                ).fetchone()
                assert row is not None
                assert row["real_value"] == pytest.approx(55.0)
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestGeneBlob:

    def GCE_test_get_agent_gene_blob_returns_blob(self):
        db_path = GCE__make_temp_db()
        try:
            blob = b"special_gene_data\x00\xff"
            GCE_insert_agent(db_path, "g1", blob, 100.0, GCE__now_ms())
            result = GCE_get_agent_gene_blob(db_path, "g1")
            assert result == blob
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_agent_gene_blob_nonexistent_returns_none(self):
        db_path = GCE__make_temp_db()
        try:
            result = GCE_get_agent_gene_blob(db_path, "no-agent")
            assert result is None
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestEliteAgents:

    def GCE_test_get_elite_agents_returns_top_n(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "elite-1", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_insert_agent(db_path, "elite-2", GCE__dummy_blob(), 500.0, GCE__now_ms())
            GCE_insert_agent(db_path, "elite-3", GCE__dummy_blob(), 300.0, GCE__now_ms())
            GCE_insert_agent(db_path, "elite-4", GCE__dummy_blob(), 50.0, GCE__now_ms())
            elite = GCE_get_elite_agents(db_path, 2)
            assert len(elite) == 2
            # Top 2 should be elite-2 (500) and elite-3 (300), in descending order
            assert elite[0]["id"] == "elite-2"
            assert elite[0]["energy"] == pytest.approx(500.0)
            assert elite[1]["id"] == "elite-3"
            assert elite[1]["energy"] == pytest.approx(300.0)
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_elite_agents_excludes_dead(self):
        db_path = GCE__make_temp_db()
        try:
            GCE_insert_agent(db_path, "elite-dead", GCE__dummy_blob(), 999.0, GCE__now_ms())
            GCE_insert_agent(db_path, "elive-alive", GCE__dummy_blob(), 100.0, GCE__now_ms())
            GCE_set_agent_status(db_path, "elite-dead", "dead")
            elite = GCE_get_elite_agents(db_path, 5)
            elite_ids = {a["id"] for a in elite}
            assert "elite-dead" not in elite_ids
            assert "elive-alive" in elite_ids
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_elite_agents_empty_db(self):
        db_path = GCE__make_temp_db()
        try:
            elite = GCE_get_elite_agents(db_path, 10)
            assert elite == []
        finally:
            GCE__cleanup_db(db_path)
