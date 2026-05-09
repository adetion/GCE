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

"""数据库初始化与连接管理测试 / Database initialization and connection management tests."""

from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest

from gce.storage.GCE_database import (
    GCE_get_connection,
    GCE_get_schema_version,
    GCE_init_db,
    GCE_migrate_db,
    SCHEMA_VERSION,
)

# Expected tables after initialization
EXPECTED_TABLES = {"agents", "predictions", "raw_events", "config"}


def GCE__temp_db_path() -> str:
    """Create a temporary directory and return a db path inside it."""
    tmpdir = tempfile.mkdtemp(prefix="gce_test_db_")
    return os.path.join(tmpdir, "test.db")


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


class GCE_TestDatabaseInit:

    def GCE_test_init_db_creates_tables_without_error(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)  # should not raise
            conn = GCE_get_connection(db_path)
            try:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                table_names = {row["name"] for row in tables}
                for expected in EXPECTED_TABLES:
                    assert expected in table_names, (
                        f"Table '{expected}' not found after GCE_init_db"
                    )
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_init_db_is_idempotent(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            GCE_init_db(db_path)  # second call should not raise
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestDatabaseConnection:

    def GCE_test_get_connection_returns_sqlite3_connection(self):
        db_path = GCE__temp_db_path()
        try:
            conn = GCE_get_connection(db_path)
            try:
                assert isinstance(conn, sqlite3.Connection)
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_connection_creates_parent_dirs(self):
        import shutil
        tmpdir = tempfile.mkdtemp(prefix="gce_test_db_")
        db_path = os.path.join(tmpdir, "sub", "nested", "test.db")
        try:
            conn = GCE_get_connection(db_path)
            conn.close()
            assert os.path.isfile(db_path)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def GCE_test_get_connection_wal_mode_enabled(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute("PRAGMA journal_mode").fetchone()
                assert row is not None
                # WAL mode should be enabled
                assert row[0].upper() == "WAL", (
                    f"Expected WAL mode, got {row[0]}"
                )
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_foreign_keys_pragma_on(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute("PRAGMA foreign_keys").fetchone()
                assert row is not None
                assert row[0] == 1, (
                    f"Expected foreign_keys ON, got {row[0]}"
                )
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestSchemaVersion:

    def GCE_test_get_schema_version_empty_db_returns_zero(self):
        db_path = GCE__temp_db_path()
        try:
            conn = GCE_get_connection(db_path)
            try:
                # Manually create only the config table so the query works
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)"
                )
                conn.commit()
                version = GCE_get_schema_version(conn)
                assert version == 0
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_get_schema_version_after_init(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                version = GCE_get_schema_version(conn)
                assert version == SCHEMA_VERSION
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestTablesExist:

    def GCE_test_agents_table_exists(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'"
                ).fetchone()
                assert row is not None, "agents table does not exist"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_predictions_table_exists(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'"
                ).fetchone()
                assert row is not None, "predictions table does not exist"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_raw_events_table_exists(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='raw_events'"
                ).fetchone()
                assert row is not None, "raw_events table does not exist"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_config_table_exists(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='config'"
                ).fetchone()
                assert row is not None, "config table does not exist"
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)


class GCE_TestMigration:

    def GCE_test_migrate_db_handles_fresh_db(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            GCE_migrate_db(db_path)  # should not raise
        finally:
            GCE__cleanup_db(db_path)

    def GCE_test_migrate_db_sets_schema_version(self):
        db_path = GCE__temp_db_path()
        try:
            GCE_init_db(db_path)
            GCE_migrate_db(db_path)
            conn = GCE_get_connection(db_path)
            try:
                version = GCE_get_schema_version(conn)
                assert version == SCHEMA_VERSION
            finally:
                conn.close()
        finally:
            GCE__cleanup_db(db_path)
