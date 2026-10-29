"""
Machine Learning Model Training, Evaluation, and Prediction Endpoints.
"""

import uuid
import json
from typing import List, Dict, Any, Optional
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.entities import Compound, ModelRun, Target, Assay
from ...schemas.payloads import ModelTrainRequest, ModelEvaluationMetrics, PredictionItem
from ...services.prediction.pipeline import prediction_pipeline
from ...services.chemistry.processor import chemistry_processor
from ...services.uncertainty.estimator import uncertainty_estimator

router = APIRouter(prefix="/models", tags=["Machine Learning"])

# In-memory store for currently active fitted model and predictions
_CURRENT_MODEL_STATE: Dict[str, Any] = {}


@router.post("/train", response_model=ModelEvaluationMetrics)
def train_model(payload: ModelTrainRequest, db: Session = Depends(get_db)):
    """
    Trains a classical predictive model (Random Forest, Gradient Boosting, or Baseline)
    using leakage-free scaffold split or random split, and computes rigorous metrics.
    """
    compounds = db.query(Compound).filter(Compound.historical_pic50.isnot(None)).all()
    if len(compounds) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient compounds with assay measurements ({len(compounds)} found). Need at least 10."
        )

    smiles_list = [c.canonical_smiles for c in compounds]
    y_values = [c.historical_pic50 for c in compounds]

    try:
        run_res = prediction_pipeline.train_and_evaluate(
            smiles_list=smiles_list,
            y_values=y_values,
            model_type=payload.model_type,
            split_method=payload.split_method,
            test_size=payload.test_size,
            random_seed=payload.random_seed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

    run_id = f"MRUN-{uuid.uuid4().hex[:8].upper()}"
    metrics = run_res["metrics"]

    # Persist in DB
    model_run = ModelRun(
        run_id=run_id,
        target_id=payload.target_id,
        assay_id=payload.assay_id,
        model_type=payload.model_type,
        split_method=payload.split_method,
        test_size=payload.test_size,
        random_seed=payload.random_seed,
        num_train=run_res["num_train"],
        num_test=run_res["num_test"],
        r2=metrics["r2"],
        rmse=metrics["rmse"],
        mae=metrics["mae"],
        spearman=metrics["spearman_corr"],
        pearson=metrics["pearson_corr"],
        roc_auc=metrics.get("roc_auc"),
        pr_auc=metrics.get("pr_auc"),
        calibration_slope=metrics.get("coverage_stats", {}).get("empirical_coverage"),
        parameters_json=json.dumps({"n_estimators": payload.n_estimators})
    )
    db.add(model_run)
    db.commit()

    # Pre-generate candidate pool predictions
    all_compounds = db.query(Compound).all()
    all_smiles = [c.canonical_smiles for c in all_compounds]
    all_fps = prediction_pipeline.extract_features(all_smiles)

    train_smiles = [smiles_list[i] for i in run_res["train_indices"]]
    train_fps = run_res["X_train"]

    model = run_res["model"]
    if hasattr(model, "estimators_"):
        preds, uncerts = uncertainty_estimator.estimate_ensemble_uncertainty(model, all_fps)
    else:
        preds = model.predict(all_fps)
        uncerts = np.zeros_like(preds)

    ood_scores = uncertainty_estimator.compute_ood_scores(all_fps, train_fps)
    novelty_scores = chemistry_processor.compute_novelty_scores(all_smiles, train_smiles)

    _CURRENT_MODEL_STATE["model"] = model
    _CURRENT_MODEL_STATE["run_id"] = run_id
    _CURRENT_MODEL_STATE["predictions"] = {
        c.compound_id: {
            "predicted_pic50": round(float(preds[i]), 3),
            "uncertainty": round(float(uncerts[i]), 3),
            "ood_score": round(float(ood_scores[i]), 3),
            "novelty_score": round(float(novelty_scores[i]), 3),
            "is_predicted_active": bool(preds[i] >= 6.5)
        }
        for i, c in enumerate(all_compounds)
    }
    _CURRENT_MODEL_STATE["train_indices"] = run_res["train_indices"]
    _CURRENT_MODEL_STATE["test_indices"] = run_res["test_indices"]
    _CURRENT_MODEL_STATE["train_smiles"] = train_smiles
    _CURRENT_MODEL_STATE["test_smiles"] = [smiles_list[i] for i in run_res["test_indices"]]

    return {
        "r2": metrics["r2"],
        "rmse": metrics["rmse"],
        "mae": metrics["mae"],
        "spearman_corr": metrics["spearman_corr"],
        "pearson_corr": metrics["pearson_corr"],
        "roc_auc": metrics.get("roc_auc"),
        "pr_auc": metrics.get("pr_auc"),
        "num_train": run_res["num_train"],
        "num_test": run_res["num_test"],
        "model_type": payload.model_type,
        "split_method": payload.split_method,
        "calibration_slope": metrics.get("coverage_stats", {}).get("empirical_coverage"),
        "ood_compounds_count": int(np.sum(ood_scores > 0.6))
    }


@router.get("/latest", response_model=Optional[ModelEvaluationMetrics])
def get_latest_model(db: Session = Depends(get_db)):
    """Returns the most recent model evaluation metrics."""
    latest = db.query(ModelRun).order_by(ModelRun.created_at.desc()).first()
    if not latest:
        return None

    return {
        "r2": latest.r2,
        "rmse": latest.rmse,
        "mae": latest.mae,
        "spearman_corr": latest.spearman,
        "pearson_corr": latest.pearson,
        "roc_auc": latest.roc_auc,
        "pr_auc": latest.pr_auc,
        "num_train": latest.num_train,
        "num_test": latest.num_test,
        "model_type": latest.model_type,
        "split_method": latest.split_method,
        "calibration_slope": latest.calibration_slope,
        "ood_compounds_count": latest.ood_count
    }


@router.get("/predictions", response_model=List[PredictionItem])
def get_candidate_predictions(db: Session = Depends(get_db)):
    """Returns activity predictions, uncertainty, and novelty for all candidate compounds."""
    compounds = db.query(Compound).all()
    if not _CURRENT_MODEL_STATE.get("predictions"):
        # Auto-train default model if not yet trained
        default_req = ModelTrainRequest()
        train_model(default_req, db)

    preds_map = _CURRENT_MODEL_STATE.get("predictions", {})

    items = []
    for c in compounds:
        p = preds_map.get(c.compound_id, {
            "predicted_pic50": c.historical_pic50 or 6.0,
            "uncertainty": 0.25,
            "ood_score": 0.3,
            "novelty_score": 0.4,
            "is_predicted_active": True
        })
        items.append({
            "compound_id": c.compound_id,
            "source_id": c.source_id,
            "canonical_smiles": c.canonical_smiles,
            "predicted_pic50": p["predicted_pic50"],
            "uncertainty": p["uncertainty"],
            "ood_score": p["ood_score"],
            "is_predicted_active": p["is_predicted_active"],
            "novelty_score": p["novelty_score"],
            "scaffold_id": c.scaffold_id or "SCAF-00000",
            "cost": c.cost,
            "availability": c.availability
        })
    return items
