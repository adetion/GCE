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

"""遗传操作：交叉、变异、随机树生成、修剪 / Genetic operations: crossover, mutation, random tree generation, pruning."""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from gce.core.GCE_gene import GCE_Gene, GCE_Node, GCE_NodeType, GCE_count_nodes, GCE_tree_depth, GCE_validate_tree
from gce.core.GCE_functions import FUNCTIONS, GCE_get_arity

FEATURE_COUNT = 36  # 特征池中的特征总数 / Total number of features in the feature pool


def GCE_random_terminal(feature_count: int = FEATURE_COUNT) -> GCE_Node:
    """生成随机终结符节点：特征索引或常量 / Generate a random terminal node: either a feature index or a constant."""
    if random.random() < 0.6:
        # 特征引用 / Feature reference
        return GCE_Node(type=GCE_NodeType.TERMINAL, index=random.randrange(feature_count))
    else:
        # 常量，范围 [-5, 5] / Constant in [-5, 5]
        return GCE_Node(type=GCE_NodeType.TERMINAL, const=random.uniform(-5.0, 5.0))


def GCE_random_function() -> str:
    """从函数集中随机选择一个函数名 / Pick a random function name from the function set."""
    return random.choice(list(FUNCTIONS.keys()))


def GCE_random_tree(depth: int, feature_count: int = FEATURE_COUNT) -> GCE_Node:
    """生成随机表达式树 / Generate a random expression tree.

    Args:
        depth: 剩余最大深度 / Maximum remaining depth.
        feature_count: 特征池中的特征数量 / Number of features in the pool.
    """
    if depth <= 1:
        return GCE_random_terminal(feature_count)

    op_name = GCE_random_function()
    arity = GCE_get_arity(op_name)
    children = [GCE_random_tree(depth - 1, feature_count) for _ in range(arity)]
    return GCE_Node(type=GCE_NodeType.FUNCTION, op=op_name, children=children)


def GCE__collect_all_nodes(
    node: GCE_Node,
    parent: Optional[GCE_Node] = None,
    child_index: int = -1,
) -> List[Tuple[GCE_Node, Optional[GCE_Node], int]]:
    """收集所有节点，返回 (节点, 父节点, 在父节点中的子索引) / Collect all nodes as (node, parent, child_index_in_parent). Root has parent=None, index=-1."""
    result: List[Tuple[GCE_Node, Optional[GCE_Node], int]] = []
    result.append((node, parent, child_index))
    if node.type == GCE_NodeType.FUNCTION and node.children:
        for i, child in enumerate(node.children):
            result.extend(GCE__collect_all_nodes(child, node, i))
    return result


def GCE__replace_child(parent: GCE_Node, child_index: int, new_child: GCE_Node) -> None:
    """就地替换一个子节点 / Replace a child node in place."""
    if parent.children is not None:
        parent.children[child_index] = new_child


def GCE_crossover(
    parent1_gene: GCE_Gene,
    parent2_gene: GCE_Gene,
    max_depth: int = 8,
    max_retries: int = 3,
) -> Tuple[GCE_Gene, GCE_Gene]:
    """在两个父代基因之间执行子树交叉 / Perform subtree crossover between two parent genes.

    返回两个子代基因。如果交叉在最大重试次数后仍失败，则返回父代的克隆 /
    Returns two child genes. If crossover fails after max_retries, returns clones of the parents.
    """
    for _ in range(max_retries):
        # 通过序列化往返进行深拷贝 / Deep copy parents (via serialization roundtrip)
        child1 = GCE_Gene.GCE_from_json(parent1_gene.GCE_to_json())
        child2 = GCE_Gene.GCE_from_json(parent2_gene.GCE_to_json())

        nodes1 = GCE__collect_all_nodes(child1.tree)
        nodes2 = GCE__collect_all_nodes(child2.tree)

        if len(nodes1) < 2 and len(nodes2) < 2:
            continue

        # 从每棵树中随机选择节点 / Pick random nodes from each tree
        node1, parent1, idx1 = random.choice(nodes1)
        node2, parent2, idx2 = random.choice(nodes2)

        # 交换子树，对被交换的子树创建深拷贝 / Swap subtrees. Creating deep copies of the swapped subtrees.
        subtree1 = GCE_Node.GCE_from_dict(node1.GCE_to_dict())
        subtree2 = GCE_Node.GCE_from_dict(node2.GCE_to_dict())

        if parent1 is not None:
            GCE__replace_child(parent1, idx1, subtree2)
        else:
            child1.tree = subtree2

        if parent2 is not None:
            GCE__replace_child(parent2, idx2, subtree1)
        else:
            child2.tree = subtree1

        # 验证两个子代 / Validate both children
        if GCE_validate_tree(child1.tree, max_depth) and GCE_validate_tree(child2.tree, max_depth):
            return child1, child2

    # 所有重试都失败了 —— 返回克隆 / All retries failed — return clones
    child1 = GCE_Gene.GCE_from_json(parent1_gene.GCE_to_json())
    child2 = GCE_Gene.GCE_from_json(parent2_gene.GCE_to_json())
    return child1, child2


