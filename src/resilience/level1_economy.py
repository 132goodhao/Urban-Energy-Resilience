# -*- coding: utf-8 -*-
"""
Level 1 Resilience Module: Economy-based indicators.
一级响应（经济）韧性指标模块

This module computes economy-based resilience indicators, including:
1. Regional average GDP
2. Regional economic surplus
3. Regional economic energy consumption
4. Total energy surplus (economic purchasing power)

These indicators measure the economic capacity to respond to energy disruptions.
"""

from typing import Dict, List, Optional, Set
import networkx as nx
import pandas as pd
import pickle

from ..preprocessing.config_loader import get_config


class EconomyResilience:
    """
    Calculator for Level 1 (Economy-based) resilience indicators.

    This class computes indicators that measure how economic factors
    influence energy system resilience.

    Attributes:
        config (ConfigLoader): Configuration loader instance.
        terminal_nodes (Optional[Set]): Set of terminal energy nodes.
        gdp_adjusted_networks (Optional[Dict]): GDP-adjusted network data.
        df_gdp (Optional[pd.DataFrame]): GDP data DataFrame.
        energy_investment_ratio (Optional[pd.DataFrame]): Energy investment ratio data.

    Example:
        >>> calc = EconomyResilience()
        >>> calc.load_data()
        >>> results = calc.compute_all_indicators()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the EconomyResilience calculator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config = get_config(config_path)

        # Data containers
        self.terminal_nodes: Optional[Set[str]] = None
        self.gdp_adjusted_networks: Optional[Dict] = None
        self.df_gdp: Optional[pd.DataFrame] = None
        self.energy_investment_ratio: Optional[pd.DataFrame] = None

    def load_data(
        self,
        env_vars_path: Optional[str] = None,
        gdp_adjusted_networks_path: Optional[str] = None,
        gdp_population_path: Optional[str] = None,
        energy_investment_path: Optional[str] = None
    ) -> None:
        """
        Load required data files.

        Args:
            env_vars_path: Path to env_vars.pkl (terminal nodes).
            gdp_adjusted_networks_path: Path to GDP-adjusted networks.
            gdp_population_path: Path to GDP and population data.
            energy_investment_path: Path to energy investment ratio Excel file.
        """
        # Load env_vars (terminal nodes)
        if env_vars_path is None:
            env_vars_path = self.config.get_full_path('env_vars')
        if env_vars_path and env_vars_path.exists():
            with open(env_vars_path, 'rb') as f:
                env_vars = pickle.load(f)
            self.terminal_nodes = env_vars['terminal_nodes']

        # Load GDP-adjusted networks
        if gdp_adjusted_networks_path is None:
            gdp_adjusted_networks_path = self.config.get_full_path('gdp_adjusted_networks')
        if gdp_adjusted_networks_path and gdp_adjusted_networks_path.exists():
            with open(gdp_adjusted_networks_path, 'rb') as f:
                self.gdp_adjusted_networks = pickle.load(f)

        # Load GDP and population data
        if gdp_population_path is None:
            gdp_population_path = self.config.get_full_path('gdp_population')
        if gdp_population_path and gdp_population_path.exists():
            with open(gdp_population_path, 'rb') as f:
                df_dict = pickle.load(f)
            self.df_gdp = df_dict['gdp'].drop('西藏', level='地区')

        # Load energy investment ratio
        if energy_investment_path is None:
            energy_investment_path = "data/raw/能源投资占GDP比例.xlsx"
        energy_investment_path = self.config.resolve_path(energy_investment_path)
        if energy_investment_path.exists():
            self.energy_investment_ratio = pd.read_excel(
                energy_investment_path,
                index_col=0,
                usecols=['年份', '比例']
            )

    def compute_regional_average_gdp(self) -> pd.DataFrame:
        """
        Compute regional average GDP for each year.

        Returns:
            DataFrame with columns: 区域名, 年份, 年均GDP.
        """
        if self.df_gdp is None:
            raise ValueError("GDP data not loaded. Call load_data() first.")

        average_gdp = []

        for grid_name in self.df_gdp.index.get_level_values('区域名').unique():
            for year in self.df_gdp.columns:
                region_gdp = self.df_gdp.loc[grid_name, year]
                average_gdp_value = region_gdp.mean()
                average_gdp.append([grid_name, year, average_gdp_value])

        df_average_gdp = pd.DataFrame(
            average_gdp,
            columns=['grid_name', 'year', '年均GDP']
        )
        return df_average_gdp

    def compute_regional_economic_surplus(self, df_average_gdp: pd.DataFrame) -> pd.DataFrame:
        """
        Compute regional economic surplus for each region and year.

        Economic surplus = Region GDP - Regional Average GDP

        Args:
            df_average_gdp: DataFrame from compute_regional_average_gdp.

        Returns:
            DataFrame with columns: 区域名, 地区名, 年份, 经济富裕度.
        """
        if self.df_gdp is None:
            raise ValueError("GDP data not loaded. Call load_data() first.")

        economic_surplus = []

        for grid_name in self.df_gdp.index.get_level_values('区域名').unique():
            df_average_gdp_region = df_average_gdp[
                df_average_gdp['grid_name'] == grid_name
            ]

            for year in self.df_gdp.columns:
                for region in self.df_gdp.loc[grid_name].index:
                    region_gdp = self.df_gdp.loc[(grid_name, region), year]
                    average_gdp_value = df_average_gdp_region[
                        df_average_gdp_region['year'] == year
                    ]['年均GDP'].values[0]
                    surplus_value = region_gdp - average_gdp_value
                    economic_surplus.append([grid_name, region, year, surplus_value])

        df_economic_surplus = pd.DataFrame(
            economic_surplus,
            columns=['grid_name', 'region', 'year', '经济富裕度']
        )
        return df_economic_surplus

    def compute_regional_energy_consumption(self) -> pd.DataFrame:
        """
        Compute regional average economic energy consumption.

        Energy consumption is calculated as the sum of flows to terminal nodes.

        Returns:
            DataFrame with columns: 区域名, 年份, 区域经济能耗平均值.
        """
        if self.gdp_adjusted_networks is None or self.terminal_nodes is None:
            raise ValueError("Network data not loaded. Call load_data() first.")

        average_energy_consumption = []

        for grid_name, years_data in self.gdp_adjusted_networks.items():
            for year, regions_data in years_data.items():
                region_energy_consumption = []
                for region, G in regions_data.items():
                    # Calculate terminal consumption
                    total_terminal_consumption = sum(
                        G[u][v]['weight']
                        for u, v in G.edges()
                        if v in self.terminal_nodes
                    )
                    region_energy_consumption.append(total_terminal_consumption)

                # Calculate regional average
                if region_energy_consumption:
                    average_consumption = sum(region_energy_consumption) / len(region_energy_consumption)
                else:
                    average_consumption = 0
                average_energy_consumption.append([grid_name, year, average_consumption])

        df_average_energy = pd.DataFrame(
            average_energy_consumption,
            columns=['grid_name', 'year', '区域经济能耗平均值']
        )
        return df_average_energy

    def compute_total_energy_surplus(
        self,
        df_economic_surplus: pd.DataFrame,
        df_average_energy: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute total energy surplus (economic purchasing power).

        Total Energy Surplus = Economic Surplus × Average Energy Consumption × Investment Ratio

        Args:
            df_economic_surplus: DataFrame from compute_regional_economic_surplus.
            df_average_energy: DataFrame from compute_regional_energy_consumption.

        Returns:
            DataFrame with columns: 区域名, 地区名, 年份, 总经济能耗富裕度.
        """
        if self.energy_investment_ratio is None:
            raise ValueError("Investment ratio data not loaded. Call load_data() first.")

        total_energy_surplus = []

        for grid_name, regions_data in df_economic_surplus.groupby('grid_name'):
            df_average_region_energy = df_average_energy[
                df_average_energy['grid_name'] == grid_name
            ]

            for region, df_region in regions_data.groupby('region'):
                for year in df_region['year'].values:
                    region_surplus = df_region.loc[
                        df_region['year'] == year
                    ]['经济富裕度'].values[0]

                    # Check if year exists in average energy data
                    avg_energy_filtered = df_average_region_energy['year'] == year
                    if avg_energy_filtered.sum() == 0:
                        continue  # Skip if no matching year

                    average_energy = df_average_region_energy.loc[
                        avg_energy_filtered, '区域经济能耗平均值'].values[0]

                    energy_ratio = self.energy_investment_ratio.loc[year].values[0]

                    total_surplus = region_surplus * average_energy * energy_ratio
                    total_energy_surplus.append([grid_name, region, year, total_surplus])

        df_total_energy_surplus = pd.DataFrame(
            total_energy_surplus,
            columns=['grid_name', 'region', 'year', '总经济能耗富裕度']
        )
        return df_total_energy_surplus

    def compute_all_indicators(self, save_path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Compute all economy-based resilience indicators.

        Args:
            save_path: Optional path to save results as Excel file.

        Returns:
            Dictionary with DataFrames for each indicator.
        """
        # Check data loaded
        if self.df_gdp is None:
            raise ValueError("GDP data not loaded. Call load_data() first.")
        if self.gdp_adjusted_networks is None or self.terminal_nodes is None:
            raise ValueError("Network data not loaded. Call load_data() first.")

        # Part 1: Regional average GDP
        df_average_gdp = self.compute_regional_average_gdp()

        # Part 2: Regional economic surplus
        df_economic_surplus = self.compute_regional_economic_surplus(df_average_gdp)

        # Part 3: Regional energy consumption
        df_average_energy = self.compute_regional_energy_consumption()

        # Part 4: Total energy surplus
        df_total_energy_surplus = self.compute_total_energy_surplus(
            df_economic_surplus, df_average_energy
        )

        results = {
            'regional_average_gdp': df_average_gdp,
            'regional_economic_surplus': df_economic_surplus,
            'regional_energy_consumption': df_average_energy,
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
        df_average_gdp_pivot = results['regional_average_gdp'].pivot(
            index='grid_name', columns='year', values='年均GDP'
        )

        df_economic_surplus_pivot = results['regional_economic_surplus'].pivot(
            index=['grid_name', 'region'], columns='year', values='经济富裕度'
        )

        df_average_energy_pivot = results['regional_energy_consumption'].pivot(
            index='grid_name', columns='year', values='区域经济能耗平均值'
        )

        df_total_energy_surplus_pivot = results['total_energy_surplus'].pivot(
            index=['grid_name', 'region'], columns='year', values='总经济能耗富裕度'
        )

        return {
            'average_gdp': df_average_gdp_pivot,
            'economic_surplus': df_economic_surplus_pivot,
            'average_energy': df_average_energy_pivot,
            'total_energy_surplus': df_total_energy_surplus_pivot
        }
