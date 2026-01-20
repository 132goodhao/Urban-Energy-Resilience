# -*- coding: utf-8 -*-
"""
Resilience analysis module.
韧性分析模块

This module provides tools for computing multi-level resilience indicators
for energy systems.

Submodules:
    level1_economy: Level 1 - Economy-based indicators
    level2_population: Level 2 - Population-based indicators
    level3_structure: Level 3 - Structure-based indicators

Classes:
    EconomyResilience: Compute economy-based resilience indicators
    PopulationResilience: Compute population-based resilience indicators
    StructureResilience: Compute structure-based resilience indicators

Example:
    >>> from src.resilience import EconomyResilience, StructureResilience
    >>> econ_calc = EconomyResilience()
    >>> econ_calc.load_data()
    >>> econ_results = econ_calc.compute_all_indicators()
    >>> struct_calc = StructureResilience()
    >>> ci_results = struct_calc.compute_average_CI_for_all_networks(all_networks)
"""

from .level1_economy import EconomyResilience
from .level2_population import PopulationResilience
from .level3_structure import StructureResilience

__all__ = [
    'EconomyResilience',
    'PopulationResilience',
    'StructureResilience'
]

__version__ = '0.1.0'
