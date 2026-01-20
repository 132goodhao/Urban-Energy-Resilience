# -*- coding: utf-8 -*-
"""
Level 3 Resilience Module: Structure-based indicators.
三级响应（结构）韧性指标模块

This module computes structure-based resilience indicators, including:
1. Average Collective Influence (CI) by node category:
   - Primary Energy nodes
   - Processing nodes
   - Terminal nodes

These indicators measure the structural capacity of the energy network
to maintain functionality under disruptions.
"""

from typing import Dict, List, Optional, Set
import networkx as nx
import pandas as pd
import pickle

from ..preprocessing.config_loader import get_config
from ..network_analysis import CICalculator


class StructureResilience:
    """
    Calculator for Level 3 (Structure-based) resilience indicators.

    This class computes indicators that measure how network structure
    influences energy system resilience through Collective Influence (CI).

    Attributes:
        config (ConfigLoader): Configuration loader instance.
        ci_calculator (CICalculator): CI calculation instance.
        node_categories (Optional[Dict]): Node category mappings.

    Example:
        >>> calc = StructureResilience()
        >>> calc.load_node_categories()
        >>> results = calc.compute_average_CI_for_all_networks(all_networks)
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the StructureResilience calculator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config = get_config(config_path)
        self.ci_calculator = CICalculator()
        self.node_categories: Optional[Dict[str, Set[str]]] = None

    def load_node_categories(self, env_vars_path: Optional[str] = None) -> None:
        """
        Load node categories from env_vars.pkl.

        Args:
            env_vars_path: Path to env_vars.pkl.
        """
        if env_vars_path is None:
            env_vars_path = self.config.get_full_path('env_vars')

        if env_vars_path and env_vars_path.exists():
            with open(env_vars_path, 'rb') as f:
                env_vars = pickle.load(f)

            # Define node categories
            self.node_categories = {
                'Primary Energy': env_vars['primary_energy_nodes'],
                'Processing': env_vars['processing_nodes'],
                'Terminal': env_vars['terminal_nodes']
            }

    def compute_average_CI_by_category(
        self,
        G: nx.DiGraph,
        node_CI: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compute the average CI for each node category.

        Args:
            G: NetworkX directed graph.
            node_CI: Dictionary mapping node names to CI values.

        Returns:
            Dictionary mapping category names to average CI values.
        """
        if self.node_categories is None:
            self.load_node_categories()

        return self.ci_calculator.compute_average_CI_by_category(
            G, node_CI, self.node_categories
        )

    def compute_average_CI_for_all_networks(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        node_categories: Optional[Dict[str, Set[str]]] = None,
        verbose: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Compute the average CI for each category across all networks.

        Args:
            all_networks: Nested dictionary structure:
                {grid_name: {year: {region: G}}}
            node_categories: Optional custom node categories.
            verbose: Whether to print progress information.

        Returns:
            Dictionary with keys 'primary', 'processing', 'terminal',
            each containing a pivot DataFrame with CI values.
        """
        # Use provided categories or load from file
        if node_categories is None:
            if self.node_categories is None:
                self.load_node_categories()
            node_categories = self.node_categories

        return self.ci_calculator.compute_CI_for_all_networks(
            all_networks, node_categories, verbose
        )

    def compute_CI_for_specific_year(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        year: int,
        verbose: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Compute CI for networks of a specific year.

        Args:
            all_networks: Nested dictionary structure.
            year: Year to analyze.
            verbose: Whether to print progress information.

        Returns:
            Dictionary with 'primary', 'processing', 'terminal' DataFrames.
        """
        # Filter networks by year
        year_networks = {}
        for grid_name, years_data in all_networks.items():
            if year in years_data:
                year_networks[grid_name] = {year: years_data[year]}

        return self.compute_average_CI_for_all_networks(
            year_networks, verbose=verbose
        )

    def compute_node_ranking(
        self,
        G: nx.DiGraph,
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        Compute and rank nodes by their CI values.

        Args:
            G: NetworkX directed graph.
            top_n: Number of top nodes to return.

        Returns:
            DataFrame with node rankings.
        """
        node_CI = self.ci_calculator.compute_all_nodes_CI(G)

        # Sort by CI value (descending)
        sorted_nodes = sorted(
            node_CI.items(), key=lambda x: x[1], reverse=True
        )

        # Create DataFrame
        df = pd.DataFrame(
            sorted_nodes[:top_n],
            columns=['node', 'CI']
        )
        df['rank'] = range(1, len(df) + 1)

        # Add category information if available
        if self.node_categories:
            categories = []
            for node in df['node']:
                found = False
                for cat_name, cat_nodes in self.node_categories.items():
                    if node in cat_nodes:
                        categories.append(cat_name)
                        found = True
                        break
                if not found:
                    categories.append('Unknown')
            df['category'] = categories

        return df

    def compute_network_CI_summary(
        self,
        G: nx.DiGraph
    ) -> Dict[str, float]:
        """
        Compute summary statistics of CI values for a network.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary with CI summary statistics.
        """
        node_CI = self.ci_calculator.compute_all_nodes_CI(G)
        ci_values = list(node_CI.values())

        if not ci_values:
            return {}

        import numpy as np

        return {
            'mean_ci': np.mean(ci_values),
            'std_ci': np.std(ci_values),
            'min_ci': np.min(ci_values),
            'max_ci': np.max(ci_values),
            'median_ci': np.median(ci_values),
            'n_nodes': len(ci_values)
        }

    def compute_CI_stats_for_all_networks(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        Compute CI summary statistics for all networks.

        Args:
            all_networks: Nested dictionary structure.
            verbose: Whether to print progress information.

        Returns:
            DataFrame with CI statistics for all networks.
        """
        data = []

        total_networks = sum(
            len(years)
            for years in all_networks.values()
        )
        processed = 0

        for grid_name, years_data in all_networks.items():
            for year, regions_data in years_data.items():
                for region, G in regions_data.items():
                    processed += 1
                    if verbose and processed % 100 == 0:
                        print(f"  Processed {processed}/{total_networks} networks...")

                    # Compute CI summary
                    stats = self.compute_network_CI_summary(G)

                    if stats:
                        row = {
                            'grid': grid_name,
                            'region': region,
                            'year': year
                        }
                        row.update(stats)
                        data.append(row)

        return pd.DataFrame(data)
