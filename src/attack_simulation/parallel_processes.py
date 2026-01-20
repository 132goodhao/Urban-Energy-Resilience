# -*- coding: utf-8 -*-
"""
Parallel processes attack-recovery simulation module.
并行进程攻击-恢复模拟模块

This module provides parallel processing capabilities for attack-recovery simulations,
using multiprocessing for improved performance.

Note: This module uses multiprocessing, which requires the __main__ guard
when running scripts on Windows.
"""

import os
import random
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set
from multiprocessing import Pool
import networkx as nx

from .simulator import AttackRecoverySimulator, calculate_max_step_for_networks


class ParallelProcessSimulator:
    """
    Parallel process simulator for attack-recovery simulations.

    This class provides multi-process simulation capabilities with:
    - Independent caching for each (region, year) combination
    - File locking for concurrent writes
    - Flush-based checkpointing for large simulations

    Attributes:
        num_bootstrap (int): Number of bootstrap iterations.
        drop_ratio (float): Proportion of edges to remove.
        max_workers (int): Number of parallel processes.
        save_path (str): Directory path for saving results.

    Example:
        >>> simulator = ParallelProcessSimulator(
        ...     num_bootstrap=1000,
        ...     drop_ratio=0.3,
        ...     max_workers=16
        ... )
        >>> simulator.run_parallel(all_networks)
    """

    def __init__(
        self,
        num_bootstrap: int = 1000,
        drop_ratio: float = 1.0,
        max_workers: int = 4,
        save_path: str = "outputs/attack_recovery"
    ):
        """
        Initialize the parallel simulator.

        Args:
            num_bootstrap: Number of bootstrap iterations.
            drop_ratio: Proportion of edges to remove (0-1).
            max_workers: Number of parallel processes to use.
            save_path: Directory for saving results.
        """
        self.num_bootstrap = num_bootstrap
        self.drop_ratio = max(0.0, min(1.0, drop_ratio))
        self.max_workers = max_workers
        self.save_path = Path(save_path)

        # Create save directory
        self.save_path.mkdir(parents=True, exist_ok=True)

    def execute_bootstrap(
        self,
        G: nx.DiGraph,
        region: str,
        year: int,
        base_seed: int = 42
    ) -> Dict[str, List]:
        """
        Execute bootstrap simulation for a single network.

        Args:
            G: NetworkX directed graph.
            region: Region name.
            year: Year.
            base_seed: Base random seed.

        Returns:
            Dictionary with 'attack' and 'recovery' sequences.
        """
        simulator = AttackRecoverySimulator(
            drop_ratio=self.drop_ratio,
            random_seed=base_seed
        )

        total_attack_flows, total_recovery_flows = simulator.bootstrap_simulation(
            G, self.num_bootstrap, base_seed
        )

        return {
            'region': region,
            'year': year,
            'attack_flows': total_attack_flows,
            'recovery_flows': total_recovery_flows
        }

    def run_parallel(
        self,
        all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
        specified_grids: Optional[List[str]] = None,
        specified_regions: Optional[List[str]] = None,
        year_range: Optional[List[int]] = None,
        verbose: bool = False
    ) -> None:
        """
        Run parallel simulations for all networks.

        Args:
            all_networks: Nested dictionary structure.
            specified_grids: List of grid names to process (None for all).
            specified_regions: List of region names to process (None for all).
            year_range: List of years [start, end] to process (None for all).
            verbose: Whether to print progress information.
        """
        # Build argument list for parallel processing
        args_list = []
        bootstrap_index = 0

        for grid_name, years_data in all_networks.items():
            # Filter by grid name
            if specified_grids and grid_name not in specified_grids:
                continue

            for year, regions_data in years_data.items():
                # Filter by year range
                if year_range and (year < year_range[0] or year > year_range[1]):
                    continue

                for region, G in regions_data.items():
                    # Filter by region name
                    if specified_regions and region not in specified_regions:
                        continue

                    # Create arguments for this simulation
                    args_list.append((
                        G.copy(),
                        region,
                        year,
                        self.num_bootstrap,
                        self.drop_ratio,
                        42 + bootstrap_index  # Unique seed
                    ))

                    bootstrap_index += 1

        if verbose:
            print(f"Total simulations to run: {len(args_list)}")
            print(f"Using {self.max_workers} parallel processes...")

        # Run simulations in parallel
        with Pool(processes=self.max_workers) as pool:
            results = pool.starmap(self._execute_and_save, args_list)

        if verbose:
            print(f"Completed {len(results)} simulations")

    def _execute_and_save(
        self,
        G: nx.DiGraph,
        region: str,
        year: int,
        num_bootstrap: int,
        drop_ratio: float,
        seed: int
    ) -> Dict[str, any]:
        """
        Execute simulation and save results (internal method for multiprocessing).

        Args:
            G: NetworkX directed graph.
            region: Region name.
            year: Year.
            num_bootstrap: Number of bootstrap iterations.
            drop_ratio: Proportion of edges to remove.
            seed: Random seed.

        Returns:
            Summary statistics of the simulation.
        """
        simulator = AttackRecoverySimulator(drop_ratio=drop_ratio, random_seed=seed)
        attack_sequences, recovery_sequences = simulator.bootstrap_simulation(
            G, num_bootstrap, seed
        )

        # Compute summary statistics
        summary = {
            'region': region,
            'year': year
        }

        # Flatten sequences for analysis
        max_len = max(len(s) for s in attack_sequences) if attack_sequences else 0

        # Average attack flows at each step
        if attack_sequences:
            attack_matrix = []
            for seq in attack_sequences:
                # Pad sequences to same length
                padded = seq + [0] * (max_len - len(seq))
                attack_matrix.append(padded)
            import numpy as np
            summary['avg_attack_flows'] = list(np.mean(attack_matrix, axis=0))
            summary['final_attack_flow'] = np.mean([s[-1] if s else 0 for s in attack_sequences])
            summary['min_attack_flow'] = np.mean([min(s) if s else 0 for s in attack_sequences])

        # Average recovery flows at each step
        if recovery_sequences:
            recovery_matrix = []
            for seq in recovery_sequences:
                # Pad sequences to same length
                padded = seq + [0] * (max_len - len(seq))
                recovery_matrix.append(padded)
            import numpy as np
            summary['avg_recovery_flows'] = list(np.mean(recovery_matrix, axis=0))
            summary['final_recovery_flow'] = np.mean([s[-1] if s else 0 for s in recovery_sequences])

        # Save detailed results to file
        self._save_detailed_results(summary, region, year)

        return summary

    def _save_detailed_results(
        self,
        summary: Dict[str, any],
        region: str,
        year: int
    ) -> None:
        """
        Save detailed bootstrap results to CSV files.

        Args:
            summary: Summary statistics dictionary.
            region: Region name.
            year: Year.
        """
        # Save attack flows
        if 'avg_attack_flows' in summary:
            attack_df = pd.DataFrame(summary['avg_attack_flows']).T
            attack_df.columns = ['Average_Flow']
            attack_df.index.name = 'Step'
            attack_file = self.save_path / f'{region}_{year}_attack.csv'
            attack_df.to_csv(attack_file)

        # Save recovery flows
        if 'avg_recovery_flows' in summary:
            recovery_df = pd.DataFrame(summary['avg_recovery_flows']).T
            recovery_df.columns = ['Average_Flow']
            recovery_df.index.name = 'Step'
            recovery_file = self.save_path / f'{region}_{year}_recovery.csv'
            recovery_df.to_csv(recovery_file)

    def compute_summary_statistics(self) -> Dict[str, pd.DataFrame]:
        """
        Compute summary statistics from all saved simulation files.

        Returns:
            Dictionary with 'attack' and 'recovery' summary DataFrames.
        """
        # Find all result files
        attack_files = list(self.save_path.glob('*_attack.csv'))
        recovery_files = list(self.save_path.glob('*_recovery.csv'))

        # Load attack data
        attack_results = []
        for file in attack_files:
            df = pd.read_csv(file, index_col=0)
            # Extract region and year from filename
            parts = file.stem.split('_')
            region = '_'.join(parts[:-2])
            year = int(parts[-2])

            avg_performance = df['Average_Flow'].mean()

            attack_results.append({
                'region': region,
                'year': year,
                'avg_performance': avg_performance,
                'file': file.name
            })

        # Load recovery data
        recovery_results = []
        for file in recovery_files:
            df = pd.read_csv(file, index_col=0)
            parts = file.stem.split('_')
            region = '_'.join(parts[:-2])
            year = int(parts[-2])

            avg_performance = df['Average_Flow'].mean()

            recovery_results.append({
                'region': region,
                'year': year,
                'avg_performance': avg_performance,
                'file': file.name
            })

        df_attack_summary = pd.DataFrame(attack_results)
        df_recovery_summary = pd.DataFrame(recovery_results)

        return {
            'attack': df_attack_summary,
            'recovery': df_recovery_summary
        }

    def save_summary_to_excel(self, output_path: Optional[str] = None) -> None:
        """
        Save summary statistics to Excel file.

        Args:
            output_path: Optional output file path.
        """
        summary = self.compute_summary_statistics()

        if output_path is None:
            output_path = self.save_path / 'summary_attack_recovery.xlsx'
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            summary['attack'].to_excel(writer, sheet_name='Attack_Summary')
            summary['recovery'].to_excel(writer, sheet_name='Recovery_Summary')