def GCE_mutate(gene: GCE_Gene, config: Dict) -> GCE_Gene:
    """变异一个基因，均匀选择五种变异类型之一 / Mutate a gene. Uniformly selects one of five mutation types.

    返回变异后的基因（原地修改） / Returns the mutated gene (in-place modification).
    """
    max_depth = config.get("max_depth", 8)
    min_nodes = config.get("min_nodes", 3)
    max_nodes = config.get("max_nodes", 50)
    mask_flip_rate = config.get("mask_flip_rate", 0.05)
    feature_count = config.get("feature_count", FEATURE_COUNT)

    mutation_type = random.choice([
        "terminal", "function", "subtree", "shrink_expand", "mask"
    ])

    if mutation_type == "terminal":
        GCE__mutate_terminal(gene, feature_count)
    elif mutation_type == "function":
        GCE__mutate_function(gene)
    elif mutation_type == "subtree":
        GCE__mutate_subtree(gene, max_depth, feature_count)
    elif mutation_type == "shrink_expand":
        GCE__mutate_shrink_expand(gene, feature_count)
    elif mutation_type == "mask":
        GCE__mutate_mask(gene, mask_flip_rate)

    # 验证并在必要时修剪 / Validate and prune if necessary
    if not GCE_validate_tree(gene.tree, max_depth, min_nodes, max_nodes):
        gene.tree = GCE_prune_tree(gene.tree, max_depth, max_nodes)

    # 如果仍然无效（节点太少），通过添加终结符恢复 / If still invalid (e.g. too few nodes), revert by adding terminals
    while GCE_count_nodes(gene.tree) < min_nodes:
        gene.tree = GCE__expand_tree(gene.tree, feature_count)

    return gene


def GCE__mutate_terminal(gene: GCE_Gene, feature_count: int) -> None:
    """随机改变一个终结符节点：特征索引扰动或常量抖动 / Randomly change a terminal node: feature index perturbation or constant jitter."""
    nodes = GCE__collect_all_nodes(gene.tree)
    terminals = [(n, p, i) for n, p, i in nodes if n.type == GCE_NodeType.TERMINAL]
    if not terminals:
        return
    node, _, _ = random.choice(terminals)
    if node.index is not None and random.random() < 0.5:
        node.index = random.randrange(feature_count)
    elif node.const is not None:
        node.const += random.gauss(0.0, 1.0)


def GCE__mutate_function(gene: GCE_Gene) -> None:
    """随机改变一个函数节点的运算符 / Randomly change a function node's operator."""
    nodes = GCE__collect_all_nodes(gene.tree)
    func_nodes = [(n, p, i) for n, p, i in nodes if n.type == GCE_NodeType.FUNCTION]
    if not func_nodes:
        return
    node, _, _ = random.choice(func_nodes)
    new_op = GCE_random_function()
    old_arity = GCE_get_arity(node.op or "")
    new_arity = GCE_get_arity(new_op)
    if old_arity == new_arity:
        # 相同参数数量 —— 直接交换运算符 / Same arity — just swap operator
        node.op = new_op
    else:
        # 不同参数数量 —— 用新的随机树替换 / Different arity — replace with a fresh random tree
        gene.tree = GCE_random_tree(depth=3, feature_count=FEATURE_COUNT)


def GCE__mutate_subtree(gene: GCE_Gene, max_depth: int, feature_count: int) -> None:
    """用新的随机树替换一个随机子树 / Replace a random subtree with a new random tree."""
    nodes = GCE__collect_all_nodes(gene.tree)
    node, parent, idx = random.choice(nodes)
    new_subtree = GCE_random_tree(depth=random.randint(1, max_depth), feature_count=feature_count)
    if parent is not None:
        GCE__replace_child(parent, idx, new_subtree)
    else:
        gene.tree = new_subtree


