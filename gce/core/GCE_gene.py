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

"""基因组与表达式树节点定义 / Gene and expression tree node definitions."""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GCE_NodeType(Enum):
    """节点类型枚举：终结符或函数 / Node type enumeration: terminal or function."""
    TERMINAL = 1
    FUNCTION = 2


@dataclass
class GCE_Node:
    """表达式树节点 / Expression tree node.

    Attributes:
        type: 节点类型（终结符或函数） / Node type (terminal or function).
        op: 函数运算符名称 / Function operator name.
        children: 子节点列表 / List of child nodes.
        index: 特征索引（仅终结符） / Feature index (terminal only).
        const: 常量值（仅终结符） / Constant value (terminal only).
    """
    type: GCE_NodeType
    op: Optional[str] = None
    children: Optional[List[GCE_Node]] = None
    index: Optional[int] = None       # 特征索引（终结符） / Feature index (terminal)
    const: Optional[float] = None     # 常量值（终结符） / Constant value (terminal)

    def GCE_to_dict(self) -> Dict[str, Any]:
        """将节点序列化为字典 / Serialize node to dictionary."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.type == GCE_NodeType.FUNCTION:
            d["op"] = self.op
            d["children"] = [c.GCE_to_dict() for c in (self.children or [])]
        else:
            d["index"] = self.index
            d["const"] = self.const
        return d

    @classmethod
    def GCE_from_dict(cls, d: Dict[str, Any]) -> GCE_Node:
        """从字典反序列化节点 / Deserialize node from dictionary."""
        node_type = GCE_NodeType(d["type"])
        if node_type == GCE_NodeType.FUNCTION:
            return cls(
                type=node_type,
                op=d["op"],
                children=[cls.GCE_from_dict(c) for c in d.get("children", [])],
            )
        else:
            return cls(
                type=node_type,
                index=d.get("index"),
                const=d.get("const"),
            )


@dataclass
class GCE_Gene:
    """基因：特征掩码 + 表达式树 + 变异率 / Gene: feature mask + expression tree + mutation rate.

    Attributes:
        mask: 位掩码，选择哪些特征被使用 / Bitmask selecting which features are used.
        tree: 表达式树的根节点 / Root node of the expression tree.
        mutation_rate: 变异概率 / Mutation probability.
    """
    mask: int
    tree: GCE_Node
    mutation_rate: float = 0.1

    def GCE_to_json(self) -> str:
        """将基因序列化为 JSON 字符串 / Serialize gene to JSON string."""
        return json.dumps({
            "mask": self.mask,
            "tree": self.tree.GCE_to_dict(),
            "mutation_rate": self.mutation_rate,
        })

    @classmethod
    def GCE_from_json(cls, s: str) -> GCE_Gene:
        """从 JSON 字符串反序列化基因 / Deserialize gene from JSON string."""
        d = json.loads(s)
        return cls(
            mask=d["mask"],
            tree=GCE_Node.GCE_from_dict(d["tree"]),
            mutation_rate=d.get("mutation_rate", 0.1),
        )


def GCE_serialize_gene(gene: GCE_Gene) -> bytes:
    """将基因序列化为压缩字节用于 BLOB 存储 / Serialize gene to compressed bytes for BLOB storage."""
    raw = gene.GCE_to_json().encode("utf-8")
    return zlib.compress(raw)


def GCE_deserialize_gene(blob: bytes) -> GCE_Gene:
    """从压缩 BLOB 反序列化基因 / Deserialize gene from compressed BLOB."""
    raw = zlib.decompress(blob)
    return GCE_Gene.GCE_from_json(raw.decode("utf-8"))


def GCE_count_nodes(node: GCE_Node) -> int:
    """统计树中节点总数 / Count total number of nodes in the tree."""
    if node.type == GCE_NodeType.TERMINAL:
        return 1
    return 1 + sum(GCE_count_nodes(c) for c in (node.children or []))


def GCE_tree_depth(node: GCE_Node) -> int:
    """计算树的最大深度 / Calculate maximum depth of the tree."""
    if node.type == GCE_NodeType.TERMINAL:
        return 1
    return 1 + max(GCE_tree_depth(c) for c in (node.children or []))


def GCE_validate_tree(
    node: GCE_Node,
    max_depth: int = 8,
    min_nodes: int = 3,
    max_nodes: int = 50,
) -> bool:
    """检查树是否满足深度和节点数约束 / Check if tree satisfies depth and node count constraints."""
    depth = GCE_tree_depth(node)
    nodes = GCE_count_nodes(node)
    return depth <= max_depth and min_nodes <= nodes <= max_nodes
