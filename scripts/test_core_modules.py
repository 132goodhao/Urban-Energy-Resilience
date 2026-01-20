# -*- coding: utf-8 -*-
"""
Test script for core calculation modules.
核心计算模块测试脚本

This script tests the core modules in three stages:
- Stage A: Basic network analysis (NetworkStats, NetworkMetrics)
- Stage B: Structure resilience (CI, NCI calculation)
- Stage C: Full resilience indicators (Level 1/2/3)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing import NetworkBuilder, NetworkStats
from src.network_analysis import NetworkMetrics, compute_network_summary_dataframe
from src.network_analysis import CICalculator, NCIIndexCalculator


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    print(f"\n{char * 60}")
    print(f"  {text}")
    print(f"{char * 60}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"[OK] {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"[FAIL] {text}")


def test_stage_a_basic_network_analysis() -> bool:
    """
    Stage A: Basic network analysis.

    Tests:
    - NetworkBuilder: Load networks and get info
    - NetworkStats: Compute flow statistics
    - NetworkMetrics: Compute connectivity, centrality, etc.
    """
    print_header("Stage A: Basic Network Analysis")

    try:
        # 1. Load networks
        print("Step 1: Loading networks...")
        builder = NetworkBuilder()
        networks = builder.load_networks("data/raw/all_networks.pkl")
        print_success(f"Loaded {len(builder.get_available_grids())} grids")

        # 2. Get sample network
        grids = builder.get_available_grids()
        G = builder.get_network(grids[0], 2010, builder.get_available_regions(grids[0], 2010)[0])
        info = builder.get_network_info(G)
        print(f"\nSample network info:")
        print(f"  Nodes: {info['n_nodes']}")
        print(f"  Edges: {info['n_edges']}")
        print(f"  Density: {info['density']:.4f}")
        print_success("Network info retrieved")

        # 3. Test NetworkStats
        print("\nStep 2: Testing NetworkStats...")
        metrics = NetworkMetrics()
        total_flow = metrics.compute_flow_metrics(G)['total_flow']
        print(f"  Total flow: {total_flow:.2f}")

        node_summary = NetworkStats.node_summary(G)
        print(f"  Node summary: {len(node_summary)} nodes")

        print_success("NetworkStats/NetworkMetrics working correctly")

        # 4. Test NetworkMetrics
        print("\nStep 3: Testing NetworkMetrics...")
        metrics = NetworkMetrics()

        connectivity = metrics.compute_connectivity(G)
        print(f"  Connectivity metrics:")
        print(f"    Density: {connectivity['density']:.4f}")
        print(f"    Components: {connectivity['n_components']}")

        flow_metrics = metrics.compute_flow_metrics(G)
        print(f"  Flow metrics:")
        print(f"    Total flow: {flow_metrics['total_flow']:.2f}")
        print(f"    Avg inflow: {flow_metrics['avg_inflow']:.2f}")
        print(f"    Avg outflow: {flow_metrics['avg_outflow']:.2f}")

        centrality = metrics.compute_centrality(G)
        print(f"  Centrality metrics computed for {len(centrality['in_degree_centrality'])} nodes")

        print_success("NetworkMetrics working correctly")

        # 5. Test summary dataframe
        print("\nStep 4: Testing summary DataFrame...")
        # Use a subset for testing
        test_networks = {}
        for grid_name in grids[:2]:  # First 2 grids only
            test_networks[grid_name] = {}
            for year in [2001, 2010, 2020]:  # 3 years only
                if year in networks[grid_name]:
                    test_networks[grid_name][year] = {
                        region: G
                        for region, G in list(networks[grid_name][year].items())[:5]  # First 5 regions
                    }

        summary_df = compute_network_summary_dataframe(test_networks, verbose=True)
        print_success(f"Summary DataFrame created: {len(summary_df)} rows")

        return True

    except Exception as e:
        print_error(f"Stage A failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stage_b_structure_resilience() -> bool:
    """
    Stage B: Structure resilience analysis.

    Tests:
    - CI Calculator: Compute Collective Influence
    - NCI Calculator: Compute Network Complexity Index
    - StructureResilience: Average CI by category
    """
    print_header("Stage B: Structure Resilience")

    try:
        # 1. Load networks
        print("Step 1: Loading networks...")
        builder = NetworkBuilder()
        networks = builder.load_networks("data/raw/all_networks.pkl")
        grids = builder.get_available_grids()

        # 2. Load node categories
        print("\nStep 2: Loading node categories...")
        import pickle
        env_vars_path = "data/raw/env_vars.pkl"
        with open(env_vars_path, 'rb') as f:
            env_vars = pickle.load(f)

        node_categories = {
            'Primary Energy': env_vars['primary_energy_nodes'],
            'Processing': env_vars['processing_nodes'],
            'Terminal': env_vars['terminal_nodes']
        }
        print_success(f"Loaded node categories: {list(node_categories.keys())}")

        # 3. Test CI Calculator
        print("\nStep 3: Testing CI Calculator...")
        ci_calculator = CICalculator()

        # Test with a sample network
        G = builder.get_network(grids[0], 2010, builder.get_available_regions(grids[0], 2010)[0])
        node_ci = ci_calculator.compute_all_nodes_CI(G)
        print(f"  Computed CI for {len(node_ci)} nodes")

        # Compute average CI by category
        avg_ci = ci_calculator.compute_average_CI_by_category(G, node_ci, node_categories)
        print(f"  Average CI by category:")
        for cat, val in avg_ci.items():
            print(f"    {cat}: {val:.2e}" if val else f"    {cat}: None")

        print_success("CI Calculator working correctly")

        # 4. Test CI for all networks (subset)
        print("\nStep 4: Testing CI for multiple networks...")
        test_networks = {}
        for grid_name in grids[:2]:  # First 2 grids
            test_networks[grid_name] = {}
            for year in [2001, 2010, 2020]:
                if year in networks[grid_name]:
                    test_networks[grid_name][year] = {
                        region: G
                        for region, G in list(networks[grid_name][year].items())[:5]
                    }

        ci_results = ci_calculator.compute_CI_for_all_networks(
            test_networks, node_categories, verbose=True
        )
        print_success(f"CI results computed: primary={len(ci_results['primary'])}, "
                   f"processing={len(ci_results['processing'])}, terminal={len(ci_results['terminal'])}")

        # 5. Test NCI Calculator
        print("\nStep 5: Testing NCI Calculator...")
        nci_calculator = NCIIndexCalculator()

        nci_results = nci_calculator.compute_NCI_for_all_networks(
            test_networks, verbose=True
        )
        print(f"  NCI results: {len(nci_results['summary'])} rows")
        print(f"  Indicator weights:")
        for indicator, weight in nci_results['weights'].items():
            print(f"    {indicator}: {weight:.4f}")

        print_success("NCI Calculator working correctly")

        return True

    except Exception as e:
        print_error(f"Stage B failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stage_c_full_resilience() -> bool:
    """
    Stage C: Full resilience indicators.

    Tests:
    - Level 1: Economy-based indicators
    - Level 2: Population-based indicators
    - Level 3: Structure-based indicators (with all data)
    """
    print_header("Stage C: Full Resilience Indicators")

    try:
        from src.resilience import EconomyResilience, PopulationResilience, StructureResilience

        # 1. Load networks
        print("Step 1: Loading networks...")
        builder = NetworkBuilder()
        networks = builder.load_networks("data/raw/all_networks.pkl")

        # 2. Test EconomyResilience (Level 1)
        print("\nStep 2: Testing Level 1 (Economy)...")
        econ_calc = EconomyResilience()
        econ_calc.load_data()
        print_success("EconomyResilience data loaded")

        # Note: Compute with subset to avoid long runtime
        test_networks_econ = {}
        for grid_name in list(networks.keys())[:2]:
            test_networks_econ[grid_name] = {}
            for year in [2001, 2010, 2020]:
                if year in networks[grid_name]:
                    test_networks_econ[grid_name][year] = {
                        region: G
                        for region, G in list(networks[grid_name][year].items())[:3]
                    }

        econ_calc.gdp_adjusted_networks = test_networks_econ
        econ_results = econ_calc.compute_all_indicators()
        print_success(f"Level 1 results computed: {len(econ_results)} dataframes")

        # 3. Test PopulationResilience (Level 2)
        print("\nStep 3: Testing Level 2 (Population)...")
        pop_calc = PopulationResilience()
        pop_calc.load_data()

        # Check df_pop structure and print for debugging
        if pop_calc.df_pop is not None:
            print(f"  df_pop columns: {list(pop_calc.df_pop.columns)}")
            print(f"  df_pop index levels: {pop_calc.df_pop.index.names}")

        print_success("PopulationResilience data loaded")

        pop_calc.population_adjusted_networks = test_networks_econ
        pop_results = pop_calc.compute_all_indicators()
        print_success(f"Level 2 results computed: {len(pop_results)} dataframes")

        # 4. Test StructureResilience (Level 3)
        print("\nStep 4: Testing Level 3 (Structure)...")
        struct_calc = StructureResilience()
        struct_calc.load_node_categories()
        print_success("StructureResilience data loaded")

        ci_results = struct_calc.compute_average_CI_for_all_networks(
            test_networks_econ, verbose=True
        )
        print_success(f"Level 3 results computed: {len(ci_results)} dataframes")

        # 5. Test node ranking
        print("\nStep 5: Testing node ranking...")
        G_sample = networks[list(networks.keys())[0]][2001][
            list(networks[list(networks.keys())[0]][2001].keys())[0]
        ]
        ranking_df = struct_calc.compute_node_ranking(G_sample, top_n=10)
        print(f"  Top 10 nodes by CI:")
        print(ranking_df[['rank', 'node', 'CI', 'category']].to_string(index=False))

        print_success("Node ranking computed")

        return True

    except Exception as e:
        print_error(f"Stage C failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_stage(stage: str) -> int:
    """
    Run a specific test stage.

    Args:
        stage: Stage identifier ('A', 'B', or 'C').

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if stage.upper() == 'A':
        success = test_stage_a_basic_network_analysis()
    elif stage.upper() == 'B':
        success = test_stage_b_structure_resilience()
    elif stage.upper() == 'C':
        success = test_stage_c_full_resilience()
    else:
        print(f"Unknown stage: {stage}")
        print("Valid stages: A, B, C")
        return 1

    return 0 if success else 1


def main():
    """Main entry point for the test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test core calculation modules for Urban Energy Resilience"
    )
    parser.add_argument(
        'stage',
        choices=['A', 'B', 'C'],
        help='Test stage to run (A=Basic Network, B=Structure, C=Full Resilience)'
    )

    args = parser.parse_args()

    print_header(f"Running Stage {args.stage} Test")
    exit_code = run_stage(args.stage)

    print_header("Test Summary")
    if exit_code == 0:
        print_success(f"Stage {args.stage} COMPLETED")
    else:
        print_error(f"Stage {args.stage} FAILED")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
