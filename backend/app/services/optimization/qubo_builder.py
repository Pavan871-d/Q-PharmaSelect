"""
QUBO Formulation and Matrix Construction Engine for Assay-Constrained Selection.
Translates multi-objective discovery criteria (activity, uncertainty, novelty,
cost, and pairwise redundancy) and batch constraints into a mathematically rigorous QUBO.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np


class QUBOFormulationEngine:
    """Builds mathematically rigorous QUBO matrices for compound selection."""

    def __init__(self):
        pass

    def build_qubo_matrix(
        self,
        predicted_pic50: np.ndarray,
        uncertainties: np.ndarray,
        novelties: np.ndarray,
        costs: np.ndarray,
        tanimoto_matrix: np.ndarray,
        batch_size: int,
        total_budget: float,
        weight_activity: float = 1.0,
        weight_exploration: float = 0.5,
        weight_novelty: float = 0.8,
        weight_diversity: float = 0.7,
        weight_cost: float = 0.3,
        lambda_batch: Optional[float] = None
    ) -> Tuple[Dict[Tuple[int, int], float], np.ndarray, np.ndarray]:
        """
        Constructs the QUBO dictionary {(i, j): weight} and dense matrix Q.
        
        Objective:
        Minimize: - [ w_act * y_norm + w_exp * unc_norm + w_nov * nov - w_cost * cost_norm ]
                  + w_div * sum_{i < j} S_ij * x_i * x_j
                  + lambda_batch * (sum_i x_i - K)^2
                  
        Returns:
            (qubo_dict, dense_Q, linear_utilities)
        """
        N = len(predicted_pic50)
        if N == 0:
            return {}, np.zeros((0, 0)), np.zeros(0)

        # 1. Normalize individual utility components into [0, 1]
        y_min, y_max = float(np.min(predicted_pic50)), float(np.max(predicted_pic50))
        y_norm = (predicted_pic50 - y_min) / (y_max - y_min + 1e-6)

        u_max = float(np.max(uncertainties)) if np.max(uncertainties) > 0 else 1.0
        u_norm = uncertainties / (u_max + 1e-6)

        c_max = float(np.max(costs)) if np.max(costs) > 0 else 1.0
        c_norm = costs / (c_max + 1e-6)

        nov_norm = np.clip(novelties, 0.0, 1.0)

        # Net individual discovery utility \mu_i
        utilities = (
            weight_activity * y_norm
            + weight_exploration * u_norm
            + weight_novelty * nov_norm
            - weight_cost * c_norm
        )

        # 2. Derive sufficient penalty coefficient \lambda_batch to enforce exact batch size K
        # lambda_batch must dominate the maximum change in discovery utility
        max_delta_utility = float(np.max(utilities) - np.min(utilities))
        if lambda_batch is None:
            lambda_batch = max(2.5, max_delta_utility * 1.5 + 1.0)

        # 3. Construct dense Q matrix and sparse dictionary
        # Diagonal elements: Q_ii = - \mu_i + \lambda_batch * (1 - 2K)
        # Off-diagonal elements: Q_ij = w_diversity * S_ij + 2 * \lambda_batch
        dense_Q = np.zeros((N, N), dtype=np.float64)
        qubo_dict = {}

        K = float(batch_size)
        linear_penalty = lambda_batch * (1.0 - 2.0 * K)
        pairwise_batch_penalty = 2.0 * lambda_batch

        for i in range(N):
            q_ii = -float(utilities[i]) + linear_penalty
            dense_Q[i, i] = q_ii
            qubo_dict[(i, i)] = round(q_ii, 4)

            for j in range(i + 1, N):
                sim = float(tanimoto_matrix[i, j])
                q_ij = weight_diversity * sim + pairwise_batch_penalty
                dense_Q[i, j] = q_ij
                qubo_dict[(i, j)] = round(q_ij, 4)

        return qubo_dict, dense_Q, utilities

    def evaluate_qubo_energy(
        self,
        qubo_dict: Dict[Tuple[int, int], float],
        selection_vector: np.ndarray
    ) -> float:
        """Calculates exact QUBO objective energy for a binary bitstring x."""
        energy = 0.0
        for (i, j), weight in qubo_dict.items():
            if i == j:
                energy += weight * selection_vector[i]
            else:
                energy += weight * selection_vector[i] * selection_vector[j]
        return float(energy)


qubo_engine = QUBOFormulationEngine()

