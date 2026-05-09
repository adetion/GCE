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

"""预测器 —— 表达式树求值 / Predictor -- expression tree evaluation."""

from __future__ import annotations

import logging
import math
from typing import List, Optional, Tuple

from gce.core.GCE_gene import GCE_Node, GCE_NodeType
from gce.core.GCE_functions import GCE_call_function

logger = logging.getLogger("gce.core.GCE_predictor")


class GCE_Predictor:
    """在特征向量上评估基因的表达式树 / Evaluates a gene's expression tree on a feature vector."""

    def __init__(self, tree: GCE_Node) -> None:
        self.tree = tree

    def GCE_predict(self, features: List[float]) -> Optional[Tuple[float, float]]:
        """评估表达式树 / Evaluate the expression tree.

        返回 (预测值, 置信度)，如果评估失败则返回 None。此实现中置信度始终为 1.0（为未来使用预留） /
        Returns (prediction, confidence) or None if evaluation fails.
        Confidence is always 1.0 in this implementation (placeholder for future use).
        """
        try:
            value = self.GCE__eval_node(self.tree, features)
            if value is None or math.isnan(value) or math.isinf(value):
                return None
            return (value, 1.0)
        except (ValueError, ZeroDivisionError, OverflowError, IndexError, TypeError) as e:
            logger.debug("Prediction evaluation failed: %s", e)
            return None

    def GCE__eval_node(self, node: GCE_Node, features: List[float]) -> Optional[float]:
        """递归评估一个节点 / Recursively evaluate a node."""
        if node.type == GCE_NodeType.TERMINAL:
            if node.index is not None:
                if 0 <= node.index < len(features):
                    return features[node.index]
                return 0.0
            if node.const is not None:
                return node.const
            return 0.0

        if node.type == GCE_NodeType.FUNCTION:
            assert node.children is not None, f"Function node {node.op} has no children"
            args = []
            for child in node.children:
                val = self.GCE__eval_node(child, features)
                if val is None:
                    return None
                args.append(val)

            try:
                return GCE_call_function(node.op, args)
            except (ValueError, OverflowError, ZeroDivisionError):
                return 0.0

        return 0.0
