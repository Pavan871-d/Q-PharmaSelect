"""
Scientific Report Generation and Data Export Endpoints.
Generates comprehensive export packages in JSON and CSV formats.
"""

import io
import csv
import json
from datetime import datetime
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.entities import Compound, OptimizationRun, SelectedCompound, ValidationRun, QuantumRun, ModelRun
from ...core.config import settings

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])


@router.get("/export/selected-csv")
def export_selected_compounds_csv(db: Session = Depends(get_db)):
    """Exports the latest selected experimental batch as a downloadable CSV."""
    latest_opt = db.query(OptimizationRun).order_by(OptimizationRun.created_at.desc()).first()
    if not latest_opt:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Message"])
        writer.writerow(["No optimization runs available to export."])
        return Response(content=output.getvalue(), media_type="text/csv")

    selected = db.query(SelectedCompound).filter(SelectedCompound.opt_run_id == latest_opt.run_id).order_by(SelectedCompound.rank).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "rank", "compound_id", "source_id", "canonical_smiles", "predicted_pic50",
        "uncertainty", "novelty_score", "cost_usd", "scaffold_id", "scaffold",
        "availability", "marginal_utility", "selection_rationale", "evidence_status"
    ])

    for s in selected:
        writer.writerow([
            s.rank, s.compound_id, s.source_id, s.canonical_smiles, s.predicted_pic50,
            s.uncertainty, s.novelty_score, s.cost, s.scaffold_id, s.scaffold,
            s.availability, s.marginal_utility, s.selection_rationale, s.evidence_status
        ])

    filename = f"qpharmaselect_selected_batch_{latest_opt.run_id}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/full-json")
def export_full_experiment_package(db: Session = Depends(get_db)):
    """Exports complete experiment package including metadata, QML, optimization, and validation."""
    latest_model = db.query(ModelRun).order_by(ModelRun.created_at.desc()).first()
    latest_q = db.query(QuantumRun).order_by(QuantumRun.created_at.desc()).first()
    latest_opt = db.query(OptimizationRun).order_by(OptimizationRun.created_at.desc()).first()
    latest_val = db.query(ValidationRun).order_by(ValidationRun.created_at.desc()).first()

    selected = []
    if latest_opt:
        sel_records = db.query(SelectedCompound).filter(SelectedCompound.opt_run_id == latest_opt.run_id).order_by(SelectedCompound.rank).all()
        selected = [
            {
                "rank": s.rank,
                "compound_id": s.compound_id,
                "source_id": s.source_id,
                "canonical_smiles": s.canonical_smiles,
                "predicted_pic50": s.predicted_pic50,
                "uncertainty": s.uncertainty,
                "novelty_score": s.novelty_score,
                "cost": s.cost,
                "scaffold": s.scaffold,
                "scaffold_id": s.scaffold_id,
                "selection_rationale": s.selection_rationale,
                "evidence_status": s.evidence_status
            }
            for s in sel_records
        ]

    package = {
        "metadata": {
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "generated_at": datetime.utcnow().isoformat(),
            "target": "EGFR (CHEMBL203)",
            "assay": "CHEMBL615112"
        },
        "model_evaluation": {
            "run_id": latest_model.run_id if latest_model else None,
            "model_type": latest_model.model_type if latest_model else None,
            "split_method": latest_model.split_method if latest_model else None,
            "r2": latest_model.r2 if latest_model else None,
            "rmse": latest_model.rmse if latest_model else None,
            "spearman": latest_model.spearman if latest_model else None
        },
        "quantum_experiment": {
            "run_id": latest_q.run_id if latest_q else None,
            "backend": latest_q.backend_name if latest_q else None,
            "num_qubits": latest_q.num_qubits if latest_q else None,
            "circuit_depth": latest_q.circuit_depth if latest_q else None,
            "shots": latest_q.num_shots if latest_q else None,
            "execution_status": latest_q.status if latest_q else None,
            "evidence_status": latest_q.evidence_status if latest_q else None
        },
        "optimization": {
            "run_id": latest_opt.run_id if latest_opt else None,
            "solver": latest_opt.solver_backend if latest_opt else None,
            "batch_size": latest_opt.batch_size if latest_opt else None,
            "budget": latest_opt.total_budget if latest_opt else None,
            "actual_cost": latest_opt.total_cost if latest_opt else None,
            "objective_value": latest_opt.objective_value if latest_opt else None,
            "batch_size_satisfied": latest_opt.batch_size_satisfied if latest_opt else None,
            "budget_satisfied": latest_opt.budget_satisfied if latest_opt else None,
            "selected_compounds": selected
        },
        "retrospective_validation": {
            "validation_id": latest_val.validation_id if latest_val else None,
            "enrichment_factor": latest_val.enrichment_factor if latest_val else None,
            "hit_rate": latest_val.hit_rate if latest_val else None,
            "novel_scaffolds": latest_val.novel_scaffolds if latest_val else None,
            "cost_efficiency": latest_val.cost_efficiency if latest_val else None,
            "baselines": json.loads(latest_val.baselines_json) if latest_val and latest_val.baselines_json else []
        }
    }

    return package

