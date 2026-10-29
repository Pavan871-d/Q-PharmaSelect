"""
Activity Prediction Pipeline with Strict Leakage-Resistant Data Splitting.
Implements scaffold splitting, random splitting, Random Forest ensembles,
Gradient Boosting, and scientific evaluation metrics.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import scipy.stats as stats
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    roc_auc_score, average_precision_score, f1_score, balanced_accuracy_score
)
from sklearn.model_selection import train_test_split
from ..chemistry.processor import chemistry_processor
from ..uncertainty.estimator import uncertainty_estimator


class ActivityPredictionPipeline:
    """End-to-end predictive modeling pipeline for molecular assays."""

    def __init__(self):
        self.processor = chemistry_processor
        self.uncertainty = uncertainty_estimator

    def partition_by_scaffold(
        self,
        smiles_list: List[str],
        test_size: float = 0.25,
        random_seed: int = 42
    ) -> Tuple[List[int], List[int]]:
        """
        Partitions dataset by Bemis-Murcko scaffolds so that scaffolds
        in the test set do not appear in the training set (leakage-free scaffold split).
        """
        rng = np.random.RandomState(random_seed)
        scaffold_to_indices = {}

        for idx, smiles in enumerate(smiles_list):
            _, scaff_id = self.processor.get_murcko_scaffold(smiles)
            if scaff_id not in scaffold_to_indices:
                scaffold_to_indices[scaff_id] = []
            scaffold_to_indices[scaff_id].append(idx)

        # Shuffle scaffold groups
        scaffold_keys = list(scaffold_to_indices.keys())
        rng.shuffle(scaffold_keys)

        total_samples = len(smiles_list)
        target_test_count = int(total_samples * test_size)

        train_indices = []
        test_indices = []

        for scaff in scaffold_keys:
            indices = scaffold_to_indices[scaff]
            if len(test_indices) + len(indices) <= target_test_count or not test_indices:
                test_indices.extend(indices)
            else:
                train_indices.extend(indices)

        # Ensure at least one in train and test
        if not train_indices:
            train_indices = test_indices[: len(test_indices) // 2]
            test_indices = test_indices[len(test_indices) // 2 :]

        return train_indices, test_indices

    def partition_random(
        self,
        n_samples: int,
        test_size: float = 0.25,
        random_seed: int = 42
    ) -> Tuple[List[int], List[int]]:
        """Standard random split with fixed seed."""
        indices = np.arange(n_samples)
        train_idx, test_idx = train_test_split(
            indices, test_size=test_size, random_state=random_seed
        )
        return train_idx.tolist(), test_idx.tolist()

    def extract_features(self, smiles_list: List[str]) -> np.ndarray:
        """Computes Morgan ECFP4 fingerprint feature matrix."""
        return self.processor.compute_fingerprints_batch(smiles_list)

    def train_and_evaluate(
        self,
        smiles_list: List[str],
        y_values: List[float],
        model_type: str = "random_forest",
        split_method: str = "scaffold_split",
        test_size: float = 0.25,
        random_seed: int = 42,
        activity_threshold: float = 6.5
    ) -> Dict[str, Any]:
        """
        Executes a leakage-resistant model training run and evaluates on held-out data.
        """
        n_samples = len(smiles_list)
        if n_samples < 10:
            raise ValueError(f"Insufficient samples for training ({n_samples} provided, minimum 10 required).")

        # 1. Leakage-free split
        if split_method == "scaffold_split":
            train_idx, test_idx = self.partition_by_scaffold(smiles_list, test_size, random_seed)
        else:
            train_idx, test_idx = self.partition_random(n_samples, test_size, random_seed)

        train_smiles = [smiles_list[i] for i in train_idx]
        test_smiles = [smiles_list[i] for i in test_idx]

        y_train = np.array([y_values[i] for i in train_idx], dtype=np.float32)
        y_test = np.array([y_values[i] for i in test_idx], dtype=np.float32)

        # 2. Extract features strictly
        X_train = self.extract_features(train_smiles)
        X_test = self.extract_features(test_smiles)

        # 3. Model Initialization
        if model_type == "random_forest":
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=14,
                min_samples_split=3,
                random_state=random_seed,
                n_jobs=-1
            )
        elif model_type == "gradient_boosting":
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.08,
                random_state=random_seed
            )
        else:
            # Baseline median model
            model = DummyRegressor(strategy="median")

        # 4. Train Model
        model.fit(X_train, y_train)

        # 5. Predict on Test Set
        if isinstance(model, RandomForestRegressor):
            y_test_pred, test_uncertainties = self.uncertainty.estimate_ensemble_uncertainty(model, X_test)
        else:
            y_test_pred = model.predict(X_test)
            test_uncertainties = np.zeros_like(y_test_pred)

        # 6. Out-Of-Distribution (OOD) score for test set relative to train set
        test_ood = self.uncertainty.compute_ood_scores(X_test, X_train)

        # 7. Regression Metrics
        rmse = float(np.sqrt(mean_squared_error(y_test, y_test_pred)))
        mae = float(mean_absolute_error(y_test, y_test_pred))
        r2 = float(r2_score(y_test, y_test_pred))

        # Rank correlations
        if len(y_test) > 2 and np.std(y_test_pred) > 1e-6:
            spearman_corr, _ = stats.spearmanr(y_test, y_test_pred)
            pearson_corr, _ = stats.pearsonr(y_test, y_test_pred)
        else:
            spearman_corr, pearson_corr = 0.0, 0.0

        # 8. Classification Metrics against threshold
        y_test_binary = (y_test >= activity_threshold).astype(int)
        y_pred_binary = (y_test_pred >= activity_threshold).astype(int)

        roc_auc = None
        pr_auc = None
        if len(np.unique(y_test_binary)) > 1:
            try:
                roc_auc = float(roc_auc_score(y_test_binary, y_test_pred))
                pr_auc = float(average_precision_score(y_test_binary, y_test_pred))
            except Exception:
                pass

        # Interval calibration check
        coverage_stats = {}
        if isinstance(model, RandomForestRegressor):
            coverage_stats = self.uncertainty.evaluate_interval_coverage(
                y_test, y_test_pred, test_uncertainties
            )

        return {
            "model": model,
            "model_type": model_type,
            "split_method": split_method,
            "random_seed": random_seed,
            "num_train": len(train_idx),
            "num_test": len(test_idx),
            "train_indices": train_idx,
            "test_indices": test_idx,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "y_test_pred": y_test_pred,
            "test_uncertainties": test_uncertainties,
            "test_ood": test_ood,
            "metrics": {
                "r2": round(r2, 4),
                "rmse": round(rmse, 4),
                "mae": round(mae, 4),
                "spearman_corr": round(float(spearman_corr), 4),
                "pearson_corr": round(float(pearson_corr), 4),
                "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
                "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
                "coverage_stats": coverage_stats
            }
        }


prediction_pipeline = ActivityPredictionPipeline()