def GCE__mutate_shrink_expand(gene: GCE_Gene, feature_count: int) -> None:
    """收缩：删除子树并提升一个子节点。扩展：用一元函数包装终结符 / Shrink: delete a subtree and promote a child. Expand: wrap a terminal with a unary function."""
    nodes = GCE__collect_all_nodes(gene.tree)
    if random.random() < 0.5:
        # 收缩：选择一个函数节点，用其一个子节点替换 / Shrink: pick a function node, replace it with one of its children
        func_nodes = [(n, p, i) for n, p, i in nodes if n.type == GCE_NodeType.FUNCTION and n.children]
        if not func_nodes:
            return
        node, parent, idx = random.choice(func_nodes)
        replacement = random.choice(node.children)  # type: ignore[arg-type]
        if parent is not None:
            GCE__replace_child(parent, idx, replacement)
        else:
            gene.tree = replacement
    else:
        # 扩展：用 abs、sin、cos、exp 或 log 包装终结符 / Expand: wrap a terminal with abs, sin, cos, exp, or log
        terminals = [(n, p, i) for n, p, i in nodes if n.type == GCE_NodeType.TERMINAL]
        if not terminals:
            return
        node, parent, idx = random.choice(terminals)
        unary_op = random.choice(["abs", "sin", "cos", "exp", "log"])
        GCE_wrapper = GCE_Node(type=GCE_NodeType.FUNCTION, op=unary_op, children=[node])
        if parent is not None:
            GCE__replace_child(parent, idx, GCE_wrapper)
        else:
            gene.tree = GCE_wrapper


def GCE__mutate_mask(gene: GCE_Gene, flip_rate: float) -> None:
    """翻转特征掩码中的随机位 / Flip random bits in the feature mask."""
    for bit in range(FEATURE_COUNT):
        if random.random() < flip_rate:
            gene.mask ^= (1 << bit)


def GCE_prune_tree(node: GCE_Node, max_depth: int, max_nodes: int) -> GCE_Node:
    """修剪超出深度或节点数限制的树 / Prune a tree that exceeds depth or node count limits.

    策略：如果深度超过最大深度，用终结符替换最深的子树；如果节点数超过最大节点数，反复替换最深的子树 /
    Strategy: if depth > max_depth, replace deepest subtrees with terminals.
    If node count > max_nodes, repeatedly replace deepest subtrees.
    """
    depth = GCE_tree_depth(node)
    if depth <= max_depth and GCE_count_nodes(node) <= max_nodes:
        return node

    # 如果仍然太深，递归修剪子节点 / If still too deep, recursively prune children
    if depth > max_depth:
        node = GCE__prune_depth(node, max_depth)
    while GCE_count_nodes(node) > max_nodes:
        node = GCE__prune_one_level(node)
    return node


def GCE__prune_depth(node: GCE_Node, max_depth: int, current_depth: int = 1) -> GCE_Node:
    """将超出最大深度的节点替换为随机终结符 / Replace nodes beyond max_depth with random terminals."""
    if current_depth >= max_depth:
        return GCE_random_terminal()
    if node.type == GCE_NodeType.FUNCTION and node.children:
        node.children = [
            GCE__prune_depth(c, max_depth, current_depth + 1) for c in node.children
        ]
    return node


def GCE__prune_one_level(node: GCE_Node) -> GCE_Node:
    """删除最深的子树并用终结符替换 / Remove the deepest subtree and replace with a terminal."""
    nodes = GCE__collect_all_nodes(node)
    # 找到最深的节点 / Find deepest nodes
    deepest = max(nodes, key=lambda x: GCE__node_path_depth(x))
    target, parent, idx = deepest
    if parent is not None:
        GCE__replace_child(parent, idx, GCE_random_terminal())
    else:
        node = GCE_random_terminal()
    return node


def GCE__node_path_depth(item: Tuple[GCE_Node, Optional[GCE_Node], int]) -> int:
    """返回已收集节点的深度（节点字段本身） / Return depth of a collected node (the node field itself)."""
    return GCE_tree_depth(item[0])


def GCE__expand_tree(node: GCE_Node, feature_count: int) -> GCE_Node:
    """用一元函数包装树以增加节点数 / Wrap the tree in a unary function to increase node count."""
    op = random.choice(["abs", "sin", "cos", "exp", "log"])
    return GCE_Node(type=GCE_NodeType.FUNCTION, op=op, children=[node])
