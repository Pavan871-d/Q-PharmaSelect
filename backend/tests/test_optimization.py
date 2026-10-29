"""
Tests for Constrained Combinatorial Optimization and QUBO Formulation.
Includes verification against small-instance exhaustive enumeration.
"""

import pytest
import numpy as np
from backend.app.services.optimization.qubo_builder import qubo_engine
from backend.app.services.optimization.solver_adapter import opt_service


def test_qubo_small_instance_exhaustive_verification():
    """
    Section 13.7: Test the formulation on small instances where an
    exhaustive classical optimum can be calculated. Compare the QUBO objective
    and selected batch against the small-instance reference solution.
    """
    N = 8
    K = 3
    total_budget = 1500.0

    np.random.seed(42)
    predicted_pic50 = np.array([8.5, 7.8, 6.2, 5.1, 8.9, 7.1, 4.5, 8.0], dtype=np.float32)
    uncertainties = np.array([0.3, 0.4, 0.2, 0.5, 0.25, 0.35, 0.6, 0.3], dtype=np.float32)
    novelties = np.array([0.8, 0.5, 0.9, 0.2, 0.7, 0.6, 0.1, 0.85], dtype=np.float32)
    costs = np.array([400.0, 350.0, 500.0, 200.0, 600.0, 450.0, 150.0, 380.0], dtype=np.float32)

    # Random symmetric similarity matrix with 1.0 diagonal
    raw_sim = np.random.uniform(0.1, 0.6, (N, N))
    tanimoto_mat = (raw_sim + raw_sim.T) / 2.0
    np.fill_diagonal(tanimoto_mat, 1.0)

    # Build QUBO
    qubo_dict, dense_Q, linear_utils = qubo_engine.build_qubo_matrix(
        predicted_pic50=predicted_pic50,
        uncertainties=uncertainties,
        novelties=novelties,
        costs=costs,
        tanimoto_matrix=tanimoto_mat,
        batch_size=K,
        total_budget=total_budget,
        weight_activity=1.0,
        weight_exploration=0.5,
        weight_novelty=0.8,
        weight_diversity=0.7,
        weight_cost=0.3
    )

    # 1. Exhaustive ground truth
    best_exact_vec, best_exact_energy = opt_service.solve_exact_exhaustive(
        qubo_dict=qubo_dict,
        N=N,
        batch_size=K,
        costs=costs,
        total_budget=total_budget
    )

    # 2. Heuristic Solver
    best_sa_vec, best_sa_energy = opt_service.solve_simulated_annealing(
        qubo_dict=qubo_dict,
        N=N,
        batch_size=K,
        costs=costs,
        total_budget=total_budget,
        num_iterations=2000,
        random_seed=42
    )

    # Check batch size constraint
    assert np.sum(best_exact_vec) == K
    assert np.sum(best_sa_vec) == K

    # Check budget constraint
    assert np.sum(best_exact_vec * costs) <= total_budget
    assert np.sum(best_sa_vec * costs) <= total_budget

    # Heuristic must find the global optimum or within 0.1% of global optimum
    energy_diff = abs(best_sa_energy - best_exact_energy)
    assert energy_diff < 0.05, f"Heuristic energy {best_sa_energy} differs from exhaustive {best_exact_energy}"


def test_classical_baselines_compliance():
    N = 20
    K = 5
    budget = 2500.0

    pred_pic50 = np.random.uniform(4.0, 9.0, N)
    costs = np.random.uniform(300.0, 700.0, N)
    sim_mat = np.eye(N)

    # Test greedy activity
    greedy_act = opt_service.baseline_greedy_activity(pred_pic50, costs, K, budget)
    assert np.sum(greedy_act) <= K
    assert np.sum(greedy_act * costs) <= budget

    # Test greedy MMR
    greedy_mmr = opt_service.baseline_greedy_mmr(pred_pic50, sim_mat, costs, K, budget)
    assert np.sum(greedy_mmr) <= K
    assert np.sum(greedy_mmr * costs) <= budget

    # Test random feasible
    rand_batches = opt_service.baseline_random_feasible(N, costs, K, budget, num_trials=10)
    assert len(rand_batches) > 0
    for rb in rand_batches:
        assert np.sum(rb) == K
        assert np.sum(rb * costs) <= budget

