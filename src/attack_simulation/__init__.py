# -*- coding: utf-8 -*-
"""
Attack simulation module.
攻击模拟模块

This module provides tools for simulating attacks and recovery
on energy networks using bootstrap methods.

Submodules:
    simulator: Core attack-recovery simulation logic
    parallel_processes: Parallel processing for large-scale simulations

Classes:
    AttackRecoverySimulator: Simulate random attack and recovery
    ParallelProcessSimulator: Run simulations in parallel

Example:
    >>> from src.attack_simulation import AttackRecoverySimulator
    >>> simulator = AttackRecoverySimulator(drop_ratio=0.3, seed=42)
    >>> _, attack_flows, recovery_flows = simulator.simulate(G)
"""

from .simulator import (
    AttackRecoverySimulator,
    calculate_max_step_for_networks,
    simulate_single_network
)
from .parallel_processes import (
    ParallelProcessSimulator,
    run_parallel_attack_recovery
)

__all__ = [
    'AttackRecoverySimulator',
    'calculate_max_step_for_networks',
    'simulate_single_network',
    'ParallelProcessSimulator',
    'run_parallel_attack_recovery'
]

__version__ = '0.1.0'
