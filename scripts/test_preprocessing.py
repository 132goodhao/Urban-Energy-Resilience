# -*- coding: utf-8 -*-
"""
Test script for preprocessing module.
预处理模块测试脚本

This script tests the functionality of all classes in the preprocessing module:
- ConfigLoader
- NetworkBuilder
- NetworkStats
- InterprovincialFlowAnalyzer
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing import (
    get_config,
    NetworkBuilder,
    NetworkStats,
    InterprovincialFlowAnalyzer
)


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


def test_config_loader():
    """Test ConfigLoader functionality."""
    print_header("Test 1: ConfigLoader")

    try:
        config = get_config()

        # Test getting paths
        data_dir = config.get('paths.data_dir')
        print(f"Data directory: {data_dir}")

        # Test getting study parameters
        years = config.get('study.years')
        print(f"Study years: {years}")

        # Test getting attack recovery params
        n_simulations = config.get('attack_recovery.n_simulations')
        print(f"Number of simulations: {n_simulations}")

        # Test path resolution
        full_path = config.resolve_path('data/raw/all_networks.pkl')
        print(f"Resolved path: {full_path}")

        print_success("ConfigLoader working correctly")
        return True

    except Exception as e:
        print_error(f"ConfigLoader failed: {e}")
        return False


def test_network_builder():
    """Test NetworkBuilder functionality."""
    print_header("Test 2: NetworkBuilder")

    try:
        builder = NetworkBuilder()

        # Test loading networks
        print("Loading networks...")
        networks = builder.load_networks("data/raw/all_networks.pkl")
        print(f"Networks loaded successfully")

        # Test getting available grids
        grids = builder.get_available_grids()
        print(f"Available grids ({len(grids)}): {grids}")
        print_success(f"Found {len(grids)} grids")

        # Test getting available years for first grid
        if grids:
            first_grid = grids[0]
            years = builder.get_available_years(first_grid)
            print(f"Years for '{first_grid}': {years}")

            # Test getting regions for first year
            if years:
                first_year = years[0]
                regions = builder.get_available_regions(first_grid, first_year)
                print(f"Regions for '{first_grid}' in {first_year}: {len(regions)} regions")

                # Test getting a specific network
                if regions:
                    first_region = regions[0]
                    G = builder.get_network(first_grid, first_year, first_region)
                    print(f"Got network for '{first_region}'")

                    # Test network info
                    info = builder.get_network_info(G)
                    print(f"  Nodes: {info['n_nodes']}")
                    print(f"  Edges: {info['n_edges']}")
                    print(f"  Density: {info['density']:.4f}")
                    print(f"  Weighted: {info['is_weighted']}")

        # Test filtering
        print("\nTesting filtering...")
        filtered = builder.filter_networks_by_years([2010, 2015, 2020])
        print_success(f"Filtered to years: {list(filtered[grids[0]].keys())}")

        # Test region to grid mapping
        mapping = builder.compute_region_to_grid_mapping()
        print(f"Region-to-grid mapping: {len(mapping)} regions mapped")

        print_success("NetworkBuilder working correctly")
        return True

    except Exception as e:
        print_error(f"NetworkBuilder failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_network_stats():
    """Test NetworkStats functionality."""
    print_header("Test 3: NetworkStats")

    try:
        builder = NetworkBuilder()
        networks = builder.load_networks("data/raw/all_networks.pkl")

        # Get a sample network
        grids = builder.get_available_grids()
        G = builder.get_network(grids[0], 2010, builder.get_available_regions(grids[0], 2010)[0])

        # Test total flow
        total = NetworkStats.total_flow(G)
        print(f"Total flow: {total:.2f}")

        # Test node flow
        nodes = list(G.nodes())[:3]  # Test first 3 nodes
        for node in nodes:
            stats = NetworkStats.node_flow(G, node)
            print(f"Node '{node}': inflow={stats['inflow']:.2f}, "
                  f"outflow={stats['outflow']:.2f}, net={stats['net']:.2f}")

        # Test edge summary
        edge_summary = NetworkStats.edge_summary(G)
        print(f"\nEdge summary: {len(edge_summary)} edges")
        print(edge_summary.head())

        # Test node summary
        node_summary = NetworkStats.node_summary(G)
        print(f"\nNode summary: {len(node_summary)} nodes")
        print(node_summary.head())

        print_success("NetworkStats working correctly")
        return True

    except Exception as e:
        print_error(f"NetworkStats failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_interprovincial_flows():
    """Test InterprovincialFlowAnalyzer functionality."""
    print_header("Test 4: InterprovincialFlowAnalyzer")

    try:
        analyzer = InterprovincialFlowAnalyzer()
        analyzer.load_networks("data/raw/all_networks.pkl")

        # Get a sample network to find energy nodes
        builder = analyzer.builder
        grids = builder.get_available_grids()
        G = builder.get_network(grids[0], 2010, builder.get_available_regions(grids[0], 2010)[0])

        # Find potential energy nodes (nodes with specific patterns)
        energy_nodes = [n for n in G.nodes() if "煤" in n or "油" in n or "气" in n]
        print(f"Found energy nodes: {energy_nodes[:5]}")

        if energy_nodes:
            energy_node = energy_nodes[0]
            print(f"\nTesting with energy node: '{energy_node}'")

            # Test computing energy stats
            stats = analyzer.compute_energy_stats(energy_node, years=[2010, 2015])
            print(f"\nStats for year 2010:")
            print(stats[2010].head(10))

            # Test top importers
            top_importers = analyzer.get_top_importers(energy_node, 2010, top_n=3)
            print(f"\nTop 3 importers in 2010:")
            print(top_importers)

            # Test top exporters
            top_exporters = analyzer.get_top_exporters(energy_node, 2010, top_n=3)
            print(f"\nTop 3 exporters in 2010:")
            print(top_exporters)
        else:
            print("No energy nodes found, skipping flow analysis tests")

        print_success("InterprovincialFlowAnalyzer working correctly")
        return True

    except Exception as e:
        print_error(f"InterprovincialFlowAnalyzer failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_header("Preprocessing Module Test Suite")

    results = {
        "ConfigLoader": test_config_loader(),
        "NetworkBuilder": test_network_builder(),
        "NetworkStats": test_network_stats(),
        "InterprovincialFlowAnalyzer": test_interprovincial_flows(),
    }

    # Print summary
    print_header("Test Summary")

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"{symbol} {test_name}: {status}")

    print_header("Overall Result")
    if all_passed:
        print("[OK] All tests PASSED!")
        return 0
    else:
        print("[FAIL] Some tests FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
