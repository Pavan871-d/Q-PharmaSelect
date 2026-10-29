"""
Solver Adapter for Constrained Batch Selection.
Directly interfaces with QpiAI Opt SDK (QUBOProblem / Solver)
and provides verified classical baselines (Simulated Annealing, Greedy MMR,
Random Feasible Sampling, and Exact Exhaustive Enumerator).
"""

import time
import itertools
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from ...core.config import settings
from .qubo_builder import qubo_engine

try:
    import qpiai_opt
    from qpiai_opt.problem.qubo import QUBOProblem
    from qpiai_opt.solver.solver import Solver as QpiAISolver
    QPIAI_OPT_AVAILABLE = True
except ImportError:
    QPIAI_OPT_AVAILABLE = False


class QpiAIOptService:
    """Production optimizer adapter for molecular batch screening."""

    def __init__(self):
        self.sdk_available = QPIAI_OPT_AVAILABLE
        self.qubo_engine = qubo_engine

    def check_connection(self) -> Dict[str, Any]:
        """Checks QpiAI Opt SDK availability and authentication settings."""
        has_key = settings.has_opt_key
        return {
            "sdk_available": self.sdk_available,
            "has_api_key": has_key,
            "opt_url": settings.QPIAI_OPT_URL,
            "status": "CONFIGURED" if has_key else "KEY_REQUIRED",
            "supported_formulations": ["QUBO", "ISING", "MAX_INDEPENDENT_SET"]
        }

    def solve_exact_exhaustive(
        self,
        qubo_dict: Dict[Tuple[int, int], float],
        N: int,
        batch_size: int,
        costs: np.ndarray,
        total_budget: float
    ) -> Tuple[np.ndarray, float]:
        """
        Calculates exact global minimum QUBO energy via brute-force combination search.
        Permitted for N <= 18 to establish ground truth reference.
        """
        best_energy = float("inf")
        best_selection = np.zeros(N, dtype=int)

        for combo in itertools.combinations(range(N), batch_size):
            cost_sum = sum(costs[i] for i in combo)
            if cost_sum > total_budget:
                continue

            vec = np.zeros(N, dtype=int)
            vec[list(combo)] = 1
            energy = self.qubo_engine.evaluate_qubo_energy(qubo_dict, vec)

            if energy < best_energy:
                best_energy = energy
                best_selection = vec.copy()

        return best_selection, best_energy

    def solve_simulated_annealing(
        self,
        qubo_dict: Dict[Tuple[int, int], float],
        N: int,
        batch_size: int,
        costs: np.ndarray,
        total_budget: float,
        initial_temp: float = 10.0,
        cooling_rate: float = 0.98,
        num_iterations: int = 1500,
        random_seed: int = 42
    ) -> Tuple[np.ndarray, float]:
        """
        Simulated Annealing QUBO solver that enforces batch size by swapping
        selected and unselected bits at each iteration.
        """
        rng = np.random.RandomState(random_seed)

        # Initial feasible state
        current_state = np.zeros(N, dtype=int)
        valid_indices = list(range(N))
        chosen = rng.choice(valid_indices, size=batch_size, replace=False)
        current_state[chosen] = 1

        current_energy = self.qubo_engine.evaluate_qubo_energy(qubo_dict, current_state)
        best_state = current_state.copy()
        best_energy = current_energy

        temp = initial_temp
        for _ in range(num_iterations):
            # Propose swap: one 1 -> 0 and one 0 -> 1
            ones = np.where(current_state == 1)[0]
            zeros = np.where(current_state == 0)[0]
            if len(ones) == 0 or len(zeros) == 0:
                break

            swap_out = rng.choice(ones)
            swap_in = rng.choice(zeros)

            candidate_state = current_state.copy()
            candidate_state[swap_out] = 0
            candidate_state[swap_in] = 1

            candidate_energy = self.qubo_engine.evaluate_qubo_energy(qubo_dict, candidate_state)
            delta_e = candidate_energy - current_energy

            # Metropolis acceptance
            if delta_e < 0 or rng.rand() < np.exp(-delta_e / max(temp, 1e-4)):
                current_state = candidate_state
                current_energy = candidate_energy

                if current_energy < best_energy:
                    # Enforce budget constraint preference
                    if np.sum(current_state * costs) <= total_budget:
                        best_energy = current_energy
                        best_state = current_state.copy()

            temp *= cooling_rate

        return best_state, best_energy

    def solve_qpiai_opt_cloud(
        self,
        qubo_dict: Dict[Tuple[int, int], float],
        N: int,
        logs: List[str]
    ) -> Optional[np.ndarray]:
        """
        Submits QUBO problem to QpiAI Opt cloud solver.
        """
        if not self.sdk_available or not settings.has_opt_key:
            return None

        try:
            logs.append(f"Constructing QpiAI QUBOProblem with {N} decision variables...")
            problem = QUBOProblem(
                num_variables=N,
                qubo_dict=qubo_dict,
                max_evaluations=1000
            )

            logs.append(f"Connecting to QpiAI Opt solver at {settings.QPIAI_OPT_URL}...")
            solver = QpiAISolver(
                problem=problem,
                url=settings.QPIAI_OPT_URL,
                access_token=settings.QPIAI_OPT_API_KEY
            )
            solver.run(queue=False)
            solution = solver.get_solution()

            if solution and isinstance(solution, dict):
                # Solution is dictionary mapping variable index to 0 or 1
                selection = np.zeros(N, dtype=int)
                for idx, val in solution.items():
                    try:
                        int_idx = int(idx)
                        if 0 <= int_idx < N:
                            selection[int_idx] = int(val)
                    except ValueError:
                        pass
                logs.append("QpiAI Opt solver execution succeeded.")
                return selection
            else:
                logs.append(f"QpiAI Opt returned empty or non-dict solution: {solution}")
                return None
        except Exception as e:
            logs.append(f"QpiAI Opt Cloud error: {str(e)}")
            return None

    # ========================================================================
    # Classical Baseline Batch Selection Algorithms (Section 14)
    # ========================================================================

    def baseline_greedy_activity(
        self,
        predicted_pic50: np.ndarray,
        costs: np.ndarray,
        batch_size: int,
        total_budget: float
    ) -> np.ndarray:
        """
        Selects the top-K compounds with highest predicted activity within budget.
        """
        N = len(predicted_pic50)
        sorted_indices = np.argsort(-predicted_pic50)
        selected = np.zeros(N, dtype=int)

        current_cost = 0.0
        count = 0
        for idx in sorted_indices:
            if count >= batch_size:
                break
            if current_cost + costs[idx] <= total_budget:
                selected[idx] = 1
                current_cost += costs[idx]
                count += 1

        return selected

    def baseline_greedy_mmr(
        self,
        predicted_pic50: np.ndarray,
        tanimoto_matrix: np.ndarray,
        costs: np.ndarray,
        batch_size: int,
        total_budget: float,
        diversity_weight: float = 0.5
    ) -> np.ndarray:
        """
        Maximal Marginal Relevance (MMR) greedy selection balancing potency and diversity.
        """
        N = len(predicted_pic50)
        selected = np.zeros(N, dtype=int)
        remaining = set(range(N))

        # First compound: highest activity
        sorted_idx = np.argsort(-predicted_pic50)
        first_pick = sorted_idx[0]
        selected[first_pick] = 1
        remaining.remove(first_pick)
        current_cost = costs[first_pick]

        while np.sum(selected) < batch_size and remaining:
            selected_indices = np.where(selected == 1)[0]
            best_mmr_score = -float("inf")
            best_cand = None

            for cand in remaining:
                if current_cost + costs[cand] > total_budget:
                    continue

                max_sim_to_selected = np.max(tanimoto_matrix[cand, selected_indices])
                mmr_score = predicted_pic50[cand] - diversity_weight * max_sim_to_selected * 5.0
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_cand = cand

            if best_cand is None:
                break

            selected[best_cand] = 1
            remaining.remove(best_cand)
            current_cost += costs[best_cand]

        return selected

    def baseline_random_feasible(
        self,
        N: int,
        costs: np.ndarray,
        batch_size: int,
        total_budget: float,
        num_trials: int = 50,
        random_seed: int = 42
    ) -> List[np.ndarray]:
        """
        Generates a distribution of random feasible batches for statistical comparison.
        """
        rng = np.random.RandomState(random_seed)
        valid_batches = []

        for _ in range(num_trials * 3):
            if len(valid_batches) >= num_trials:
                break
            sample = rng.choice(N, size=batch_size, replace=False)
            if np.sum(costs[sample]) <= total_budget:
                vec = np.zeros(N, dtype=int)
                vec[sample] = 1
                valid_batches.append(vec)

        # Fallback if strict budget is tight: take least costly random sample
        if not valid_batches:
            sample = np.argsort(costs)[:batch_size]
            vec = np.zeros(N, dtype=int)
            vec[sample] = 1
            valid_batches.append(vec)

        return valid_batches


opt_service = QpiAIOptService()
