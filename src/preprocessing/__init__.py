# -*- coding: utf-8 -*-
"""
Preprocessing module for energy network data.
网络数据预处理模块

This module provides tools for loading, fixing, and preprocessing
energy network data for resilience analysis.

Submodules:
    config_loader: Configuration management utilities
    network_fix: Network data correction and fixing
    network_builder: Network loading and construction
    interprovincial_flows: Interprovincial flow analysis

Classes:
    ConfigLoader: Load and manage project configuration
    NetworkFixer: Fix unit conversion errors in network data
    NetworkBuilder: Build and manage energy network graphs
    NetworkStats: Compute network statistics
    InterprovincialFlowAnalyzer: Analyze interprovincial energy flows
"""

from .config_loader import ConfigLoader, get_config
from .network_fix import NetworkFixer
from .network_builder import NetworkBuilder, NetworkStats
from .interprovincial_flows import InterprovincialFlowAnalyzer

__all__ = [
    'ConfigLoader',
    'get_config',
    'NetworkFixer',
    'NetworkBuilder',
    'NetworkStats',
    'InterprovincialFlowAnalyzer'
]

__version__ = '0.1.0'
