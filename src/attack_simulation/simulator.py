# -*- coding: utf-8 -*-
"""
Attack-Recovery Simulator module.
攻击-恢复模拟模块

This module provides functionality for simulating random attacks and recovery
on energy networks using the bootstrap method.

The simulation follows these steps:
1. Randomly remove edges (attack phase)
2. Gradually restore edges (recovery phase)
3. Measure energy flow at each step
"""

from typing import Dict, List, Optional, Tuple, Set
import random
import networkx as nx


class AttackRecoverySimulator:
    """
    Simulator for random attack and recovery on energy networks.

    This class implements a bootstrap-based simulation that:
    - Randomly removes edges (attack)
    - Measures flow degradation
    - Gradually restores edges (recovery)
    - Measures flow recovery

    Attributes:
        random_seed (Optional[int]): Seed for random number generation.
        drop_ratio (float): Proportion of edges to remove (0-1).

    Example:
        >>> simulator = AttackRecoverySimulator(drop_ratio=0.3, seed=42)
        >>> edges_removed, attack_flows, recovery_flows = simulator.simulate(G)
    """

    def __init__(self, drop_ratio: float = 1.0, random_seed: Optional[int] = None):
        """
        Initialize the simulator.

        Args:
            drop_ratio: Proportion of edges to remove (0 to 1).
            random_seed: Random seed for reproducibility.
        """
        self.drop_ratio = max(0.0, min(1.0, drop_ratio))
        self.random_seed = random_seed
        self.rng = random.Random(random_seed)

    def calculate_total_energy_flow(self, G: nx.DiGraph) -> float:
        """
        Calculate the total energy flow in a network.

        Args:
            G: NetworkX directed graph.

        Returns:
            Sum of absolute edge weights.
        """
        return sum(abs(d.get('weight', 1.0)) for _, _, d in G.edges(data=True))

    def update_energy_flow_recursive(
        self,
        G: nx.DiGraph,
        u: str,
        v: str,
        visited_edges: Optional[Set[Tuple[str, str]]] = None
    ) -> bool:
        """
        Update energy flow to simulate edge removal, recursively affecting downstream.

        This function propagates the effect of edge (u, v) removal
        through the network, adjusting weights of downstream edges.

        Args:
            G: NetworkX directed graph.
            u: Source node.
            v: Target node.
            visited_edges: Set of already visited edges to prevent cycles.

        Returns:
            True if the removal triggered further updates, False otherwise.
        """
        if visited_edges is None:
            visited_edges = set()

        # Skip if already visited (prevent cycles)
        if (u, v) in visited_edges:
            return False
        visited_edges.add((u, v))

        # Skip if edge doesn't exist
        if not G.has_edge(u, v):
            return False

        # Remove edge and record its weight
        removed_weight = G[u][v]['weight']
        G.remove_edge(u, v)

        # Update inflow to node v
        in_edges_v = G.in_edges(v, data=True)
        new_in_flow_v = sum(data['weight'] for _, _, data in in_edges_v)

        # If node v has no inflow, remove all its outgoing edges
        if new_in_flow_v == 0:
            out_edges_v = list(G.out_edges(v, data=True))
            for _, target, _ in out_edges_v:
                self.update_energy_flow_recursive(G, v, target, visited_edges)
            return True

        # Otherwise, distribute the removed weight proportionally to outgoing edges
        out_edges_v = list(G.out_edges(v, data=True))
        if not out_edges_v:
            return False

        total_out_weight = sum(d['weight'] for _, _, d in out_edges_v)

        if total_out_weight > 0:
            for _, target, data in out_edges_v:
                weight_reduction = removed_weight * (data['weight'] / total_out_weight)
                data['weight'] -= weight_reduction
                # Recursively update downstream
                self.update_energy_flow_recursive(G, v, target, visited_edges)

        return False

    def random_attack_and_recovery(
        self,
        G: nx.DiGraph,
        random_seed: Optional[int] = None
    ) -> Tuple[List, List[float], List[float]]:
        """
        Execute random attack and recovery simulation.

        Args:
            G: NetworkX directed graph (will be copied, not modified).
            random_seed: Optional random seed for this simulation.

        Returns:
            Tuple of:
            - edges_to_remove: List of edges that were removed
            - attack_flows: List of normalized flow values during attack
            - recovery_flows: List of normalized flow values during recovery
        """
        # Use provided seed or default
        rng = self.rng if random_seed is None else random.Random(random_seed)

        # Create a copy to avoid modifying original
        G_sim = G.copy()

        # Calculate initial flow
        initial_energy_flow = self.calculate_total_energy_flow(G_sim)
        total_edges = list(G_sim.edges(data=True))
        num_edges_to_drop = int(len(total_edges) * self.drop_ratio)

        # Randomly select edges to remove
        edges_to_remove = rng.sample(total_edges, num_edges_to_drop)

        attack_flows = []
        recovery_flows = []
        visited_edges = set()

        # Attack phase: Remove edges and measure flow
        for edge in edges_to_remove:
            # Update flow considering downstream effects
            self.update_energy_flow_recursive(G_sim, edge[0], edge[1], visited_edges)
            total_flow = self.calculate_total_energy_flow(G_sim)
            attack_flows.append(total_flow / initial_energy_flow)

        # Recovery phase: Restore edges and measure flow
        for edge in edges_to_remove:
            G_sim.add_edge(edge[0], edge[1], weight=edge[2]['weight'])
            total_flow = self.calculate_total_energy_flow(G_sim)
            recovery_flows.append(total_flow / initial_energy_flow)

        return edges_to_remove, attack_flows, recovery_flows

    def bootstrap_simulation(
        self,
        G: nx.DiGraph,
        num_bootstrap: int = 10,
        base_seed: Optional[int] = None
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Run multiple bootstrap simulations.

        Args:
            G: NetworkX directed graph.
            num_bootstrap: Number of bootstrap iterations.
            base_seed: Base seed for reproducibility.

        Returns:
            Tuple of:
            - total_attack_flows: List of attack flow sequences
            - total_recovery_flows: List of recovery flow sequences
        """
        total_attack_flows = []
        total_recovery_flows = []

        for i in range(num_bootstrap):
            # Generate seed for each bootstrap iteration
            if base_seed is not None:
                seed = base_seed + i
            else:
                seed = None

            _, attack_flows, recovery_flows = self.random_attack_and_recovery(
                G.copy(), seed
            )

            total_attack_flows.append(attack_flows)
            total_recovery_flows.append(recovery_flows)

        return total_attack_flows, total_recovery_flows

    def compute_resilience_metrics(
        self,
        attack_flows: List[float],
        recovery_flows: List[float]
    ) -> Dict[str, float]:
        """
        Compute resilience metrics from flow sequences.

        Args:
            attack_flows: Normalized flow values during attack phase.
            recovery_flows: Normalized flow values during recovery phase.

        Returns:
            Dictionary with resilience metrics.
        """
        if not attack_flows:
            return {}

        import numpy as np

        # Attack phase metrics
        min_attack_flow = min(attack_flows)
        final_attack_flow = attack_flows[-1]

        # Recovery phase metrics
        if recovery_flows:
            final_recovery_flow = recovery_flows[-1]
            recovery_speed = (
                (final_recovery_flow - final_attack_flow) / len(recovery_flows)
                if len(recovery_flows) > 0 else 0
            )
        else:
            final_recovery_flow = final_attack_flow
            recovery_speed = 0

        return {
            'min_attack_flow': min_attack_flow,
            'final_attack_flow': final_attack_flow,
            'final_recovery_flow': final_recovery_flow,
            'attack_phase_resilience': 1 - (1 - min_attack_flow),
            'recovery_efficiency': final_recovery_flow,
            'recovery_speed': recovery_speed,
            'overall_resilience': (
                (min_attack_flow + final_recovery_flow) / 2
            )
        }

    def simulate_and_compute_metrics(
        self,
        G: nx.DiGraph,
        num_bootstrap: int = 10,
        base_seed: Optional[int] = None
    ) -> Dict[str, List[float]]:
        """
        Run bootstrap simulations and compute aggregate metrics.

        Args:
            G: NetworkX directed graph.
            num_bootstrap: Number of bootstrap iterations.
            base_seed: Base seed for reproducibility.

        Returns:
            Dictionary with average values of each metric across bootstrap iterations.
        """
        attack_sequences, recovery_sequences = self.bootstrap_simulation(
            G, num_bootstrap, base_seed
        )

        # Compute metrics for each bootstrap iteration
        metrics_lists = {}
        for attack_flows, recovery_flows in zip(
            attack_sequences, recovery_sequences
        ):
            metrics = self.compute_resilience_metrics(
                attack_flows, recovery_flows
            )
            for key, value in metrics.items():
                if key not in metrics_lists:
                    metrics_lists[key] = []
                metrics_lists[key].append(value)

        # Compute averages
        return {key: np.mean(values) for key, values in metrics_lists.items()}

    def calculate_max_step(self, G: nx.DiGraph) -> int:
        """
        Calculate the maximum number of steps for the simulation.

        This equals the number of edges that would be removed.

        Args:
            G: NetworkX directed graph.

        Returns:
            Number of simulation steps.
        """
        return int(len(G.edges) * self.drop_ratio)


def calculate_max_step_for_networks(
    all_networks: Dict[str, Dict[int, Dict[str, nx.DiGraph]]],
    drop_ratio: float = 1.0
) -> int:
    """
    Calculate the maximum number of steps across all networks.

    Args:
        all_networks: Nested dictionary structure.
        drop_ratio: Proportion of edges to remove.

    Returns:
        Maximum number of steps needed.
    """
    max_step = 0

    for grid_name, years_data in all_networks.items():
        for year, regions_data in years_data.items():
            for region, G in regions_data.items():
                num_edges_to_drop = int(len(G.edges) * drop_ratio)
                max_step = max(max_step, num_edges_to_drop)

    return max_step


def simulate_single_network(
    G: nx.DiGraph,
    num_bootstrap: int = 10,
    drop_ratio: float = 1.0,
    seed: int = 42
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Convenience function to simulate a single network.

    Args:
        G: NetworkX directed graph.
        num_bootstrap: Number of bootstrap iterations.
        drop_ratio: Proportion of edges to remove.
        seed: Random seed.

    Returns:
        Tuple of (attack_sequences, recovery_sequences).
    """
    simulator = AttackRecoverySimulator(drop_ratio=drop_ratio, random_seed=seed)
    return simulator.bootstrap_simulation(G, num_bootstrap, seed)
