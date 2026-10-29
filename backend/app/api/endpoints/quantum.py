"""
QpiAI Quantum SDK / QCloud Endpoints.
Executes molecular quantum circuits, records measurements, and benchmarks QML.
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.entities import Compound, QuantumRun
from ...schemas.payloads import QuantumRunRequest, QuantumRunResponse
from ...services.quantum.qcloud_runner import quantum_service
from ...services.prediction.pipeline import prediction_pipeline
from .models import _CURRENT_MODEL_STATE, ModelTrainRequest, train_model

router = APIRouter(prefix="/quantum", tags=["Quantum Machine Learning"])


@router.post("/run", response_model=QuantumRunResponse)
def execute_quantum_experiment(payload: QuantumRunRequest, db: Session = Depends(get_db)):
    """
    Executes a real QpiAI Quantum SDK experiment:
    - Encodes molecular descriptors via PCA onto quantum rotation angles.
    - Constructs parameterized quantum circuits with Hadamard, Ry, Rz, and CNOT entanglement ladders.
    - Runs on QpiAI QCloud backend (if authenticated) or QpiAI simulator.
    - Records measurements, execution time, and evaluates hybrid quantum model vs classical baseline.
    """
    compounds = db.query(Compound).filter(Compound.historical_pic50.isnot(None)).all()
    if len(compounds) < 10:
        raise HTTPException(status_code=400, detail="Insufficient compounds for quantum experiment.")

    # Ensure dataset is split
    if not _CURRENT_MODEL_STATE.get("train_indices"):
        train_model(ModelTrainRequest(target_id=payload.target_id), db)

    train_idx = _CURRENT_MODEL_STATE["train_indices"]
    test_idx = _CURRENT_MODEL_STATE["test_indices"]

    smiles_all = [c.canonical_smiles for c in compounds]
    y_all = [c.historical_pic50 for c in compounds]

    train_smiles = [smiles_all[i] for i in train_idx if i < len(smiles_all)]
    test_smiles = [smiles_all[i] for i in test_idx if i < len(smiles_all)]

    y_train = [y_all[i] for i in train_idx if i < len(y_all)]
    y_test = [y_all[i] for i in test_idx if i < len(y_all)]

    import numpy as np
    X_train_fps = prediction_pipeline.extract_features(train_smiles)
    X_test_fps = prediction_pipeline.extract_features(test_smiles)

    # Run quantum experiment via QpiAI Quantum SDK
    q_result = quantum_service.run_quantum_experiment(
        X_train_fps=X_train_fps,
        y_train=np.array(y_train, dtype=np.float32),
        X_test_fps=X_test_fps,
        y_test=np.array(y_test, dtype=np.float32),
        num_qubits=payload.num_qubits,
        num_shots=payload.num_shots,
        backend_name=payload.backend_name
    )

    # Persist in DB
    q_run = QuantumRun(
        run_id=q_result["run_id"],
        target_id=payload.target_id,
        backend_name=q_result["backend_name"],
        num_qubits=q_result["num_qubits"],
        circuit_depth=q_result["circuit_depth"],
        num_shots=q_result["num_shots"],
        execution_time_ms=q_result["execution_time_ms"],
        status=q_result["status"],
        qasm_code=q_result["qasm_preview"],
        counts_json=json.dumps(q_result["measurement_counts_summary"]),
        baseline_rmse=q_result["classical_baseline_rmse"],
        quantum_rmse=q_result["quantum_hybrid_rmse"],
        baseline_r2=q_result["classical_baseline_r2"],
        quantum_r2=q_result["quantum_hybrid_r2"],
        logs_json=json.dumps(q_result["logs"]),
        evidence_status=q_result["evidence_status"]
    )
    db.add(q_run)
    db.commit()

    return q_result


@router.get("/latest", response_model=Optional[QuantumRunResponse])
def get_latest_quantum_run(db: Session = Depends(get_db)):
    """Returns the most recent quantum experiment execution record."""
    latest = db.query(QuantumRun).order_by(QuantumRun.created_at.desc()).first()
    if not latest:
        return None

    counts = json.loads(latest.counts_json) if latest.counts_json else {}
    logs = json.loads(latest.logs_json) if latest.logs_json else []

    return {
        "run_id": latest.run_id,
        "backend_name": latest.backend_name,
        "status": latest.status,
        "sdk_version": quantum_service.sdk_version,
        "num_qubits": latest.num_qubits,
        "circuit_depth": latest.circuit_depth,
        "num_shots": latest.num_shots,
        "execution_time_ms": latest.execution_time_ms,
        "qasm_preview": latest.qasm_code or "",
        "measurement_counts_summary": counts,
        "classical_baseline_rmse": latest.baseline_rmse,
        "quantum_hybrid_rmse": latest.quantum_rmse,
        "classical_baseline_r2": latest.baseline_r2,
        "quantum_hybrid_r2": latest.quantum_r2,
        "evidence_status": latest.evidence_status,
        "logs": logs
    }

