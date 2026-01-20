# -*- coding: utf-8 -*-
"""
Network builder module.
网络构建模块

This module provides functionality for building, loading, and processing
energy network graphs from various data sources.
"""

import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
import networkx as nx
import pandas as pd

from .config_loader import get_config


class NetworkBuilder:
    """
    Builder for constructing and managing energy network graphs.

    This class provides methods to load network data, construct NetworkX graphs,
    and perform common network operations.

    Attributes:
        config (ConfigLoader): Configuration loader instance.
        networks (Optional[Dict]): Loaded network data.

    Example:
        >>> builder = NetworkBuilder()
        >>> networks = builder.load_networks()
        >>> graph = builder.get_network('华北', 2010, '北京')
    """

    # Standard node names for inter-provincial flows
    NODE_IN_INTERPROVINCIAL = "外省_区、市调入量"
    NODE_OUT_INTERPROVINCIAL = "本省_区、市调出量_-"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the NetworkBuilder.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config = get_config(config_path)
        self.networks: Optional[Dict[str, Any]] = None

    def load_networks(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load network data from a pickle file.

        Args:
            path: Path to the pickle file. If None, uses default from config.

        Returns:
            Dictionary containing network data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if path is None:
            path = self.config.get_full_path('networks')
            if path is None:
                path = Path('data/raw/all_networks.pkl')
        else:
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Network data file not found: {path}")

        with open(path, 'rb') as f:
            self.networks = pickle.load(f)

        return self.networks

    def save_networks(
        self,
        networks: Dict[str, Any],
        path: Optional[str] = None,
        create_dir: bool = True
    ) -> None:
        """
        Save network data to a pickle file.

        Args:
            networks: Dictionary containing network data.
            path: Path to save the file. If None, uses default output path.
            create_dir: Whether to create parent directories if they don't exist.
        """
        if path is None:
            path = Path('data/processed/networks_processed.pkl')
        else:
            path = Path(path)

        if create_dir:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(networks, f)

    def get_available_grids(self) -> List[str]:
        """
        Get list of available power grid names.

        Returns:
            List of grid names.

        Raises:
            ValueError: If networks have not been loaded.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")
        return list(self.networks.keys())

    def get_available_years(self, grid_name: str) -> List[int]:
        """
        Get list of available years for a given grid.

        Args:
            grid_name: Name of the power grid.

        Returns:
            List of years.

        Raises:
            ValueError: If networks have not been loaded or grid not found.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")
        if grid_name not in self.networks:
            raise ValueError(f"Grid '{grid_name}' not found.")
        return list(self.networks[grid_name].keys())

    def get_available_regions(self, grid_name: str, year: int) -> List[str]:
        """
        Get list of available regions for a given grid and year.

        Args:
            grid_name: Name of the power grid.
            year: Year.

        Returns:
            List of region names.

        Raises:
            ValueError: If networks have not been loaded or grid/year not found.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")
        if grid_name not in self.networks:
            raise ValueError(f"Grid '{grid_name}' not found.")
        if year not in self.networks[grid_name]:
            raise ValueError(f"Year {year} not found for grid '{grid_name}'.")
        return list(self.networks[grid_name][year].keys())

    def get_network(
        self,
        grid_name: str,
        year: int,
        region_name: str
    ) -> nx.DiGraph:
        """
        Get a specific network graph.

        Args:
            grid_name: Name of the power grid.
            year: Year.
            region_name: Region name.

        Returns:
            NetworkX directed graph.

        Raises:
            ValueError: If networks have not been loaded or specified network not found.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        try:
            return self.networks[grid_name][year][region_name]
        except KeyError as e:
            raise ValueError(
                f"Network not found for grid='{grid_name}', year={year}, region='{region_name}'. "
                f"Missing key: {e}"
            )

    def network_exists(
        self,
        grid_name: str,
        year: int,
        region_name: str
    ) -> bool:
        """
        Check if a specific network graph exists.

        Args:
            grid_name: Name of the power grid.
            year: Year.
            region_name: Region name.

        Returns:
            True if the network exists, False otherwise.
        """
        if self.networks is None:
            return False

        try:
            return (
                grid_name in self.networks and
                year in self.networks[grid_name] and
                region_name in self.networks[grid_name][year]
            )
        except (KeyError, TypeError):
            return False

    def get_network_info(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Get basic information about a network graph.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary containing network statistics.
        """
        return {
            'n_nodes': G.number_of_nodes(),
            'n_edges': G.number_of_edges(),
            'is_directed': G.is_directed(),
            'is_weighted': any('weight' in d for _, _, d in G.edges(data=True)),
            'nodes': list(G.nodes()),
            'density': nx.density(G) if G.number_of_nodes() > 0 else 0
        }

    def filter_networks_by_years(
        self,
        years: List[int]
    ) -> Dict[str, Any]:
        """
        Filter networks to include only specified years.

        Args:
            years: List of years to keep.

        Returns:
            Filtered networks dictionary.

        Raises:
            ValueError: If networks have not been loaded.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        filtered = {}
        years_set = set(years)

        for grid_name, grid_data in self.networks.items():
            filtered[grid_name] = {
                year: regions
                for year, regions in grid_data.items()
                if year in years_set
            }

        return filtered

    def filter_networks_by_regions(
        self,
        regions: Set[str]
    ) -> Dict[str, Any]:
        """
        Filter networks to include only specified regions.

        Args:
            regions: Set of region names to keep.

        Returns:
            Filtered networks dictionary.

        Raises:
            ValueError: If networks have not been loaded.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        filtered = {}
        regions_set = set(regions)

        for grid_name, grid_data in self.networks.items():
            filtered[grid_name] = {}
            for year, year_data in grid_data.items():
                filtered[grid_name][year] = {
                    region: G
                    for region, G in year_data.items()
                    if region in regions_set
                }

        return filtered

    def get_all_regions(self) -> Set[str]:
        """
        Get all unique region names across all grids and years.

        Returns:
            Set of all region names.

        Raises:
            ValueError: If networks have not been loaded.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        regions = set()
        for grid_data in self.networks.values():
            for year_data in grid_data.values():
                regions.update(year_data.keys())

        return regions

    def get_grid_for_region(self, region_name: str) -> Optional[str]:
        """
        Find which grid contains a given region.

        Args:
            region_name: Name of the region.

        Returns:
            Grid name if found, None otherwise.

        Raises:
            ValueError: If networks have not been loaded.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        for grid_name, grid_data in self.networks.items():
            for year_data in grid_data.values():
                if region_name in year_data:
                    return grid_name

        return None

    def compute_region_to_grid_mapping(self) -> Dict[str, str]:
        """
        Create a mapping from region names to grid names.

        Returns:
            Dictionary mapping region names to grid names.

        Raises:
            ValueError: If networks have not been loaded.
        """
        if self.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        region2grid = {}

        for grid_name, grid_data in self.networks.items():
            for year_data in grid_data.values():
                for region_name in year_data.keys():
                    if region_name not in region2grid:
                        region2grid[region_name] = grid_name

        return region2grid

    def get_node_types(self, G: nx.DiGraph) -> Dict[str, str]:
        """
        Infer node types based on network structure.

        This is a heuristic classification. For accurate classification,
        use the env_vars data file.

        Args:
            G: NetworkX directed graph.

        Returns:
            Dictionary mapping node names to inferred types.
        """
        # This is a simplified heuristic
        # In practice, use env_vars for accurate classification
        node_types = {}

        for node in G.nodes():
            # Check for inter-provincial nodes
            if node == self.NODE_IN_INTERPROVINCIAL:
                node_types[node] = 'interprovincial_in'
            elif node == self.NODE_OUT_INTERPROVINCIAL:
                node_types[node] = 'interprovincial_out'
            # Check for primary energy nodes (usually only have outgoing edges)
            elif G.out_degree(node) > 0 and G.in_degree(node) == 0:
                node_types[node] = 'primary_energy'
            # Check for consumption nodes (usually only have incoming edges)
            elif G.in_degree(node) > 0 and G.out_degree(node) == 0:
                node_types[node] = 'consumption'
            else:
                node_types[node] = 'processing'

        return node_types

    def create_network_from_dataframe(
        self,
        df: pd.DataFrame,
        source_col: str = 'source',
        target_col: str = 'target',
        weight_col: str = 'weight'
    ) -> nx.DiGraph:
        """
        Create a NetworkX graph from a pandas DataFrame.

        Args:
            df: DataFrame containing edge information.
            source_col: Name of column containing source nodes.
            target_col: Name of column containing target nodes.
            weight_col: Name of column containing edge weights.

        Returns:
            NetworkX directed graph.
        """
        G = nx.DiGraph()

        for _, row in df.iterrows():
            source = row[source_col]
            target = row[target_col]
            weight = row.get(weight_col, 1.0)

            if G.has_edge(source, target):
                G[source][target]['weight'] += weight
            else:
                G.add_edge(source, target, weight=weight)

        return G


class NetworkStats:
    """
    Utility class for computing network statistics.

    This class provides static methods for computing various
    network metrics.
    """

    @staticmethod
    def total_flow(G: nx.DiGraph) -> float:
        """
        Calculate total flow through the network.

        Args:
            G: NetworkX directed graph.

        Returns:
            Total absolute flow.
        """
        total = 0.0
        for u, v, data in G.edges(data=True):
            weight = data.get('weight', 1.0)
            total += abs(weight)
        return total

    @staticmethod
    def node_flow(G: nx.DiGraph, node: str) -> Dict[str, float]:
        """
        Calculate total inflow and outflow for a node.

        Args:
            G: NetworkX directed graph.
            node: Node name.

        Returns:
            Dictionary with 'inflow', 'outflow', and 'net' values.
        """
        inflow = sum(
            abs(d.get('weight', 1.0))
            for _, _, d in G.in_edges(node, data=True)
        )
        outflow = sum(
            abs(d.get('weight', 1.0))
            for _, _, d in G.out_edges(node, data=True)
        )
        return {
            'inflow': inflow,
            'outflow': outflow,
            'net': inflow - outflow
        }

    @staticmethod
    def edge_summary(G: nx.DiGraph) -> pd.DataFrame:
        """
        Create a summary DataFrame of all edges.

        Args:
            G: NetworkX directed graph.

        Returns:
            DataFrame with edge information.
        """
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                'source': u,
                'target': v,
                'weight': data.get('weight', 1.0)
            })
        return pd.DataFrame(edges)

    @staticmethod
    def node_summary(G: nx.DiGraph) -> pd.DataFrame:
        """
        Create a summary DataFrame of all nodes.

        Args:
            G: NetworkX directed graph.

        Returns:
            DataFrame with node information.
        """
        nodes = []
        for node in G.nodes():
            stats = NetworkStats.node_flow(G, node)
            nodes.append({
                'node': node,
                'inflow': stats['inflow'],
                'outflow': stats['outflow'],
                'net': stats['net'],
                'degree': G.degree(node),
                'in_degree': G.in_degree(node),
                'out_degree': G.out_degree(node)
            })
        return pd.DataFrame(nodes)
