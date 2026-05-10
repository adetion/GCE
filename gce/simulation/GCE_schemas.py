#
# -*- coding: utf-8 -*-
#
# Gaming Chaos Engine V0.1.0 – A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# Contact:
#   Email: i126@126.com
#   Website: wop.cc
#
# ... (license header identical to all other project files) ...

"""推演层数据结构. / Simulation data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GCE_Participant:
    """推演参与者. / Simulation participant."""

    name: str
    initial_position: float = 0.0
    strategy_hint: str = ""


@dataclass
class GCE_Scenario:
    """推演场景定义. / Simulation scenario definition."""

    participants: List[GCE_Participant]
    initial_prices: List[float]
    time_steps: int = 30
    objective: str = ""
    raw_input: str = ""
    game_type: str = ""
    sentiment_context: Dict[str, Any] = field(default_factory=dict)
    domain_id: str = ""


@dataclass
class GCE_SimulationResult:
    """推演结果. / Simulation result."""

    consensus_trajectory: List[float]
    lyapunov_estimate: float
    bifurcation_points: List[int]
    elite_strategies: Dict[str, Any] = field(default_factory=dict)
    game_type: str = ""
    participant_trajectories: Dict[str, List[float]] = field(default_factory=dict)
    equilibrium_estimate: float = 0.0
    nash_convergence: float = 0.0
    trajectory_volatility: float = 0.0
    key_events: List[Dict[str, Any]] = field(default_factory=list)
    sentiment_impact: Dict[str, Any] = field(default_factory=dict)
