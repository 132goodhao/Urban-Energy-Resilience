# -*- coding: utf-8 -*-
"""
Network analysis module.
网络分析模块

This module provides tools for computing network metrics and indices
for energy network analysis.

Submodules:
    ci_calculation: Collective Influence (CI) calculation
    nci_index: Network Complexity Index (NCI) calculation
    metrics: Additional network metrics (centrality, connectivity, etc.)

Classes:
    CICalculator: Compute Collective Influence of nodes
    NCIIndexCalculator: Compute Network Complexity Index
    NetworkMetrics: Compute various network metrics

Example:
    >>> from src.network_analysis import CICalculator, NCIIndexCalculator
    >>> ci_calc = CICalculator()
    >>> nci_calc = NCIIndexCalculator()
    >>> ci_results = ci_calc.compute_all_nodes_CI(G)
    >>> nci_results = nci_calc.compute_NCI_for_all_networks(all_networks)
"""

from .ci_calculation import (
    CICalculator,
    compute_node_strength,
    compute_collective_influence,
    compute_all_nodes_CI
)
from .nci_index import NCIIndexCalculator, calculate_NCI_for_dataframe
from .metrics import NetworkMetrics, compute_network_summary_dataframe

__all__ = [
    'CICalculator',
    'compute_node_strength',
    'compute_collective_influence',
    'compute_all_nodes_CI',
    'NCIIndexCalculator',
    'calculate_NCI_for_dataframe',
    'NetworkMetrics',
    'compute_network_summary_dataframe'
]

__version__ = '0.1.0'
