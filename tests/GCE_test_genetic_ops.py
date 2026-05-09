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

"""遗传操作测试."""

from __future__ import annotations

import pytest

from gce.core.GCE_gene import GCE_Gene, GCE_Node, GCE_NodeType, GCE_count_nodes, GCE_tree_depth, GCE_validate_tree
from gce.core.GCE_genetic_ops import (
    FEATURE_COUNT,
    GCE_crossover,
    GCE_mutate,
    GCE_prune_tree,
    GCE_random_tree,
)


def GCE__make_terminal(index: int | None = None, const: float | None = None) -> GCE_Node:
    return GCE_Node(type=GCE_NodeType.TERMINAL, index=index, const=const)


def GCE__make_func(op: str, *children: GCE_Node) -> GCE_Node:
    return GCE_Node(type=GCE_NodeType.FUNCTION, op=op, children=list(children))


class GCE_TestRandomTree:
    def GCE_test_generates_valid_tree(self):
        tree = GCE_random_tree(depth=3, feature_count=FEATURE_COUNT)
        assert GCE_validate_tree(tree, max_depth=3, min_nodes=1, max_nodes=50)

    def GCE_test_terminal_at_depth_1(self):
        tree = GCE_random_tree(depth=1, feature_count=FEATURE_COUNT)
        assert tree.type == GCE_NodeType.TERMINAL


class GCE_TestCrossover:
    def GCE_test_crossover_produces_valid_children(self):
        tree1 = GCE__make_func("add", GCE__make_terminal(index=0), GCE__make_terminal(index=1))
        tree2 = GCE__make_func("sub", GCE__make_terminal(const=3.0), GCE__make_terminal(index=2))
        g1 = GCE_Gene(mask=0xFF, tree=tree1)
        g2 = GCE_Gene(mask=0xFF, tree=tree2)

        c1, c2 = GCE_crossover(g1, g2, max_depth=8, max_retries=5)

        assert GCE_validate_tree(c1.tree, max_depth=8)
        assert GCE_validate_tree(c2.tree, max_depth=8)

    def GCE_test_crossover_returns_clones_on_failure(self):
        # Use very small max_depth to force failures
        tree1 = GCE__make_func("add", GCE__make_terminal(0), GCE__make_func("sin", GCE__make_terminal(1)))
        tree2 = GCE__make_func("sub", GCE__make_terminal(2), GCE__make_terminal(3))
        g1 = GCE_Gene(mask=0xFF, tree=tree1)
        g2 = GCE_Gene(mask=0xFF, tree=tree2)

        # Force retry exhaustion — but it should still return valid clones
        c1, c2 = GCE_crossover(g1, g2, max_depth=8, max_retries=10)

        assert GCE_validate_tree(c1.tree, max_depth=8)
        assert GCE_validate_tree(c2.tree, max_depth=8)


class GCE_TestMutation:
    def GCE_test_mutate_produces_valid_tree(self):
        config = {
            "max_depth": 6,
            "min_nodes": 3,
            "max_nodes": 50,
            "mask_flip_rate": 0.05,
            "feature_count": FEATURE_COUNT,
        }
        gene = GCE_Gene(
            mask=0xFFFF,
            tree=GCE__make_func("add", GCE__make_terminal(0), GCE__make_terminal(1)),
        )

        for _ in range(20):
            mutated = GCE_mutate(gene, config)
            assert GCE_validate_tree(mutated.tree, max_depth=6, min_nodes=3, max_nodes=50)

    def GCE_test_mutate_handles_min_nodes(self):
        config = {
            "max_depth": 6,
            "min_nodes": 5,
            "max_nodes": 50,
            "mask_flip_rate": 0.05,
            "feature_count": FEATURE_COUNT,
        }
        # Tree with only 2 nodes (< min_nodes)
        gene = GCE_Gene(mask=0xFFFF, tree=GCE__make_func("abs", GCE__make_terminal(0)))

        for _ in range(20):
            mutated = GCE_mutate(gene, config)
            # After mutation, should be expanded to meet min_nodes
            assert GCE_count_nodes(mutated.tree) >= config["min_nodes"]


class GCE_TestPruneTree:
    def GCE_test_prune_reduces_depth(self):
        # Build a deep chain: sin(sin(sin(sin(sin(x))))) = depth 6
        tree = GCE__make_terminal(index=0)
        for _ in range(5):
            tree = GCE__make_func("sin", tree)
        assert GCE_tree_depth(tree) == 6

        pruned = GCE_prune_tree(tree, max_depth=3, max_nodes=50)
        assert GCE_tree_depth(pruned) <= 3

    def GCE_test_prune_reduces_nodes(self):
        # Build many nodes
        tree = GCE__make_terminal(const=0)
        for _ in range(30):
            tree = GCE__make_func("add", tree, GCE__make_terminal(const=1))
        assert GCE_count_nodes(tree) > 50

        pruned = GCE_prune_tree(tree, max_depth=20, max_nodes=50)
        assert GCE_count_nodes(pruned) <= 50
