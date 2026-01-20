# -*- coding: utf-8 -*-
"""
Main pipeline script for Urban Energy Resilience analysis.
城市能源韧性分析主流程脚本

This script provides a unified entry point for running all analysis
modules in the correct order.

Usage:
    python scripts/run_pipeline.py [OPTIONS]

Options:
    --level LEVEL         Resilience level: 1, 2, 3, or all (default: all)
    --year YEAR          Specific year to analyze (can be specified multiple times)
    --grid GRID          Specific grid name to analyze
    --region REGION      Specific region name to analyze
    --output PATH        Output directory for results
    --verbose            Print detailed progress information
    --dry-run           Print steps without executing
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing import NetworkBuilder, NetworkStats
from src.network_analysis import (
    CICalculator,
    NCIIndexCalculator,
    NetworkMetrics,
    compute_network_summary_dataframe
)
from src.resilience import EconomyResilience, PopulationResilience, StructureResilience
from src.attack_simulation import AttackRecoverySimulator


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    print(f"\n{char * 60}")
    print(f"  {text}")
    print(f"{char * 60}\n")


def print_step(text: str, step_num: int):
    """Print a formatted step."""
    print(f"Step {step_num}: {text}")


def print_info(text: str):
    """Print info message."""
    print(f"[INFO] {text}")


def print_success(text: str):
    """Print a success message."""
    print(f"[OK] {text}")


class Pipeline:
    """
    Main pipeline for Urban Energy Resilience analysis.

    This class coordinates the execution of all analysis modules
    in the correct order and with proper error handling.

    Attributes:
        config: Configuration settings.
        verbose: Whether to print detailed information.
        dry_run: Whether to print steps without executing.
    """

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        """
        Initialize the pipeline.

        Args:
            verbose: Print detailed progress information.
            dry_run: Print steps without executing.
        """
        from src.preprocessing import get_config
        self.config = get_config()
        self.verbose = verbose
        self.dry_run = dry_run

    def run_preprocessing(self) -> None:
        """
        Run preprocessing steps.
        """
        print_step("Preprocessing - Loading network data", 1)

        if not self.dry_run:
            builder = NetworkBuilder()
            networks = builder.load_networks("data/raw/all_networks.pkl")

            grids = builder.get_available_grids()
            years_per_grid = {g: len(builder.get_available_years(g)) for g in grids}
            regions_per_year_grid = sum(
                len(builder.get_available_regions(g, y))
                for g in grids
                for y in years_per_grid[g]
            )

            print_info(f"Loaded {len(grids)} grids, {regions_per_year_grid} network instances")
        else:
            print_info("[DRY RUN] Would load networks from data/raw/all_networks.pkl")

        print_success("Preprocessing completed")

    def run_network_analysis(
        self,
        year: Optional[int] = None
    ) -> None:
        """
        Run network analysis: CI and NCI calculation.

        Args:
            year: Specific year to analyze, None for all years.
        """
        print_step("Network Analysis - Computing CI and NCI", 2)

        if not self.dry_run:
            # Load networks
            builder = NetworkBuilder()
            networks = builder.load_networks("data/raw/all_networks.pkl")

            # Filter by year if specified
            if year is not None:
                filtered_networks = {}
                for grid_name, years_data in networks.items():
                    if year in years_data:
                        filtered_networks[grid_name] = {year: years_data[year]}
                networks = filtered_networks
                print_info(f"Analyzing year {year} only")

            # Load node categories
            import pickle
            with open("data/raw/env_vars.pkl", 'rb') as f:
                env_vars = pickle.load(f)

            node_categories = {
                'Primary Energy': env_vars['primary_energy_nodes'],
                'Processing': env_vars['processing_nodes'],
                'Terminal': env_vars['terminal_nodes']
            }

            # Compute CI
            ci_calculator = CICalculator()
            ci_results = ci_calculator.compute_CI_for_all_networks(
                networks, node_categories, verbose=self.verbose
            )
            print_info(f"Computed CI for {len(ci_results['primary'])} network instances")

            # Save CI results
            self._save_ci_results(ci_results)

            # Compute NCI
            nci_calculator = NCIIndexCalculator()
            nci_results = nci_calculator.compute_NCI_for_all_networks(
                networks, verbose=self.verbose
            )
            print_info(f"Computed NCI for {len(nci_results['summary'])} network instances")

            # Save NCI results
            self._save_nci_results(nci_results)

        else:
            print_info("[DRY RUN] Would compute CI and NCI")
            if year:
                print_info(f"[DRY RUN] Year filter: {year}")

        print_success("Network analysis completed")

    def run_resilience_analysis(
        self,
        levels: str = "all"
    ) -> None:
        """
        Run resilience analysis for specified levels.

        Args:
            levels: Resilience levels to compute: "1", "2", "3", or "all".
        """
        levels = levels.lower()

        if levels == "all":
            print_step("Resilience Analysis - All Levels (1, 2, 3)", 3)
        elif levels == "1":
            print_step("Resilience Analysis - Level 1 (Economy)", 3)
        elif levels == "2":
            print_step("Resilience Analysis - Level 2 (Population)", 3)
        elif levels == "3":
            print_step("Resilience Analysis - Level 3 (Structure)", 3)
        else:
            print(f"Invalid level: {levels}")
            return

        if not self.dry_run:
            # Load networks
            builder = NetworkBuilder()
            networks = builder.load_networks("data/raw/all_networks.pkl")

            # Level 1: Economy
            if levels in ["all", "1"]:
                print_info("Computing Level 1 indicators...")
                econ_calc = EconomyResilience()
                econ_calc.load_data()
                econ_results = econ_calc.compute_all_indicators()
                print_info(f"Computed {len(econ_results)} economy indicators")
                # Save results
                self._save_resilience_results(econ_results, "level1_economy")

            # Level 2: Population
            if levels in ["all", "2"]:
                print_info("Computing Level 2 indicators...")
                pop_calc = PopulationResilience()
                pop_calc.load_data()
                pop_results = pop_calc.compute_all_indicators()
                print_info(f"Computed {len(pop_results)} population indicators")
                # Save results
                self._save_resilience_results(pop_results, "level2_population")

            # Level 3: Structure
            if levels in ["all", "3"]:
                print_info("Computing Level 3 indicators...")
                struct_calc = StructureResilience()
                struct_calc.load_node_categories()
                ci_results = struct_calc.compute_average_CI_for_all_networks(
                    networks, verbose=self.verbose
                )
                print_info(f"Computed {len(ci_results)} structure indicators")
                # Save results
                self._save_ci_results(ci_results, "level3_structure")

        else:
            print_info(f"[DRY RUN] Would compute resilience levels: {levels}")

        print_success("Resilience analysis completed")

    def run_attack_recovery(
        self,
        num_simulations: int = 100,
        drop_ratio: float = 0.3,
        n_workers: int = 4
    ) -> None:
        """
        Run attack-recovery simulation.

        Args:
            num_simulations: Number of bootstrap iterations.
            drop_ratio: Proportion of edges to remove.
            n_workers: Number of parallel workers.
        """
        print_step("Attack-Recovery Simulation", 4)

        if not self.dry_run:
            from src.attack_simulation import run_parallel_attack_recovery

            # Load networks
            builder = NetworkBuilder()
            networks = builder.load_networks("data/raw/all_networks.pkl")

            # Output directory
            output_dir = "outputs/attack_recovery"

            # Run simulation
            print_info(f"Running {num_simulations} simulations per network...")
            print_info(f"Using {n_workers} parallel workers...")

            run_parallel_attack_recovery(
                all_networks=networks,
                num_bootstrap=num_simulations,
                drop_ratio=drop_ratio,
                max_workers=n_workers,
                save_path=output_dir,
                verbose=self.verbose
            )

            print_info(f"Results saved to {output_dir}")

        else:
            print_info("[DRY RUN] Would run attack-recovery simulation")
            print_info(f"[DRY RUN] Simulations: {num_simulations}")
            print_info(f"[DRY RUN] Drop ratio: {drop_ratio}")
            print_info(f"[DRY RUN] Workers: {n_workers}")

        print_success("Attack-recovery simulation completed")

    def _save_ci_results(
        self,
        ci_results: dict,
        output_name: str = "ci_results"
    ) -> None:
        """Save CI calculation results to Excel."""
        import pandas as pd

        output_dir = Path("outputs/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{output_name}.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            ci_results['primary'].to_excel(writer, sheet_name='Primary_Energy_CI')
            ci_results['processing'].to_excel(writer, sheet_name='Processing_CI')
            ci_results['terminal'].to_excel(writer, sheet_name='Terminal_CI')

        print_info(f"Saved CI results to {output_file}")

    def _save_nci_results(
        self,
        nci_results: dict,
        output_name: str = "nci_results"
    ) -> None:
        """Save NCI calculation results to Excel."""
        import pandas as pd

        output_dir = Path("outputs/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{output_name}.xlsx"

        nci_results['summary'].to_excel(output_file, index=False)

        print_info(f"Saved NCI results to {output_file}")

    def _save_resilience_results(
        self,
        results: dict,
        prefix: str = ""
    ) -> None:
        """Save resilience results to Excel."""
        import pandas as pd

        output_dir = Path("outputs/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        for name, df in results.items():
            output_file = output_dir / f"{prefix}_{name}.xlsx"
            df.to_excel(output_file)
            print_info(f"Saved {name} to {output_file}")

    def run_all(self, levels: str = "all") -> None:
        """
        Run the complete pipeline.

        Args:
            levels: Resilience levels to compute.
        """
        print_header("Urban Energy Resilience Analysis Pipeline")

        # Step 1: Preprocessing
        self.run_preprocessing()

        # Step 2: Network Analysis (always run with CI and NCI)
        self.run_network_analysis()

        # Step 3: Resilience Analysis
        if levels:
            self.run_resilience_analysis(levels)

        print_header("Pipeline Completed Successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Urban Energy Resilience Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python scripts/run_pipeline.py

  # Run only Level 1 resilience
  python scripts/run_pipeline.py --level 1

  # Run specific year
  python scripts/run_pipeline.py --year 2010

  # Dry run to see steps
  python scripts/run_pipeline.py --dry-run
        """
    )

    parser.add_argument(
        '--level',
        choices=['1', '2', '3', 'all'],
        default='all',
        help='Resilience level to compute (default: all)'
    )

    parser.add_argument(
        '--year',
        type=int,
        action='append',
        help='Specific year to analyze (can be specified multiple times)'
    )

    parser.add_argument(
        '--grid',
        type=str,
        help='Specific grid name to analyze'
    )

    parser.add_argument(
        '--region',
        type=str,
        help='Specific region name to analyze'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='Output directory for results'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print steps without executing'
    )

    parser.add_argument(
        '--attack-recovery',
        action='store_true',
        help='Run attack-recovery simulation'
    )

    parser.add_argument(
        '--n-simulations',
        type=int,
        default=100,
        help='Number of bootstrap simulations (default: 100)'
    )

    parser.add_argument(
        '--drop-ratio',
        type=float,
        default=0.3,
        help='Edge removal ratio (default: 0.3)'
    )

    parser.add_argument(
        '--n-workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )

    args = parser.parse_args()

    # Create pipeline
    pipeline = Pipeline(verbose=args.verbose, dry_run=args.dry_run)

    # Run pipeline
    if args.attack_recovery:
        pipeline.run_attack_recovery(
            num_simulations=args.n_simulations,
            drop_ratio=args.drop_ratio,
            n_workers=args.n_workers
        )
    else:
        pipeline.run_all(levels=args.level)


if __name__ == "__main__":
    main()
