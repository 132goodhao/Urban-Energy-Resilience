# -*- coding: utf-8 -*-
"""
Interprovincial energy flow analysis module.
省际能源流向分析模块

This module provides functionality for analyzing interprovincial energy flows,
including statistics computation, flow allocation, and visualization.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import networkx as nx
import pandas as pd
import numpy as np

from .config_loader import get_config
from .network_builder import NetworkBuilder


class InterprovincialFlowAnalyzer:
    """
    Analyzer for interprovincial energy flows.

    This class provides methods to:
    - Compute energy inflow, outflow, and net flow for each region
    - Allocate interprovincial flows based on distance
    - Visualize flow networks

    Attributes:
        builder (NetworkBuilder): NetworkBuilder instance for accessing network data.
        config (ConfigLoader): Configuration loader instance.
        region2grid (Dict[str, str]): Mapping from region names to grid names.

    Example:
        >>> analyzer = InterprovincialFlowAnalyzer()
        >>> analyzer.load_networks('data/raw/all_networks.pkl')
        >>> stats_2010 = analyzer.compute_energy_stats(
        ...     years=[2010],
        ...     energy_node="煤"
        ... )
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the InterprovincialFlowAnalyzer.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config = get_config(config_path)
        self.builder = NetworkBuilder(config_path)
        self.region2grid: Optional[Dict[str, str]] = None

    def load_networks(self, path: Optional[str] = None) -> None:
        """
        Load network data.

        Args:
            path: Path to the network pickle file.
        """
        self.builder.load_networks(path)
        self.region2grid = self.builder.compute_region_to_grid_mapping()

    def compute_energy_stats(
        self,
        energy_node: str,
        years: Optional[List[int]] = None,
        regions: Optional[Set[str]] = None
    ) -> Dict[int, pd.DataFrame]:
        """
        Compute energy inflow, outflow, and net flow for each region by year.

        Args:
            energy_node: Name of the energy node to analyze (e.g., "煤", "原油").
            years: List of years to analyze. If None, uses all available years.
            regions: Set of regions to analyze. If None, uses all available regions.

        Returns:
            Dictionary mapping years to DataFrames with statistics.

        Example:
            >>> stats = analyzer.compute_energy_stats(
            ...     energy_node="煤",
            ...     years=[2010, 2015, 2020]
            ... )
            >>> df_2010 = stats[2010]
        """
        if self.builder.networks is None:
            raise ValueError("Networks not loaded. Call load_networks() first.")

        # Get all years and regions if not specified
        if years is None:
            years = self.config.get('study.years', list(range(2001, 2021)))
        if regions is None:
            regions = self.builder.get_all_regions()

        stats_dict = {}

        for year in years:
            energy_in = {}
            energy_out = {}

            for region in regions:
                grid_name = self.region2grid.get(region)
                if not grid_name:
                    continue

                try:
                    G = self.builder.get_network(grid_name, year, region)
                except ValueError:
                    continue

                # Compute inflow (from interprovincial)
                for u, v, d in G.edges(data=True):
                    if u == NetworkBuilder.NODE_IN_INTERPROVINCIAL and v == energy_node:
                        energy_in[region] = energy_in.get(region, 0) + abs(d['weight'])

                # Compute outflow (to interprovincial)
                for u, v, d in G.edges(data=True):
                    if u == energy_node and v == NetworkBuilder.NODE_OUT_INTERPROVINCIAL:
                        energy_out[region] = energy_out.get(region, 0) + abs(d['weight'])

            # Ensure all regions are in the result
            for region in regions:
                energy_in.setdefault(region, 0.0)
                energy_out.setdefault(region, 0.0)

            df_stats = pd.DataFrame({
                "region": list(regions),
                "energy_in": [energy_in[r] for r in regions],
                "energy_out": [energy_out[r] for r in regions]
            })
            df_stats['net'] = df_stats['energy_in'] - df_stats['energy_out']
            stats_dict[year] = df_stats

        return stats_dict

    def allocate_provincial_flows(
        self,
        df_stats: pd.DataFrame,
        df_gis: pd.DataFrame,
        energy_label: str = "energy"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Allocate interprovincial flows based on distance priority.

        This method uses a distance-based allocation algorithm:
        - For each net-exporting region, allocate flows to net-importing regions
        - Allocation priority: closer regions first (distance-based)

        Args:
            df_stats: DataFrame with 'region', 'energy_in', 'energy_out', 'net' columns.
            df_gis: DataFrame with 'region', 'x', 'y' columns for geographic coordinates.
            energy_label: Label for the energy value column in the output.

        Returns:
            Tuple of:
            - df_alloc: DataFrame with allocated flows ('from', 'to', energy_label)
            - df_out_left: DataFrame with unallocated outflows
            - df_in_left: DataFrame with unmet inflows

        Example:
            >>> df_stats_2010 = stats[2010]
            >>> df_alloc, df_out_left, df_in_left = analyzer.allocate_provincial_flows(
            ...     df_stats_2010, df_gis
            ... )
        """
        # Identify net-importing and net-exporting regions
        input_regions = df_stats[df_stats['net'] > 1e-6]['region'].tolist()
        output_regions = df_stats[df_stats['net'] < -1e-6]['region'].tolist()

        # Get location data
        locs = df_gis.set_index('region')[['x', 'y']].to_dict(orient='index')

        # Initial allocation quantities
        out_unallocated = {
            r: -df_stats.loc[df_stats['region'] == r, 'net'].values[0]
            for r in output_regions
        }
        in_unmet = {
            r: df_stats.loc[df_stats['region'] == r, 'net'].values[0]
            for r in input_regions
        }

        # Compute distance matrix
        distance_matrix = pd.DataFrame(
            [
                [np.hypot(locs[a]['x'] - locs[b]['x'], locs[a]['y'] - locs[b]['y'])
                 for b in input_regions]
                for a in output_regions
            ],
            index=output_regions,
            columns=input_regions
        )

        # Perform allocation
        allocation = []
        for a in output_regions:
            remain = out_unallocated[a]

            # Get candidate destinations (still have unmet demand)
            candidates = [
                (distance_matrix.loc[a, b], b)
                for b in input_regions
                if in_unmet[b] > 1e-6
            ]
            candidates.sort()  # Sort by distance (closest first)

            for _, b in candidates:
                if remain < 1e-6:
                    break
                demand = in_unmet[b]
                val = min(remain, demand)
                if val > 0:
                    allocation.append({'from': a, 'to': b, energy_label: val})
                    remain -= val
                    in_unmet[b] -= val

            out_unallocated[a] = remain

        # Compute unallocated/unmet statistics
        unallocated_stats = []
        for r in output_regions:
            total = -df_stats.loc[df_stats['region'] == r, 'net'].values[0]
            left = out_unallocated[r]
            unallocated_stats.append({
                'region': r,
                'unallocated': left,
                'unallocated_pct': left / total if total > 0 else 0
            })

        unmet_stats = []
        for r in input_regions:
            total = df_stats.loc[df_stats['region'] == r, 'net'].values[0]
            left = in_unmet[r]
            unmet_stats.append({
                'region': r,
                'unmet': left,
                'unmet_pct': left / total if total > 0 else 0
            })

        df_alloc = pd.DataFrame(allocation)
        df_out_left = pd.DataFrame(unallocated_stats)
        df_in_left = pd.DataFrame(unmet_stats)

        return df_alloc, df_out_left, df_in_left

    def visualize_provincial_network(
        self,
        df_alloc: pd.DataFrame,
        df_gis: pd.DataFrame,
        save_path: Optional[str] = None,
        energy_color: str = "#da70d6",
        figsize: Tuple[int, int] = (14, 9),
        dpi: int = 300
    ) -> None:
        """
        Visualize the interprovincial flow network.

        Args:
            df_alloc: DataFrame with allocated flows ('from', 'to', energy_label).
            df_gis: DataFrame with 'region', 'x', 'y' columns for geographic coordinates.
            save_path: Path to save the figure. If None, doesn't save.
            energy_color: Color for the flow arrows.
            figsize: Figure size (width, height).
            dpi: Dots per inch for the output image.

        Example:
            >>> analyzer.visualize_provincial_network(
            ...     df_alloc, df_gis,
            ...     save_path="outputs/figures/coal_network_2010.png"
            ... )
        """
        import matplotlib.pyplot as plt

        locs = df_gis.set_index('region')[['x', 'y']].to_dict(orient='index')

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Draw nodes
        for _, row in df_gis.iterrows():
            ax.scatter(
                row['x'], row['y'],
                s=300,
                color='lightblue',
                edgecolor='k',
                zorder=5
            )
            ax.text(
                row['x'], row['y'],
                row['region'],
                ha='center',
                va='center',
                fontsize=8,
                zorder=6
            )

        # Get flow values for arrow width scaling
        flow_col = [col for col in df_alloc.columns if col not in ['from', 'to']][0]
        flow_values = df_alloc[flow_col].values
        vmin, vmax = flow_values.min(), flow_values.max()
        min_width, max_width = 0.8, 6

        def scale(val):
            """Scale arrow width based on flow value."""
            if vmax == vmin:
                return (min_width + max_width) / 2
            return min_width + (max_width - min_width) * (val - vmin) / (vmax - vmin)

        # Draw flow arrows
        for _, row in df_alloc.iterrows():
            x1, y1 = locs[row['from']]['x'], locs[row['from']]['y']
            x2, y2 = locs[row['to']]['x'], locs[row['to']]['y']
            width = scale(row[flow_col])

            ax.annotate(
                '',
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="->",
                    color=energy_color,
                    lw=width,
                    alpha=0.7,
                    mutation_scale=18
                ),
                zorder=3
            )

        ax.axis('off')
        plt.tight_layout()

        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=dpi, transparent=True)

        plt.show()

    def compute_all_years_flows(
        self,
        energy_node: str,
        df_gis: pd.DataFrame,
        energy_label: str = "energy",
        years: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, pd.DataFrame]]:
        """
        Compute and allocate flows for all years.

        Args:
            energy_node: Name of the energy node to analyze.
            df_gis: DataFrame with 'region', 'x', 'y' columns.
            energy_label: Label for the energy value column.
            years: List of years to analyze.

        Returns:
            Dictionary mapping years to dictionaries with 'stats', 'alloc', 'out_left', 'in_left'.
        """
        if years is None:
            years = self.config.get('study.years', list(range(2001, 2021)))

        stats_dict = self.compute_energy_stats(energy_node, years)

        results = {}
        for year, df_stats in stats_dict.items():
            df_alloc, df_out_left, df_in_left = self.allocate_provincial_flows(
                df_stats, df_gis, energy_label
            )
            results[year] = {
                'stats': df_stats,
                'alloc': df_alloc,
                'out_left': df_out_left,
                'in_left': df_in_left
            }

        return results

    def get_top_importers(
        self,
        energy_node: str,
        year: int,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Get the top importers for a given energy type and year.

        Args:
            energy_node: Name of the energy node to analyze.
            year: Year to analyze.
            top_n: Number of top importers to return.

        Returns:
            DataFrame with top importers and their net imports.
        """
        stats_dict = self.compute_energy_stats(energy_node, [year])
        df_stats = stats_dict[year]

        return df_stats.nlargest(top_n, 'net')

    def get_top_exporters(
        self,
        energy_node: str,
        year: int,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Get the top exporters for a given energy type and year.

        Args:
            energy_node: Name of the energy node to analyze.
            year: Year to analyze.
            top_n: Number of top exporters to return.

        Returns:
            DataFrame with top exporters and their net exports.
        """
        stats_dict = self.compute_energy_stats(energy_node, [year])
        df_stats = stats_dict[year]

        return df_stats.nsmallest(top_n, 'net')
