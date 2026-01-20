# -*- coding: utf-8 -*-
"""
Network Complexity Index (NCI) calculation module.
网络复杂指数计算模块

This module provides functionality for computing the Network Complexity Index (NCI)
using the entropy weight-TOPSIS method.

The NCI is based on the following network indicators:
1. Number of nodes
2. Number of edges
3. Average (unweighted) degree
4. Average weighted degree
"""

from typing import Dict, List, Tuple, Optional
import networkx as nx
import pandas as pd
import numpy as np


class NCIIndexCalculator:
    """
    Calculator for Network Complexity Index (NCI).

    This class computes NCI using the entropy weight-TOPSIS method:
    1. Normalize indicators
    2. Calculate entropy values
    3. Calculate weights
    4. Determine ideal and negative ideal solutions
    5. Calculate distances and compute NCI

    Attributes:
        indicators (List[str]): List of indicator names.

    Example:
        >>> calculator = NCIIndexCalculator()
        >>> results = calculator.compute_NCI_for_all_networks(all_networks)
        >>> df = results['summary']
    """

    # Default indicators for NCI calculation
    DEFAULT_INDICATORS = [
        'Number of Nodes',
        'Number of Edges',
        'Average Degree',
        'Average Weighted Degree'
    ]

    def __init__(self, indicators: Optional[List[str]] = None):
        """
        Initialize the NCI calculator.

        Args:
            indicators: List of indicator names. If None, uses defaults.
        """
        self.indicators = indicators or self.DEFAULT_INDICATORS

    def compute_network_metrics(self, G: nx.DiGraph) -> Dict[str, float]:
        """
        Compute basic network metrics.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary with metric names and values.
        """
        # Remove isolated nodes for analysis
        G_analysis = G.copy()
        isolated_nodes = list(nx.isolates(G_analysis))
        G_analysis.remove_nodes_from(isolated_nodes)

        num_nodes = G_analysis.number_of_nodes()
        num_edges = G_analysis.number_of_edges()

        # Calculate average (unweighted) degree
        if num_nodes > 0:
            avg_degree = sum(dict(G_analysis.degree()).values()) / num_nodes
        else:
            avg_degree = 0

        # Calculate average weighted degree
        if num_nodes > 0:
            avg_weighted_degree = sum(
                dict(G_analysis.degree(weight='weight')).values()
            ) / num_nodes
        else:
            avg_weighted_degree = 0

        return {
            'Number of Nodes': num_nodes,
            'Number of Edges': num_edges,
            'Average Degree': avg_degree,
            'Average Weighted Degree': avg_weighted_degree
        }

    def normalize_indicators(self, indicators: np.ndarray) -> np.ndarray:
        """
        Normalize indicators to [0, 1] range.

        Args:
            indicators: 2D numpy array of indicators (n_samples, n_indicators).

        Returns:
            Normalized indicators array.
        """
        min_vals = indicators.min(axis=0)
        ranges = indicators.ptp(axis=0)  # ptp = max - min

        # Avoid division by zero
        ranges[ranges == 0] = 1

        norm_indicators = (indicators - min_vals) / ranges
        return norm_indicators

    def calculate_entropy_weights(self, norm_indicators: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Calculate entropy-based weights for indicators.

        Args:
            norm_indicators: Normalized indicators array.

        Returns:
            Tuple of (weights array, weights dict with indicator names).
        """
        # Avoid log(0) issues
        norm_indicators = np.clip(norm_indicators, 1e-10, 1)

        # Calculate proportion of each indicator across samples
        proportion = norm_indicators / norm_indicators.sum(axis=0, keepdims=True)

        # Calculate information entropy
        k = 1 / np.log(len(norm_indicators))
        entropy = -k * (proportion * np.log(proportion)).sum(axis=0)

        # Calculate weights
        degree_of_diversity = 1 - entropy
        weights = degree_of_diversity / degree_of_diversity.sum()

        # Create dictionary with indicator names
        weights_dict = {
            self.indicators[i]: weights[i]
            for i in range(len(self.indicators))
        }

        return weights, weights_dict

    def calculate_NCI(self, indicators: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Calculate NCI using entropy weight-TOPSIS method.

        Args:
            indicators: 2D numpy array of indicators (n_samples, n_indicators).

        Returns:
            Tuple of (NCI values array, weights dict).
        """
        # Step 1: Normalize indicators
        norm_indicators = self.normalize_indicators(indicators)

        # Step 2: Calculate weights
        weights, weights_dict = self.calculate_entropy_weights(norm_indicators)

        # Step 3: Weighted normalized indicators
        weighted_norm_indicators = norm_indicators * weights

        # Step 4: Determine ideal and negative ideal solutions
        ideal_solution = weighted_norm_indicators.max(axis=0)
        negative_ideal_solution = weighted_norm_indicators.min(axis=0)

        # Step 5: Calculate distances to ideal and negative ideal
        distance_to_ideal = np.sqrt(
            ((weighted_norm_indicators - ideal_solution) ** 2).sum(axis=1)
        )
        distance_to_negative_ideal = np.sqrt(
            ((weighted_norm_indicators - negative_ideal_solution) ** 2).sum(axis=1)
        )

        # Step 6: Calculate NCI
        NCI = distance_to_negative_ideal / (
            distance_to_ideal + distance_to_negative_ideal
        )

        return NCI, weights_dict

    def compute_NCI_for_all_networks(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        verbose: bool = False
    ) -> Dict[str, any]:
        """
        Compute NCI for all networks.

        Args:
            all_networks: Nested dictionary structure:
                {grid_name: {year: {region: G}}}
            verbose: Whether to print progress information.

        Returns:
            Dictionary with:
                - 'summary': DataFrame with all metrics and NCI
                - 'weights': Dictionary of indicator weights
                - 'nci_values': Series of NCI values
        """
        data = []

        total_networks = sum(
            len(years)
            for years in all_networks.values()
        )
        processed = 0

        # Collect metrics for all networks
        for grid_name, years_data in all_networks.items():
            for year, regions_data in years_data.items():
                for region, G in regions_data.items():
                    processed += 1
                    if verbose and processed % 100 == 0:
                        print(f"  Processed {processed}/{total_networks} networks...")

                    # Compute network metrics
                    metrics = self.compute_network_metrics(G)

                    # Record data
                    data.append([
                        year, region,
                        metrics['Number of Nodes'],
                        metrics['Number of Edges'],
                        metrics['Average Degree'],
                        metrics['Average Weighted Degree']
                    ])

        # Create DataFrame
        df = pd.DataFrame(
            data,
            columns=[
                'Year', 'Region',
                'Number of Nodes',
                'Number of Edges',
                'Average Degree',
                'Average Weighted Degree'
            ]
        )

        # Extract indicator values
        indicators = df[self.indicators].values

        # Calculate NCI
        NCI_values, weights_dict = self.calculate_NCI(indicators)

        # Add NCI to DataFrame
        df['NCI'] = NCI_values

        # Add weights to DataFrame
        for indicator in self.indicators:
            df[f'{indicator} Weight'] = weights_dict[indicator]

        return {
            'summary': df,
            'weights': weights_dict,
            'nci_values': NCI_values
        }

    def compute_NCI_for_single_year(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        year: int,
        verbose: bool = False
    ) -> Dict[str, any]:
        """
        Compute NCI for networks of a specific year.

        Args:
            all_networks: Nested dictionary structure.
            year: Year to analyze.
            verbose: Whether to print progress information.

        Returns:
            Dictionary with 'summary', 'weights', 'nci_values'.
        """
        # Filter networks by year
        year_networks = {}
        for grid_name, years_data in all_networks.items():
            if year in years_data:
                year_networks[grid_name] = {year: years_data[year]}

        return self.compute_NCI_for_all_networks(year_networks, verbose)


def calculate_NCI_for_dataframe(
    df: pd.DataFrame,
    indicator_columns: List[str],
    nci_column: str = 'NCI'
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate NCI from a DataFrame of indicators.

    This is a convenience function for calculating NCI when you already
    have indicator data in a DataFrame.

    Args:
        df: DataFrame containing indicator columns.
        indicator_columns: List of column names for indicators.
        nci_column: Name for the NCI output column.

    Returns:
        Tuple of (DataFrame with NCI column, weights dict).

    Example:
        >>> df = pd.DataFrame({
        ...     'nodes': [10, 20, 30],
        ...     'edges': [15, 25, 40],
        ...     'degree': [3.0, 2.5, 2.67]
        ... })
        >>> df, weights = calculate_NCI_for_dataframe(
        ...     df,
        ...     indicator_columns=['nodes', 'edges', 'degree']
        ... )
    """
    calculator = NCIIndexCalculator(indicator_columns)
    indicators = df[indicator_columns].values
    NCI_values, weights_dict = calculator.calculate_NCI(indicators)

    df[nci_column] = NCI_values

    # Add weights as new columns
    for indicator, weight in weights_dict.items():
        df[f'{indicator} Weight'] = weight

    return df, weights_dict
