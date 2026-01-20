# -*- coding: utf-8 -*-
"""
Network metrics module.
网络指标计算模块

This module provides additional network analysis metrics beyond CI and NCI,
including connectivity, centrality, and structural measures.
"""

from typing import Dict, List, Optional, Set
import networkx as nx
import pandas as pd
import numpy as np


class NetworkMetrics:
    """
    Calculator for various network metrics.

    This class provides methods to compute centrality, connectivity,
    and other structural metrics for energy networks.

    Example:
        >>> metrics = NetworkMetrics()
        >>> centrality = metrics.compute_centrality(G)
        >>> connectivity = metrics.compute_connectivity(G)
    """

    def __init__(self):
        """Initialize the network metrics calculator."""
        pass

    # ==================== Centrality Metrics ====================

    def compute_centrality(self, G: nx.DiGraph, normalized: bool = True) -> Dict[str, Dict[str, float]]:
        """
        Compute various centrality measures for all nodes.

        Args:
            G: NetworkX directed graph.
            normalized: Whether to normalize centrality values.

        Returns:
            Dictionary mapping metric names to node centrality values.
        """
        # In-degree centrality
        in_degree_centrality = nx.in_degree_centrality(G)

        # Out-degree centrality
        out_degree_centrality = nx.out_degree_centrality(G)

        # Betweenness centrality (consider weight)
        try:
            betweenness_centrality = nx.betweenness_centrality(
                G, normalized=normalized, weight='weight'
            )
        except Exception:
            betweenness_centrality = nx.betweenness_centrality(G, normalized=normalized)

        # Closeness centrality
        try:
            closeness_centrality = nx.closeness_centrality(G)
        except Exception:
            closeness_centrality = {node: 0 for node in G.nodes()}

        return {
            'in_degree_centrality': in_degree_centrality,
            'out_degree_centrality': out_degree_centrality,
            'betweenness_centrality': betweenness_centrality,
            'closeness_centrality': closeness_centrality
        }

    def compute_pagerank(
        self,
        G: nx.DiGraph,
        alpha: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-6
    ) -> Dict[str, float]:
        """
        Compute PageRank centrality for all nodes.

        Args:
            G: NetworkX directed graph.
            alpha: Damping parameter.
            max_iter: Maximum number of iterations.
            tol: Convergence tolerance.

        Returns:
            Dictionary mapping node names to PageRank values.
        """
        return nx.pagerank(G, alpha=alpha, max_iter=max_iter, tol=tol)

    def compute_node_importance(
        self,
        G: nx.DiGraph,
        method: str = 'pagerank',
        **kwargs
    ) -> Dict[str, float]:
        """
        Compute node importance using specified method.

        Args:
            G: NetworkX directed graph.
            method: Method to use ('pagerank', 'betweenness', 'degree', 'weighted_degree').
            **kwargs: Additional arguments for the centrality function.

        Returns:
            Dictionary mapping node names to importance scores.
        """
        method = method.lower()

        if method == 'pagerank':
            return self.compute_pagerank(G, **kwargs)
        elif method == 'betweenness':
            return nx.betweenness_centrality(G, weight='weight', **kwargs)
        elif method == 'degree':
            return dict(nx.degree(G))
        elif method == 'weighted_degree':
            return dict(G.degree(weight='weight'))
        else:
            raise ValueError(f"Unknown method: {method}")

    # ==================== Connectivity Metrics ====================

    def compute_connectivity(self, G: nx.DiGraph) -> Dict[str, float]:
        """
        Compute network connectivity metrics.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary with connectivity metrics.
        """
        metrics = {}

        # Density
        metrics['density'] = nx.density(G)

        # Average clustering coefficient
        try:
            metrics['avg_clustering'] = nx.average_clustering(G.to_undirected())
        except Exception:
            metrics['avg_clustering'] = 0

        # Number of connected components (undirected view)
        try:
            metrics['n_components'] = nx.number_connected_components(G.to_undirected())
        except Exception:
            metrics['n_components'] = 1

        # For directed graphs: strongly connected components
        try:
            metrics['n_strongly_connected'] = nx.number_strongly_connected_components(G)
        except Exception:
            metrics['n_strongly_connected'] = 1

        # Is giant component size ratio
        if G.number_of_nodes() > 0:
            G_undirected = G.to_undirected()
            largest_cc = max(nx.connected_components(G_undirected), key=len)
            metrics['giant_component_ratio'] = len(largest_cc) / G.number_of_nodes()
        else:
            metrics['giant_component_ratio'] = 0

        return metrics

    def compute_flow_metrics(self, G: nx.DiGraph) -> Dict[str, float]:
        """
        Compute flow-related metrics for an energy network.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary with flow metrics.
        """
        metrics = {}

        # Total flow
        metrics['total_flow'] = sum(
            abs(d.get('weight', 1.0))
            for _, _, d in G.edges(data=True)
        )

        # Node-level flow statistics
        node_flows = []
        for node in G.nodes():
            inflow = sum(
                abs(d.get('weight', 1.0))
                for _, _, d in G.in_edges(node, data=True)
            )
            outflow = sum(
                abs(d.get('weight', 1.0))
                for _, _, d in G.out_edges(node, data=True)
            )
            node_flows.append((inflow, outflow))

        # Aggregate statistics
        inflows = [f[0] for f in node_flows]
        outflows = [f[1] for f in node_flows]
        net_flows = [f[0] - f[1] for f in node_flows]

        metrics['avg_inflow'] = np.mean(inflows) if inflows else 0
        metrics['avg_outflow'] = np.mean(outflows) if outflows else 0
        metrics['max_inflow'] = max(inflows) if inflows else 0
        metrics['max_outflow'] = max(outflows) if outflows else 0
        metrics['std_inflow'] = np.std(inflows) if len(inflows) > 1 else 0
        metrics['std_outflow'] = np.std(outflows) if len(outflows) > 1 else 0

        return metrics

    # ==================== Node Set Analysis ====================

    def analyze_node_sets(
        self,
        G: nx.DiGraph,
        node_sets: Dict[str, Set[str]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze properties of predefined node sets.

        Args:
            G: NetworkX directed graph.
            node_sets: Dictionary mapping set names to sets of node names.

        Returns:
            Dictionary with metrics for each node set.
        """
        results = {}

        for set_name, nodes in node_sets.items():
            valid_nodes = [n for n in nodes if n in G.nodes()]

            if not valid_nodes:
                results[set_name] = {}
                continue

            # Average degree
            degrees = [G.degree(n) for n in valid_nodes]
            avg_degree = np.mean(degrees) if degrees else 0

            # Total flow
            total_flow = 0
            for n in valid_nodes:
                total_flow += sum(
                    abs(d.get('weight', 1.0))
                    for _, _, d in G.edges(n, data=True)
                )

            # Betweenness centrality average
            try:
                betweenness = nx.betweenness_centrality(G, weight='weight')
                avg_betweenness = np.mean([betweenness.get(n, 0) for n in valid_nodes])
            except Exception:
                avg_betweenness = 0

            results[set_name] = {
                'n_nodes': len(valid_nodes),
                'avg_degree': avg_degree,
                'total_flow': total_flow,
                'avg_betweenness': avg_betweenness
            }

        return results

    # ==================== Path-based Metrics ====================

    def compute_shortest_path_stats(self, G: nx.DiGraph) -> Dict[str, float]:
        """
        Compute shortest path statistics.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary with path statistics.
        """
        # Consider only the largest connected component
        G_undirected = G.to_undirected()
        largest_cc_nodes = max(
            nx.connected_components(G_undirected),
            key=len
        )
        G_sub = G.subgraph(largest_cc_nodes).copy()

        if G_sub.number_of_nodes() < 2:
            return {'avg_path_length': 0, 'diameter': 0}

        # Calculate all pairs shortest paths
        try:
            path_lengths = dict(nx.all_pairs_shortest_path_length(G_sub))
            all_lengths = []
            for source, targets in path_lengths.items():
                for target, length in targets.items():
                    if length > 0:
                        all_lengths.append(length)

            if all_lengths:
                return {
                    'avg_path_length': np.mean(all_lengths),
                    'diameter': max(all_lengths)
                }
        except Exception:
            pass

        return {'avg_path_length': 0, 'diameter': 0}

    # ==================== Summary ====================

    def compute_all_metrics(self, G: nx.DiGraph) -> Dict[str, any]:
        """
        Compute all available metrics for a network.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary with all metric categories.
        """
        return {
            'connectivity': self.compute_connectivity(G),
            'flow': self.compute_flow_metrics(G),
            'paths': self.compute_shortest_path_stats(G)
        }


def compute_network_summary_dataframe(
    all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
    verbose: bool = False
) -> pd.DataFrame:
    """
    Compute summary metrics for all networks.

    Args:
        all_networks: Nested dictionary structure.
        verbose: Whether to print progress.

    Returns:
        DataFrame with summary metrics for all networks.
    """
    metrics_calculator = NetworkMetrics()
    data = []

    total_networks = sum(len(years) for years in all_networks.values())
    processed = 0

    for grid_name, years_data in all_networks.items():
        for year, regions_data in years_data.items():
            for region, G in regions_data.items():
                processed += 1
                if verbose and processed % 100 == 0:
                    print(f"  Processed {processed}/{total_networks} networks...")

                # Compute all metrics
                all_metrics = metrics_calculator.compute_all_metrics(G)

                # Flatten metrics for DataFrame
                row = {
                    'grid': grid_name,
                    'region': region,
                    'year': year
                }

                # Add connectivity metrics
                for k, v in all_metrics['connectivity'].items():
                    row[f'conn_{k}'] = v

                # Add flow metrics
                for k, v in all_metrics['flow'].items():
                    row[f'flow_{k}'] = v

                # Add path metrics
                for k, v in all_metrics['paths'].items():
                    row[f'path_{k}'] = v

                data.append(row)

    return pd.DataFrame(data)
