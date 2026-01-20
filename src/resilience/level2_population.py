# -*- coding: utf-8 -*-
"""
Level 2 Resilience Module: Population-based indicators.
二级响应（人口）韧性指标模块

This module computes population-based resilience indicators, including:
1. Regional per-capita energy consumption
2. Regional average per-capita energy consumption
3. Per-capita energy surplus
4. Total energy surplus (load shedding capability)

These indicators measure the social capacity to respond to energy disruptions
through demand-side management.
"""

from typing import Dict, List, Optional, Set
import networkx as nx
import pandas as pd
import pickle

from ..preprocessing.config_loader import get_config


class PopulationResilience:
    """
    Calculator for Level 2 (Population-based) resilience indicators.

    This class computes indicators that measure how population factors
    influence energy system resilience.

    Attributes:
        config (ConfigLoader): Configuration loader instance.
        terminal_nodes (Optional[Set]): Set of terminal energy nodes.
        population_adjusted_networks (Optional[Dict]): Population-adjusted network data.
        df_pop (Optional[pd.DataFrame]): Population data DataFrame.

    Example:
        >>> calc = PopulationResilience()
        >>> calc.load_data()
        >>> results = calc.compute_all_indicators()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the PopulationResilience calculator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config = get_config(config_path)

        # Data containers
        self.terminal_nodes: Optional[Set[str]] = None
        self.population_adjusted_networks: Optional[Dict] = None
        self.df_pop: Optional[pd.DataFrame] = None

    def load_data(
        self,
        env_vars_path: Optional[str] = None,
        population_adjusted_networks_path: Optional[str] = None,
        population_path: Optional[str] = None
    ) -> None:
        """
        Load required data files.

        Args:
            env_vars_path: Path to env_vars.pkl (terminal nodes).
            population_adjusted_networks_path: Path to population-adjusted networks.
            population_path: Path to population data (can be combined with GDP data).
        """
        # Load env_vars (terminal nodes)
        if env_vars_path is None:
            env_vars_path = self.config.get_full_path('env_vars')
        if env_vars_path and env_vars_path.exists():
            with open(env_vars_path, 'rb') as f:
                env_vars = pickle.load(f)
            self.terminal_nodes = env_vars['terminal_nodes']

        # Load population-adjusted networks
        if population_adjusted_networks_path is None:
            population_adjusted_networks_path = self.config.get_full_path(
                'population_adjusted_networks'
            )
        if population_adjusted_networks_path and population_adjusted_networks_path.exists():
            with open(population_adjusted_networks_path, 'rb') as f:
                self.population_adjusted_networks = pickle.load(f)

        # Load population data
        if population_path is None:
            population_path = self.config.get_full_path('gdp_population')
        if population_path and population_path.exists():
            with open(population_path, 'rb') as f:
                df_dict = pickle.load(f)
            # Load and drop Tibet, ensure index names are set properly
            self.df_pop = df_dict['pop'].drop('西藏', level='地区')
            # Reset index names to ensure proper MultiIndex alignment
            if hasattr(self.df_pop.index, 'names'):
                self.df_pop.index.names = ['grid_name', 'region']
            else:
                # Reset and set proper index names if needed
                self.df_pop = self.df_pop.reset_index()
                self.df_pop = self.df_pop.set_index(['grid_name', 'region'])

    def compute_regional_energy_consumption(self) -> pd.DataFrame:
        """
        Compute regional per-capita terminal energy consumption.

        Returns:
            DataFrame with columns: 区域名, 地区名, 年份, 人均终端能耗.
        """
        if self.population_adjusted_networks is None or self.terminal_nodes is None:
            raise ValueError("Network data not loaded. Call load_data() first.")

        region_energy_consumption = []

        for grid_name, years_data in self.population_adjusted_networks.items():
            for year, regions_data in years_data.items():
                for region, G in regions_data.items():
                    # Calculate per-capita terminal consumption
                    total_terminal_consumption = sum(
                        G[u][v]['weight']
                        for u, v in G.edges()
                        if v in self.terminal_nodes
                    )
                    region_energy_consumption.append([
                        grid_name, region, year, total_terminal_consumption
                    ])

        df_region_energy = pd.DataFrame(
            region_energy_consumption,
            columns=['grid_name', 'region', 'year', '人均终端能耗']
        )
        return df_region_energy

    def compute_regional_average_consumption(
        self,
        df_region_energy: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute regional average per-capita energy consumption.

        Args:
            df_region_energy: DataFrame from compute_regional_energy_consumption.

        Returns:
            DataFrame with columns: 区域名, 年份, 平均人均终端能耗.
        """
        average_energy_consumption = []

        for grid_name, year_data in df_region_energy.groupby('grid_name'):
            for year, df_year in year_data.groupby('year'):
                average_consumption = df_year['人均终端能耗'].mean()
                average_energy_consumption.append([grid_name, year, average_consumption])

        df_average_energy = pd.DataFrame(
            average_energy_consumption,
            columns=['grid_name', 'year', '平均人均终端能耗']
        )
        return df_average_energy

    def compute_per_capita_energy_surplus(
        self,
        df_region_energy: pd.DataFrame,
        df_average_energy: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute per-capita energy surplus.

        Per-capita Energy Surplus = Regional Consumption - Regional Average

        Args:
            df_region_energy: DataFrame from compute_regional_energy_consumption.
            df_average_energy: DataFrame from compute_regional_average_consumption.

        Returns:
            DataFrame with columns: 区域名, 地区名, 年份, 人均能耗富裕度.
        """
        energy_surplus = []

        for grid_name, regions_data in df_region_energy.groupby('grid_name'):
            df_average_region = df_average_energy[
                df_average_energy['grid_name'] == grid_name
            ]

            for region, df_region in regions_data.groupby('region'):
                for year in df_region['year']:
                    region_consumption = df_region.loc[
                        df_region['year'] == year
                    ]['人均终端能耗'].values[0]

                    average_consumption = df_average_region.loc[
                        df_average_region['year'] == year
                    ]['平均人均终端能耗'].values[0]

                    surplus = region_consumption - average_consumption
                    energy_surplus.append([grid_name, region, year, surplus])

        df_energy_surplus = pd.DataFrame(
            energy_surplus,
            columns=['grid_name', 'region', 'year', '人均能耗富裕度']
        )
        return df_energy_surplus

    def compute_total_energy_surplus(
        self,
        df_energy_surplus: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute total energy surplus (load shedding capability).

        Total Energy Surplus = Per-capita Surplus × Population / 10^3

        Units: ten thousand tons of coal equivalent (万吨标煤)

        Args:
            df_energy_surplus: DataFrame from compute_per_capita_energy_surplus.

        Returns:
            DataFrame with columns: 区域名, 地区名, 年份, 总能耗富裕度.
        """
        if self.df_pop is None:
            raise ValueError("Population data not loaded. Call load_data() first.")

        # Sort by region for proper alignment
        # Based on original code, both DataFrames should have same MultiIndex structure
        # df_energy_surplus_pivot and df_pop have the same MultiIndex

        df_energy_surplus_sorted = df_energy_surplus.sort_index(level=1, ascending=False)
        df_pop_sorted = self.df_pop.sort_index(level=1, ascending=False)

        # Calculate total energy surplus
        df_total_energy_surplus = df_energy_surplus_sorted * df_pop_sorted / 10**3

        # Sort by grid_name (index level 0)
        df_total_energy_surplus = df_total_energy_surplus.sort_index(level=0, ascending=True)

        # The result keeps the same MultiIndex structure

        # Rename column for clarity
        df_total_energy_surplus = df_total_energy_surplus.rename(
            columns={'人均能耗富裕度': '总能耗富裕度'}
        )

        return df_total_energy_surplus

    def compute_all_indicators(self, save_path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Compute all population-based resilience indicators.

        Args:
            save_path: Optional path to save results as Excel file.

        Returns:
            Dictionary with DataFrames for each indicator.
        """
        # Check data loaded
        if self.population_adjusted_networks is None or self.terminal_nodes is None:
            raise ValueError("Network data not loaded. Call load_data() first.")

        # Part 1: Regional energy consumption
        df_region_energy = self.compute_regional_energy_consumption()

        # Part 2: Regional average consumption
        df_average_energy = self.compute_regional_average_consumption(
            df_region_energy
        )

        # Part 3: Per-capita energy surplus
        df_energy_surplus = self.compute_per_capita_energy_surplus(
            df_region_energy, df_average_energy
        )

        # Part 4: Total energy surplus
        # First, pivot df_energy_surplus to have MultiIndex like original code
        df_energy_surplus_pivot = df_energy_surplus.pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='人均能耗富裕度'
        )

        df_total_energy_surplus = self.compute_total_energy_surplus(
            df_energy_surplus_pivot
        )

        results = {
            'regional_energy_consumption': df_region_energy,
            'regional_average_consumption': df_average_energy,
            'per_capita_energy_surplus': df_energy_surplus,
            'total_energy_surplus': df_total_energy_surplus
        }

        # Save to Excel if requested
        if save_path:
            save_path = self.config.resolve_path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                for name, df in results.items():
                    df.to_excel(writer, sheet_name=name)

        return results

    def get_pivot_tables(self, results: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Convert result DataFrames to pivot table format.

        Args:
            results: Dictionary from compute_all_indicators.

        Returns:
            Dictionary with pivot tables.
        """
        df_region_energy_pivot = results['regional_energy_consumption'].pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='人均终端能耗'
        )

        df_average_energy_pivot = results['regional_average_consumption'].pivot(
            index='grid_name',
            columns='year',
            values='平均人均终端能耗'
        )

        df_energy_surplus_pivot = results['per_capita_energy_surplus'].pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='人均能耗富裕度'
        )

        df_total_energy_surplus_pivot = results['total_energy_surplus'].pivot(
            index=['grid_name', 'region'],
            columns='year',
            values='总能耗富裕度'
        )

        return {
            'regional_energy': df_region_energy_pivot,
            'average_energy': df_average_energy_pivot,
            'per_capita_surplus': df_energy_surplus_pivot,
            'total_surplus': df_total_energy_surplus_pivot
        }
