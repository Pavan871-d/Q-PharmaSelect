"""
Tests for Machine Learning Pipeline, Leakage Prevention, and Uncertainty.
"""

import pytest
import numpy as np
from backend.app.services.prediction.pipeline import prediction_pipeline
from backend.app.services.uncertainty.estimator import uncertainty_estimator
from backend.app.services.data_ingestion.demo_data import CURATED_COMPOUNDS
from backend.app.services.chemistry.processor import chemistry_processor


def test_scaffold_split_leakage_resistance():
    smiles_list = [c["smiles"] for c in CURATED_COMPOUNDS[:40]]
    train_idx, test_idx = prediction_pipeline.partition_by_scaffold(smiles_list, test_size=0.25, random_seed=42)

    # Check non-empty
    assert len(train_idx) > 0
    assert len(test_idx) > 0
    # No index overlap
    assert len(set(train_idx).intersection(set(test_idx))) == 0

    # Verify zero scaffold overlap between train and test
    train_scaffolds = set(chemistry_processor.get_murcko_scaffold(smiles_list[i])[1] for i in train_idx)
    test_scaffolds = set(chemistry_processor.get_murcko_scaffold(smiles_list[i])[1] for i in test_idx)
    scaffold_intersection = train_scaffolds.intersection(test_scaffolds)
    assert len(scaffold_intersection) == 0, f"Scaffold leakage detected: {scaffold_intersection}"


def test_model_training_and_metrics():
    smiles_list = [c["smiles"] for c in CURATED_COMPOUNDS]
    y_values = [c["historical_pic50"] for c in CURATED_COMPOUNDS]

    res = prediction_pipeline.train_and_evaluate(
        smiles_list=smiles_list,
        y_values=y_values,
        model_type="random_forest",
        split_method="scaffold_split",
        test_size=0.25,
        random_seed=42
    )

    metrics = res["metrics"]
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "spearman_corr" in metrics
    assert metrics["rmse"] < 2.0
    assert metrics["spearman_corr"] > 0.5


def test_epistemic_uncertainty_non_negative():
    smiles_list = [c["smiles"] for c in CURATED_COMPOUNDS[:30]]
    y_values = [c["historical_pic50"] for c in CURATED_COMPOUNDS[:30]]

    res = prediction_pipeline.train_and_evaluate(
        smiles_list=smiles_list,
        y_values=y_values,
        model_type="random_forest",
        split_method="random_split",
        random_seed=42
    )

    uncert = res["test_uncertainties"]
    assert len(uncert) == len(res["test_indices"])
    assert np.all(uncert >= 0.0)


def test_interval_coverage_calculation():
    y_true = np.array([7.0, 8.0, 6.5, 5.0, 9.0])
    y_pred = np.array([7.1, 7.8, 6.4, 5.2, 8.8])
    uncert = np.array([0.3, 0.4, 0.2, 0.5, 0.3])

    cov = uncertainty_estimator.evaluate_interval_coverage(y_true, y_pred, uncert)
    assert cov["empirical_coverage"] >= 0.8
    assert cov["mean_interval_width"] > 0.0