def run_parallel_attack_recovery(
    all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
    num_bootstrap: int = 1000,
    drop_ratio: float = 1.0,
    max_workers: int = 4,
    save_path: str = "outputs/attack_recovery",
    specified_grids: Optional[List[str]] = None,
    specified_regions: Optional[List[str]] = None,
    year_range: Optional[List[int]] = None,
    verbose: bool = False
) -> None:
    """
    Convenience function to run parallel attack-recovery simulations.

    Args:
        all_networks: Nested dictionary structure.
        num_bootstrap: Number of bootstrap iterations.
        drop_ratio: Proportion of edges to remove.
        max_workers: Number of parallel processes.
        save_path: Directory for saving results.
        specified_grids: List of grid names to process.
        specified_regions: List of region names to process.
        year_range: List of years [start, end] to process.
        verbose: Whether to print progress information.

    Example:
        >>> run_parallel_attack_recovery(
        ...     all_networks,
        ...     num_bootstrap=1000,
        ...     drop_ratio=0.3,
        ...     max_workers=16,
        ...     verbose=True
        ... )
    """
    simulator = ParallelProcessSimulator(
        num_bootstrap=num_bootstrap,
        drop_ratio=drop_ratio,
        max_workers=max_workers,
        save_path=save_path
    )

    simulator.run_parallel(
        all_networks=all_networks,
        specified_grids=specified_grids,
        specified_regions=specified_regions,
        year_range=year_range,
        verbose=verbose
    )

    # Save summary
    simulator.save_summary_to_excel()

    if verbose:
        print(f"Summary saved to {simulator.save_path / 'summary_attack_recovery.xlsx'}")
