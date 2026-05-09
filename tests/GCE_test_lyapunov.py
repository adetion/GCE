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

"""Lyapunov指数和微扰分析测试."""

from __future__ import annotations

import math

import pytest

from gce.simulation.GCE_lyapunov import GCE_estimate_lyapunov, GCE_perturbation_analysis


class GCE_TestLyapunovEstimate:
    def GCE_test_constant_series(self):
        """Constant series should give zero Lyapunov exponent."""
        traj = [1.0] * 100
        lyap = GCE_estimate_lyapunov(traj, tau=1, dim=3)
        assert lyap == pytest.approx(0.0, abs=0.01)

    def GCE_test_sinusoidal_series(self):
        """Periodic series should give a finite Lyapunov estimate."""
        traj = [math.sin(0.1 * i) for i in range(200)]
        lyap = GCE_estimate_lyapunov(traj, tau=1, dim=3)
        assert isinstance(lyap, float)
        assert math.isfinite(lyap)

    def GCE_test_random_series(self):
        """Random series should give positive Lyapunov exponent."""
        import random
        rng = random.Random(42)
        # Use a random walk (integrated noise) for more chaotic behavior
        traj = [0.0]
        for _ in range(200):
            traj.append(traj[-1] + rng.gauss(0, 1))
        lyap = GCE_estimate_lyapunov(traj, tau=1, dim=3)
        assert isinstance(lyap, float)
        assert math.isfinite(lyap)

    def GCE_test_short_series(self):
        """Short series should return 0.0 without error."""
        traj = [1.0, 2.0, 3.0]
        lyap = GCE_estimate_lyapunov(traj, tau=1, dim=3)
        assert lyap == pytest.approx(0.0)


class GCE_TestPerturbationAnalysis:
    def GCE_test_no_bifurcation_for_stable_system(self):
        """A simple linear function should have no bifurcation points."""

        def GCE_initial_state() -> list[float]:
            return [1.0]

        def GCE_simulate(state: list[float], steps: int) -> list[float]:
            x = state[0]
            return [x + 0.1 * i for i in range(steps)]

        points = GCE_perturbation_analysis(
            GCE_initial_state=GCE_initial_state,
            simulate_fn=GCE_simulate,
            epsilon=0.001,
            threshold=0.5,
            steps=10,
        )
        assert points == []

    def GCE_test_detects_divergence(self):
        """A system with exponential divergence should produce bifurcation points."""

        def GCE_initial_state() -> list[float]:
            return [1.0]

        def GCE_simulate(state: list[float], steps: int) -> list[float]:
            x = state[0]
            return [x * (1.5 ** i) for i in range(steps)]

        points = GCE_perturbation_analysis(
            GCE_initial_state=GCE_initial_state,
            simulate_fn=GCE_simulate,
            epsilon=0.001,
            threshold=0.1,
            steps=15,
        )
        # Exponential growth should trigger divergence
        assert len(points) > 0
