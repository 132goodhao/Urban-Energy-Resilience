# -*- coding: utf-8 -*-
"""
Network data fixing module.
网络数据修复模块

This module provides functionality for fixing errors in energy network data,
particularly unit conversion errors that may have been introduced during
data processing.

Background:
    Some short names have inclusion relationships that lead to double counting:
    - '煤平衡表' is contained in: 型煤平衡表, 其他洗煤平衡表, 洗精煤平衡表, 原煤平衡表
    - '天然气平衡表' is contained in: 液化天然气平衡表

    Correction needed:
    - Divide values for 型煤、其他洗煤、洗精煤、原煤 by coal conversion factor 0.697664
    - Divide values for 液化天然气平衡表 by natural gas conversion factor 12.7612
"""

import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Set
import networkx as nx

from .config_loader import get_config


class NetworkFixer:
    """
    Network data fixer for correcting unit conversion errors.

    This class provides methods to fix known issues in the network data,
    particularly the double-counting issue with certain energy categories.

    Attributes:
        config (ConfigLoader): Configuration loader instance.
        node_set_1 (Set[str]): First set of nodes requiring weight adjustment (coal types).
        node_set_2 (Set[str]): Second set of nodes requiring weight adjustment (LNG).
        factor_1 (float): Conversion factor for coal-related nodes (0.697664).
        factor_2 (float): Conversion factor for LNG nodes (12.7612).

    Example:
        >>> fixer = NetworkFixer()
        >>> fixed_networks = fixer.fix_networks(all_networks)
        >>> fixer.save_networks(fixed_networks, "networks/all_networks_fixed.pkl")
    """

    # Known node sets requiring adjustment
    NODE_SET_1 = {"原煤", "型煤", "其他洗煤", "洗精煤"}
    NODE_SET_2 = {"液化天然气"}

    # Conversion factors
    FACTOR_COAL = 0.697664  # Coal conversion factor (折标系数)
    FACTOR_LNG = 12.7612    # LNG conversion factor (折标系数)

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the NetworkFixer.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config = get_config(config_path)

    @property
    def node_set_1(self) -> Set[str]:
        """Get the first set of nodes (coal types) requiring adjustment."""
        return self.NODE_SET_1

    @property
    def node_set_2(self) -> Set[str]:
        """Get the second set of nodes (LNG) requiring adjustment."""
        return self.NODE_SET_2

    @property
    def factor_1(self) -> float:
        """Get the first conversion factor (coal)."""
        return self.FACTOR_COAL

    @property
    def factor_2(self) -> float:
        """Get the second conversion factor (LNG)."""
        return self.FACTOR_LNG

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
            return pickle.load(f)

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
            path = Path('data/processed/all_networks_fixed.pkl')
        else:
            path = Path(path)

        if create_dir:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(networks, f)

    def fix_network(
        self,
        G: nx.DiGraph,
        inplace: bool = False
    ) -> nx.DiGraph:
        """
        Fix a single network graph by adjusting edge weights for specific nodes.

        Args:
            G: The NetworkX directed graph to fix.
            inplace: If True, modify the graph in place. If False, create a copy.

        Returns:
            The fixed network graph.
        """
        if not inplace:
            G = G.copy()

        # Iterate through all edges and adjust weights
        for u, v, data in list(G.edges(data=True)):
            if u in self.node_set_1 or v in self.node_set_1:
                # Adjust for coal-related nodes
                G[u][v]['weight'] /= self.factor_1
            elif u in self.node_set_2 or v in self.node_set_2:
                # Adjust for LNG nodes
                G[u][v]['weight'] /= self.factor_2

        return G

    def fix_networks(
        self,
        networks: Dict[str, Any],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Fix all network graphs in the networks dictionary.

        The networks dictionary is expected to have the structure:
        {
            'grid_name': {
                'year': {
                    'region_name': nx.DiGraph,
                    ...
                },
                ...
            },
            ...
        }

        Args:
            networks: Dictionary containing network data.
            verbose: If True, print progress information.

        Returns:
            Dictionary containing fixed network data.

        Example:
            >>> fixer = NetworkFixer()
            >>> all_networks = fixer.load_networks()
            >>> fixed_networks = fixer.fix_networks(all_networks, verbose=True)
        """
        fixed_networks = {}
        total_grids = len(networks)

        for grid_idx, (grid_name, years) in enumerate(networks.items(), 1):
            if verbose:
                print(f"Processing grid {grid_idx}/{total_grids}: {grid_name}")

            fixed_networks[grid_name] = {}
            total_years = len(years)

            for year_idx, (year, regions) in enumerate(years.items(), 1):
                if verbose and total_years > 5:
                    print(f"  Year {year_idx}/{total_years}: {year}")

                fixed_networks[grid_name][year] = {}

                for region_name, G in regions.items():
                    # Fix the network for this region
                    fixed_G = self.fix_network(G, inplace=False)
                    fixed_networks[grid_name][year][region_name] = fixed_G

        if verbose:
            print(f"\nNetwork fixing complete!")
            print(f"Processed {total_grids} grids")

        return fixed_networks

    def fix_and_save(
        self,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        verbose: bool = False
    ) -> None:
        """
        Load, fix, and save network data in one operation.

        Args:
            input_path: Path to input pickle file.
            output_path: Path to save the fixed networks.
            verbose: If True, print progress information.

        Example:
            >>> fixer = NetworkFixer()
            >>> fixer.fix_and_save(
            ...     input_path="data/raw/all_networks.pkl",
            ...     output_path="data/processed/all_networks_fixed.pkl",
            ...     verbose=True
            ... )
        """
        if verbose:
            print("Loading networks...")
        networks = self.load_networks(input_path)

        if verbose:
            print("Fixing networks...")
        fixed_networks = self.fix_networks(networks, verbose=verbose)

        if verbose:
            print(f"Saving to {output_path}...")
        self.save_networks(fixed_networks, output_path)

        if verbose:
            print("Done!")

    def compare_networks(
        self,
        networks_original: Dict[str, Any],
        networks_fixed: Dict[str, Any],
        grid_name: str,
        year: int,
        region_name: str
    ) -> Dict[str, nx.DiGraph]:
        """
        Compare original and fixed networks for a specific grid/year/region.

        Args:
            networks_original: Original networks dictionary.
            networks_fixed: Fixed networks dictionary.
            grid_name: Name of the grid.
            year: Year to compare.
            region_name: Region name to compare.

        Returns:
            Dictionary with 'original' and 'fixed' network graphs.

        Raises:
            KeyError: If the specified grid/year/region combination does not exist.
        """
        G_original = networks_original[grid_name][year][region_name]
        G_fixed = networks_fixed[grid_name][year][region_name]

        return {
            'original': G_original,
            'fixed': G_fixed
        }

    def get_edge_diff(
        self,
        G_original: nx.DiGraph,
        G_fixed: nx.DiGraph
    ) -> Dict[str, float]:
        """
        Get the differences in edge weights between original and fixed networks.

        Args:
            G_original: Original network graph.
            G_fixed: Fixed network graph.

        Returns:
            Dictionary of edge weight differences.
        """
        diff = {}
        for u, v, data in G_fixed.edges(data=True):
            if G_original.has_edge(u, v):
                original_weight = G_original[u][v]['weight']
                fixed_weight = data['weight']
                diff[(u, v)] = fixed_weight - original_weight
        return diff


def main():
    """
    Command-line interface for the NetworkFixer.

    Usage:
        python -m src.preprocessing.network_fix --input data/raw/all_networks.pkl --output data/processed/all_networks_fixed.pkl
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix energy network data by adjusting unit conversion errors"
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to input pickle file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output pickle file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print progress information'
    )

    args = parser.parse_args()

    fixer = NetworkFixer()
    fixer.fix_and_save(
        input_path=args.input,
        output_path=args.output,
        verbose=args.verbose
    )


if __name__ == '__main__':
    main()
