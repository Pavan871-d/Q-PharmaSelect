"""
Uncertainty Quantification and Out-Of-Distribution (OOD) Analysis.
Estimates model epistemic uncertainty via ensemble tree variance
and chemical-space domain applicability via Tanimoto distance.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from ..chemistry.processor import chemistry_processor


class UncertaintyEstimator:
    """Estimates epistemic model uncertainty and chemical-space novelty/OOD."""

    def __init__(self):
        self.processor = chemistry_processor

    def estimate_ensemble_uncertainty(
        self,
        rf_model: RandomForestRegressor,
        X_features: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates individual tree predictions and derives epistemic uncertainty
        (standard deviation across the tree ensemble).
        Returns: (mean_predictions, uncertainty_std)
        """
        # Collect predictions from each tree estimator
        per_tree_preds = np.array([tree.predict(X_features) for tree in rf_model.estimators_])
        mean_preds = np.mean(per_tree_preds, axis=0)
        uncertainty_std = np.std(per_tree_preds, axis=0)
        return mean_preds, uncertainty_std

    def compute_ood_scores(
        self,
        candidate_fps: np.ndarray,
        training_fps: np.ndarray
    ) -> np.ndarray:
        """
        Calculates out-of-distribution (OOD) risk based on minimum Tanimoto distance
        to the closest molecule in the training chemical space:
        d_OOD(x) = 1.0 - max_{j in Train} Tanimoto(x, x_j)
        """
        n_candidates = candidate_fps.shape[0]
        ood_scores = np.zeros(n_candidates, dtype=np.float32)

        # Batch Tanimoto between binary vectors
        # Tanimoto(a, b) = (a . b) / (|a| + |b| - a . b)
        train_norms = np.sum(training_fps, axis=1)

        for i in range(n_candidates):
            c_fp = candidate_fps[i]
            c_norm = np.sum(c_fp)
            if c_norm == 0:
                ood_scores[i] = 1.0
                continue

            intersections = np.dot(training_fps, c_fp)
            unions = train_norms + c_norm - intersections
            unions[unions == 0] = 1.0
            tanimoto_sims = intersections / unions
            max_sim = np.max(tanimoto_sims)
            ood_scores[i] = round(float(1.0 - max_sim), 4)

        return ood_scores

    def evaluate_interval_coverage(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        uncertainty_std: np.ndarray,
        z_multiplier: float = 1.96
    ) -> Dict[str, float]:
        """
        Evaluates empirical coverage of 95% predictive interval [y_pred - z*sigma, y_pred + z*sigma].
        """
        lower = y_pred - z_multiplier * uncertainty_std
        upper = y_pred + z_multiplier * uncertainty_std
        covered = (y_true >= lower) & (y_true <= upper)
        empirical_coverage = float(np.mean(covered))
        mean_width = float(np.mean(upper - lower))
        return {
            "nominal_coverage": 0.95,
            "empirical_coverage": round(empirical_coverage, 3),
            "mean_interval_width": round(mean_width, 3),
            "calibration_error": round(abs(empirical_coverage - 0.95), 3)
        }


uncertainty_estimator = UncertaintyEstimator()
