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

"""
混沌分析 —— 李雅普诺夫指数近似 + 微扰分析. / Chaos analysis — Lyapunov exponent approximation + perturbation analysis.

纯通用算法，不针对任何特定系统. / Purely generic algorithms, not tailored to any specific system.
"""

from __future__ import annotations

import math
from typing import Callable, List


def GCE_estimate_lyapunov(
    trajectory: List[float],
    tau: int = 1,
    dim: int = 3,
) -> float:
    """从标量时间序列估计最大李雅普诺夫指数. / Estimate the largest Lyapunov exponent from a scalar time series.

    使用延迟坐标嵌入和最近邻发散追踪. / Uses delay-coordinate embedding and nearest-neighbor divergence tracking.

    Args:
        trajectory: 标量时间序列. / Scalar time series.
        tau: 嵌入延迟. / Delay for embedding.
        dim: 嵌入维度. / Embedding dimension.

    Returns:
        估计的最大李雅普诺夫指数（正值表示混沌）. / Estimated largest Lyapunov exponent (positive = chaotic).
    """
    n = len(trajectory)
    if n < dim * tau + 10:
        return 0.0

    # 构建延迟嵌入向量 / Build delay embedding vectors
    m = n - (dim - 1) * tau
    vectors: List[List[float]] = []
    for i in range(m):
        vec = [trajectory[i + j * tau] for j in range(dim)]
        vectors.append(vec)

    # 为第一个点找最近邻，追踪发散 / Find nearest neighbor for first point, track divergence
    ref = vectors[0]
    ref_norm = math.sqrt(sum(v * v for v in ref))
    if ref_norm < 1e-10:
        return 0.0

    # 找最近邻（时间上不要 GCE_close 太近，跳过前约 10 个点）/ Find closest neighbor (not too GCE_close in time, skip first ~10 points)
    min_dist = float("inf")
    neighbor_idx = 1
    for i in range(10, m):
        dist = GCE__euclidean_distance(ref, vectors[i])
        if dist < min_dist and dist > 1e-10:
            min_dist = dist
            neighbor_idx = i

    if min_dist >= float("inf") or min_dist <= 1e-10:
        return 0.0

    # 在剩余轨迹上追踪发散 / Track divergence over remaining trajectory
    steps = min(m - neighbor_idx, m - 1) - 1
    if steps < 2:
        return 0.0

    log_divergence_sum = 0.0
    count = 0
    for k in range(1, steps):
        if neighbor_idx + k >= m or 1 + k >= m:
            break
        dist_k = GCE__euclidean_distance(vectors[1 + k], vectors[neighbor_idx + k])
        if dist_k > 1e-10 and min_dist > 1e-10:
            log_divergence_sum += math.log(dist_k / min_dist)
            count += 1

    if count == 0:
        return 0.0

    # 李雅普诺夫指数估计（未按时间步缩放）/ Lyapunov exponent estimate (unscaled by time step)
    return log_divergence_sum / count


def GCE_perturbation_analysis(
    GCE_initial_state: Callable[[], List[float]],
    simulate_fn: Callable[[List[float], int], List[float]],
    epsilon: float = 0.001,
    threshold: float = 0.5,
    steps: int = 30,
) -> List[int]:
    """通过微扰分析寻找分叉候选点. / Find bifurcation candidate points via perturbation analysis.

    对初始状态的每个维度施加微小扰动，重新 GCE_simulate，并找出轨迹发散超过阈值的时间步. / For each dimension of the initial state, apply a small perturbation,
    re-GCE_simulate, and find time steps where trajectory divergence exceeds threshold.

    Args:
        GCE_initial_state: 返回基准初始状态向量的函数. / Function returning the base initial state vector.
        simulate_fn: 函数 (state, steps) -> 轨迹（标量列表）. / Function (state, steps) -> trajectory as list of scalars.
        epsilon: 扰动幅度. / Perturbation magnitude.
        threshold: 分叉检测的发散阈值. / Divergence threshold for bifurcation detection.
        steps: 推演步数. / Number of simulation steps.

    Returns:
        发散超过阈值的时间步索引列表. / List of time step indices where divergence exceeds threshold.
    """
    base_state = GCE_initial_state()
    base_traj = simulate_fn(base_state, steps)

    bifurcation_points: List[int] = []

    for dim in range(len(base_state)):
        perturbed_state = list(base_state)
        perturbed_state[dim] += epsilon
        perturbed_traj = simulate_fn(perturbed_state, steps)

        for t in range(min(len(base_traj), len(perturbed_traj))):
            divergence = abs(perturbed_traj[t] - base_traj[t])
            if divergence > threshold and t not in bifurcation_points:
                bifurcation_points.append(t)

    bifurcation_points.sort()
    return bifurcation_points


def GCE__euclidean_distance(a: List[float], b: List[float]) -> float:
    """计算两个向量之间的欧几里得距离. / Compute Euclidean distance between two vectors."""
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))
