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

"""基因序列化与验证测试."""

from __future__ import annotations

import pytest

from gce.core.GCE_gene import (
    GCE_Gene,
    GCE_Node,
    GCE_NodeType,
    GCE_count_nodes,
    GCE_deserialize_gene,
    GCE_serialize_gene,
    GCE_tree_depth,
    GCE_validate_tree,
)


def GCE__make_terminal(index: int | None = None, const: float | None = None) -> GCE_Node:
    return GCE_Node(type=GCE_NodeType.TERMINAL, index=index, const=const)


def GCE__make_func(op: str, *children: GCE_Node) -> GCE_Node:
    return GCE_Node(type=GCE_NodeType.FUNCTION, op=op, children=list(children))


class GCE_TestNodeSerialization:
    def GCE_test_terminal_roundtrip(self):
        node = GCE__make_terminal(index=5)
        data = node.GCE_to_dict()
        restored = GCE_Node.GCE_from_dict(data)
        assert restored.type == GCE_NodeType.TERMINAL
        assert restored.index == 5

    def GCE_test_function_roundtrip(self):
        node = GCE__make_func("add", GCE__make_terminal(index=0), GCE__make_terminal(const=3.14))
        data = node.GCE_to_dict()
        restored = GCE_Node.GCE_from_dict(data)
        assert restored.type == GCE_NodeType.FUNCTION
        assert restored.op == "add"
        assert len(restored.children) == 2
        assert restored.children[0].index == 0
        assert restored.children[1].const == pytest.approx(3.14)

    def GCE_test_gene_blob_roundtrip(self):
        gene = GCE_Gene(mask=0b101, tree=GCE__make_terminal(index=0), mutation_rate=0.2)
        blob = GCE_serialize_gene(gene)
        restored = GCE_deserialize_gene(blob)
        assert restored.mask == 0b101
        assert restored.mutation_rate == pytest.approx(0.2)
        assert restored.tree.index == 0


class GCE_TestTreeValidation:
    def GCE_test_count_nodes(self):
        tree = GCE__make_func("add", GCE__make_terminal(index=0), GCE__make_terminal(index=1))
        assert GCE_count_nodes(tree) == 3

    def GCE_test_tree_depth_simple(self):
        tree = GCE__make_terminal(index=0)
        assert GCE_tree_depth(tree) == 1

    def GCE_test_tree_depth_nested(self):
        tree = GCE__make_func("sin", GCE__make_func("abs", GCE__make_terminal(index=0)))
        assert GCE_tree_depth(tree) == 3

    def GCE_test_validate_tree_ok(self):
        tree = GCE__make_func("add", GCE__make_terminal(0), GCE__make_terminal(1))
        assert GCE_validate_tree(tree, max_depth=8, min_nodes=3, max_nodes=50)

    def GCE_test_validate_tree_too_deep(self):
        # depth 4 but max_depth 2
        tree = GCE__make_func("sin", GCE__make_func("abs", GCE__make_func("sin", GCE__make_terminal(0))))
        assert not GCE_validate_tree(tree, max_depth=2)

    def GCE_test_validate_tree_too_few_nodes(self):
        tree = GCE__make_terminal(index=0)
        assert not GCE_validate_tree(tree, max_depth=8, min_nodes=3)

    def GCE_test_validate_tree_too_many_nodes(self):
        # Build a chain of 52 nodes
        tree = GCE__make_terminal(const=0)
        for _ in range(51):
            tree = GCE__make_func("abs", tree)
        assert GCE_count_nodes(tree) >= 52
        assert not GCE_validate_tree(tree, max_depth=60, max_nodes=50)
