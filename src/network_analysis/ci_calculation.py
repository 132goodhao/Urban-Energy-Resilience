# -*- coding: utf-8 -*-
"""
Collective Influence (CI) calculation module.
集成影响力计算模块

This module provides functions for computing the Collective Influence (CI) of nodes
in energy networks, which measures the strategic importance of nodes based on
their position and connectivity in the network.

The CI calculation considers:
1. Node strength (total flow through the node)
2. Direct neighbors (J1 set)
3. Nodes at distance 2 (J2 set)
4. Nodes at distance 3 (J3 set)
"""

from typing import Dict, List, Set, Optional
import networkx as nx
import pandas as pd
import numpy as np


class CICalculator:
    """
    Calculator for Collective Influence (CI) of nodes in a network.

    This class provides methods to compute the CI of individual nodes
    and all nodes in a network graph.

    Attributes:
        G (nx.DiGraph): The network graph being analyzed.
        node_categories (Dict[str, Set[str]]): Optional node categories for
                                              computing average CI by category.

    Example:
        >>> calculator = CICalculator()
        >>> node_ci = calculator.compute_all_nodes_CI(G)
        >>> avg_ci_by_category = calculator.compute_average_CI_by_category(G, node_ci, categories)
    """

    def __init__(self):
        """Initialize the CI calculator."""
        pass

    def compute_node_strength(self, G: nx.DiGraph, node: str) -> float:
        """
        Calculate the strength (degree) of a node.

        Strength is calculated as the sum of weights of all incoming and outgoing edges.

        Args:
            G: NetworkX directed graph.
            node: Node name.

        Returns:
            Total strength (in_strength + out_strength).
        """
        in_strength = sum(data['weight'] for _, _, data in G.in_edges(node, data=True))
        out_strength = sum(data['weight'] for _, _, data in G.out_edges(node, data=True))
        return in_strength + out_strength

    def find_max_path_weight(self, G: nx.DiGraph, source: str, target: str) -> tuple[float, float]:
        """
        Find the path with maximum weight sum between source and target.

        Returns the weights of edges directly connected to source and target
        in the max-weight path.

        Args:
            G: NetworkX directed graph.
            source: Source node.
            target: Target node.

        Returns:
            Tuple of (source_edge_weight, target_edge_weight).
            Returns (0, 0) if no path exists.
        """
        paths = list(nx.all_simple_paths(G, source, target))

        if not paths:
            return 0, 0

        max_weight = 0
        max_path = None

        for path in paths:
            path_weight = sum(G[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
            if path_weight > max_weight:
                max_weight = path_weight
                max_path = path

        if max_path:
            w_source = G[max_path[0]][max_path[1]]['weight']
            w_target = G[max_path[-2]][max_path[-1]]['weight']
            return w_source, w_target

        return 0, 0

    def compute_collective_influence(self, G: nx.DiGraph, node: str) -> float:
        """
        Compute the Collective Influence (CI) of a node.

        The CI calculation considers three levels of neighborhood:
        - C1: Direct neighbors (J1)
        - C2: Nodes at distance 2 (J2)
        - C3: Nodes at distance 3 (J3)

        Args:
            G: NetworkX directed graph.
            node: Node name.

        Returns:
            The total CI value for the node.
        """
        # Calculate node strength
        S_i = self.compute_node_strength(G, node)

        # Initialize CI components
        C1_i, C2_i, C3_i = 0, 0, 0

        # J1: Direct neighbors
        J1 = set(G.successors(node)).union(set(G.predecessors(node)))

        # Calculate C1 component
        for j in J1:
            S_j = self.compute_node_strength(G, j)
            w_ij = G[node][j]['weight'] if G.has_edge(node, j) else G[j][node]['weight']
            C1_i += (S_i - w_ij) * (S_j - w_ij)

        # J2: Nodes at distance 2 (excluding J1)
        J2 = set()
        for intermediate in J1:
            J2.update(set(G.successors(intermediate)).union(set(G.predecessors(intermediate))))
        J2 -= J1

        # Calculate C2 component
        for j in J2:
            S_j = self.compute_node_strength(G, j)
            w_source, w_target = self.find_max_path_weight(G, node, j)
            C2_i += (S_i - w_source) * (S_j - w_target)

        # J3: Nodes at distance 3 (excluding J1 and J2)
        J3 = set()
        for intermediate in J2:
            J3.update(set(G.successors(intermediate)).union(set(G.predecessors(intermediate))))
        J3 -= J1
        J3 -= J2

        # Calculate C3 component
        for j in J3:
            S_j = self.compute_node_strength(G, j)
            w_source, w_target = self.find_max_path_weight(G, node, j)
            C3_i += (S_i - w_source) * (S_j - w_target)

        # Total CI
        CI_i = C1_i + C2_i + C3_i
        return CI_i

    def compute_all_nodes_CI(self, G: nx.DiGraph) -> Dict[str, float]:
        """
        Compute the CI for all nodes in a graph.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary mapping node names to their CI values.
        """
        node_CI = {}
        for node in G.nodes():
            node_CI[node] = self.compute_collective_influence(G, node)
        return node_CI

    def compute_average_CI_by_category(
        self,
        G: nx.DiGraph,
        node_CI: Dict[str, float],
        node_categories: Dict[str, Set[str]]
    ) -> Dict[str, float]:
        """
        Compute the average CI for each node category.

        Args:
            G: NetworkX directed graph.
            node_CI: Dictionary mapping node names to CI values.
            node_categories: Dictionary mapping category names to sets of node names.

        Returns:
            Dictionary mapping category names to average CI values.
            Categories with no nodes get None as value.
        """
        category_averages = {}

        for category_name, category_nodes in node_categories.items():
            category_CIs = [
                node_CI[node]
                for node in G.nodes()
                if node in category_nodes
            ]

            if category_CIs:
                category_averages[category_name] = sum(category_CIs) / len(category_CIs)
            else:
                category_averages[category_name] = None

        return category_averages

    def compute_CI_for_all_networks(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        node_categories: Dict[str, Set[str]],
        verbose: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Compute the average CI for each category across all networks.

        Args:
            all_networks: Nested dictionary structure:
                {grid_name: {year: {region: G}}}
            node_categories: Dictionary mapping category names to sets of node names.
            verbose: Whether to print progress information.

        Returns:
            Dictionary with keys 'primary', 'processing', 'terminal',
            each containing a pivot DataFrame with CI values.
        """
        import pandas as pd

        primary_results = []
        processing_results = []
        terminal_results = []

        total_networks = sum(
            len(years)
            for years in all_networks.values()
        )
        processed = 0

        # Iterate through all grids, years, and regions
        for grid_name, years_data in all_networks.items():
            for year, regions_data in years_data.items():
                for region, G in regions_data.items():
                    processed += 1
                    if verbose and processed % 100 == 0:
                        print(f"  Processed {processed}/{total_networks} networks...")

                    # Compute CI for all nodes in this network
                    node_CI = self.compute_all_nodes_CI(G)

                    # Compute average CI by category
                    avg_CI = self.compute_average_CI_by_category(G, node_CI, node_categories)

                    # Record results
                    primary_results.append([
                        grid_name, region, year,
                        avg_CI.get('Primary Energy')
                    ])
                    processing_results.append([
                        grid_name, region, year,
                        avg_CI.get('Processing')
                    ])
                    terminal_results.append([
                        grid_name, region, year,
                        avg_CI.get('Terminal')
                    ])

        # Convert to DataFrames
        df_primary = pd.DataFrame(
            primary_results,
            columns=['grid_name', 'region', 'year', 'Primary Energy CI']
        )
        df_processing = pd.DataFrame(
            processing_results,
            columns=['grid_name', 'region', 'year', 'Processing CI']
        )
        df_terminal = pd.DataFrame(
            terminal_results,
            columns=['grid_name', 'region', 'year', 'Terminal CI']
        )

        # Pivot to table format
        df_primary_pivot = df_primary.pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='Primary Energy CI'
        )
        df_processing_pivot = df_processing.pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='Processing CI'
        )
        df_terminal_pivot = df_terminal.pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='Terminal CI'
        )

        return {
            'primary': df_primary_pivot,
            'processing': df_processing_pivot,
            'terminal': df_terminal_pivot
        }


# Convenience functions for backward compatibility
def compute_node_strength(G: nx.DiGraph, node: str) -> float:
    """Compute the strength of a node (convenience function)."""
    calculator = CICalculator()
    return calculator.compute_node_strength(G, node)


def compute_collective_influence(G: nx.DiGraph, node: str) -> float:
    """Compute the CI of a node (convenience function)."""
    calculator = CICalculator()
    return calculator.compute_collective_influence(G, node)


def compute_all_nodes_CI(G: nx.DiGraph) -> Dict[str, float]:
    """Compute CI for all nodes in a graph (convenience function)."""
    calculator = CICalculator()
    return calculator.compute_all_nodes_CI(G)
