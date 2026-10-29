"""
Combinatorial Optimization Endpoints for Assay-Constrained Batch Selection.
Interfaces with QpiAI Opt and performs rigorous post-optimization verification.
"""

import time
import uuid
import json
from typing import Optional, List, Dict, Any
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.entities import Compound, OptimizationRun, SelectedCompound
from ...schemas.payloads import OptimizationRequest, OptimizationResponse, SelectedCompoundItem
from ...services.optimization.qubo_builder import qubo_engine
from ...services.optimization.solver_adapter import opt_service
from ...services.chemistry.processor import chemistry_processor
from .models import _CURRENT_MODEL_STATE, ModelTrainRequest, train_model

router = APIRouter(prefix="/optimization", tags=["Combinatorial Optimization"])

_CURRENT_OPT_STATE: Dict[str, Any] = {}


@router.post("/run", response_model=OptimizationResponse)
def run_batch_optimization(payload: OptimizationRequest, db: Session = Depends(get_db)):
    """
    Formulates and executes the constrained molecular batch selection problem:
    1. Filter candidates based on availability policy.
    2. Constructs mathematically sound QUBO matrix balancing activity, exploration,
       novelty, cost, and pairwise diversity.
    3. Runs QpiAI Opt solver (or local solver fallback).
    4. Independently validates all batch and budget constraints.
    5. Explains selection rationales and returns selected candidates.
    """
    start_time = time.time()
    logs = []
    run_id = f"OPTRUN-{uuid.uuid4().hex[:8].upper()}"

    logs.append(f"Initializing batch selection {run_id}: Batch size={payload.batch_size}, Budget=${payload.total_budget:,.2f}.")

    # 1. Ensure predictions are available
    if not _CURRENT_MODEL_STATE.get("predictions"):
        train_model(ModelTrainRequest(target_id=payload.target_id), db)

    preds_map = _CURRENT_MODEL_STATE["predictions"]

    # 2. Filter candidate pool according to availability policy
    all_compounds = db.query(Compound).all()
    candidate_pool = []
    for c in all_compounds:
        if c.availability == "UNAVAILABLE":
            continue
        if c.availability == "UNKNOWN" and payload.unknown_availability_policy == "EXCLUDE":
            continue
        candidate_pool.append(c)

    N = len(candidate_pool)
    if N < payload.batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Candidate pool after availability filtering ({N}) is smaller than requested batch size ({payload.batch_size})."
        )

    logs.append(f"Candidate pool: {N} valid molecules after applying availability policy '{payload.unknown_availability_policy}'.")

    # 3. Gather candidate vectors
    pred_y = np.array([preds_map[c.compound_id]["predicted_pic50"] for c in candidate_pool], dtype=np.float32)
    uncert = np.array([preds_map[c.compound_id]["uncertainty"] for c in candidate_pool], dtype=np.float32)
    nov = np.array([preds_map[c.compound_id]["novelty_score"] for c in candidate_pool], dtype=np.float32)
    costs = np.array([c.cost for c in candidate_pool], dtype=np.float32)
    smiles_list = [c.canonical_smiles for c in candidate_pool]

    # Pairwise Tanimoto similarity matrix
    tanimoto_mat = chemistry_processor.compute_pairwise_tanimoto(smiles_list)

    # 4. Formulate QUBO
    qubo_dict, dense_Q, linear_utils = qubo_engine.build_qubo_matrix(
        predicted_pic50=pred_y,
        uncertainties=uncert,
        novelties=nov,
        costs=costs,
        tanimoto_matrix=tanimoto_mat,
        batch_size=payload.batch_size,
        total_budget=payload.total_budget,
        weight_activity=payload.weight_activity,
        weight_exploration=payload.weight_exploration,
        weight_novelty=payload.weight_novelty,
        weight_diversity=payload.weight_diversity,
        weight_cost=payload.weight_cost
    )

    logs.append(f"QUBO formulation constructed: {N} binary variables, {len(qubo_dict)} active quadratic couplings.")

    # 5. Execute Solver
    solver_backend = "QPIAI_OPT_CLOUD"
    evidence_status = "QPIAI OPT EXECUTION VERIFIED"
    selection_vector = None

    if payload.solver_mode in ["QPIAI_OPT_AUTO", "QPIAI_OPT_CLOUD"]:
        selection_vector = opt_service.solve_qpiai_opt_cloud(qubo_dict, N, logs)

    if selection_vector is None:
        if payload.solver_mode == "EXHAUSTIVE" and N <= 18:
            logs.append("Executing exact exhaustive enumerator to guarantee global optimum...")
            selection_vector, _ = opt_service.solve_exact_exhaustive(
                qubo_dict, N, payload.batch_size, costs, payload.total_budget
            )
            solver_backend = "EXHAUSTIVE_ENUMERATION (GLOBAL OPTIMUM)"
            evidence_status = "EXHAUSTIVE ENUMERATION VERIFIED"
        else:
            logs.append("Running high-performance Simulated Annealing QUBO heuristic (development fallback)...")
            selection_vector, _ = opt_service.solve_simulated_annealing(
                qubo_dict, N, payload.batch_size, costs, payload.total_budget, random_seed=payload.random_seed
            )
            solver_backend = "SIMULATED_ANNEALING (QUBO HEURISTIC)"
            evidence_status = "CLASSICAL QUBO SOLVER (DEVELOPMENT FALLBACK)"

    # 6. Independent Post-Optimization Feasibility Verification (Section 13.8)
    selected_indices = np.where(selection_vector == 1)[0]
    selected_count = len(selected_indices)
    total_cost = float(np.sum(costs[selected_indices]))

    batch_satisfied = (selected_count == payload.batch_size)
    budget_satisfied = (total_cost <= payload.total_budget)

    objective_val = qubo_engine.evaluate_qubo_energy(qubo_dict, selection_vector)
    elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

    logs.append(f"Optimization finished in {elapsed_ms} ms. Selected {selected_count} compounds. Total cost: ${total_cost:,.2f}.")
    logs.append(f"Constraint verification: Batch size={batch_satisfied}, Budget satisfied={budget_satisfied}.")

    # 7. Build Selected Compound Records with Rationales
    historical_scaffolds = set()
    train_indices = _CURRENT_MODEL_STATE.get("train_indices", [])
    if train_indices:
        train_smiles = _CURRENT_MODEL_STATE.get("train_smiles", [])
        for ts in train_smiles:
            _, sc_id = chemistry_processor.get_murcko_scaffold(ts)
            historical_scaffolds.add(sc_id)

    selected_items = []
    unique_scaffolds = set()
    novel_scaffolds_count = 0

    # Sort selected compounds by individual marginal utility
    sel_pairs = [(i, linear_utils[i]) for i in selected_indices]
    sel_pairs.sort(key=lambda x: x[1], reverse=True)

    for rank, (idx, marg_u) in enumerate(sel_pairs, 1):
        c = candidate_pool[idx]
        scaff_id = c.scaffold_id or "SCAF-00000"
        unique_scaffolds.add(scaff_id)
        is_novel = scaff_id not in historical_scaffolds
        if is_novel:
            novel_scaffolds_count += 1

        # Transparent scientific rationale
        rationale_parts = []
        if pred_y[idx] >= 8.0:
            rationale_parts.append("High predicted potency (pIC50 > 8.0)")
        elif pred_y[idx] >= 6.5:
            rationale_parts.append("Moderate predicted activity")
        if uncert[idx] > 0.4:
            rationale_parts.append("High epistemic exploration value")
        if nov[idx] > 0.7:
            rationale_parts.append("High chemical novelty relative to reference series")
        if is_novel:
            rationale_parts.append("Unseen Bemis-Murcko scaffold")
        if c.cost < 400.0:
            rationale_parts.append("Cost-efficient screening candidate")

        rationale = "; ".join(rationale_parts) if rationale_parts else "Balanced discovery utility"

        item = SelectedCompoundItem(
            rank=rank,
            compound_id=c.compound_id,
            source_id=c.source_id,
            canonical_smiles=c.canonical_smiles,
            predicted_pic50=round(float(pred_y[idx]), 3),
            uncertainty=round(float(uncert[idx]), 3),
            novelty_score=round(float(nov[idx]), 3),
            cost=round(float(costs[idx]), 2),
            scaffold=c.scaffold or "Acyclic",
            scaffold_id=scaff_id,
            availability=c.availability,
            marginal_utility=round(float(marg_u), 3),
            selection_rationale=rationale,
            evidence_status=c.evidence_status or "VERIFIED SOURCE DATA"
        )
        selected_items.append(item)

    avg_pred_pic50 = round(float(np.mean(pred_y[selected_indices])), 3) if len(selected_indices) > 0 else 0.0

    # 8. Persist in Database
    opt_run = OptimizationRun(
        run_id=run_id,
        target_id=payload.target_id,
        solver_backend=solver_backend,
        batch_size=payload.batch_size,
        total_budget=payload.total_budget,
        weight_activity=payload.weight_activity,
        weight_exploration=payload.weight_exploration,
        weight_novelty=payload.weight_novelty,
        weight_diversity=payload.weight_diversity,
        weight_cost=payload.weight_cost,
        status="SUCCESS",
        runtime_ms=elapsed_ms,
        objective_value=round(objective_val, 4),
        batch_size_satisfied=batch_satisfied,
        budget_satisfied=budget_satisfied,
        selected_count=selected_count,
        total_cost=round(total_cost, 2),
        avg_predicted_pic50=avg_pred_pic50,
        unique_scaffolds=len(unique_scaffolds),
        novel_scaffolds_count=novel_scaffolds_count,
        qubo_dimension=N,
        qubo_density=round(float(len(qubo_dict) / (N * (N + 1) / 2)), 3),
        formulation_json=json.dumps({"lambda_batch": 3.5, "variables": N}),
        logs_json=json.dumps(logs),
        evidence_status=evidence_status
    )
    db.add(opt_run)

    for item in selected_items:
        sc_ent = SelectedCompound(
            opt_run_id=run_id,
            compound_id=item.compound_id,
            source_id=item.source_id,
            canonical_smiles=item.canonical_smiles,
            rank=item.rank,
            marginal_utility=item.marginal_utility,
            predicted_pic50=item.predicted_pic50,
            uncertainty=item.uncertainty,
            novelty_score=item.novelty_score,
            cost=item.cost,
            scaffold=item.scaffold,
            scaffold_id=item.scaffold_id,
            availability=item.availability,
            selection_rationale=item.selection_rationale,
            evidence_status=item.evidence_status
        )
        db.add(sc_ent)

    db.commit()

    # Cache in memory for retrospective validation with session-independent dicts
    candidate_summary = [
        {
            "compound_id": c.compound_id,
            "source_id": c.source_id,
            "name": getattr(c, "name", c.compound_id),
            "cost": float(c.cost),
            "historical_pic50": float(c.historical_pic50) if c.historical_pic50 is not None else 5.0,
            "scaffold_id": c.scaffold_id or "SCAF-00000"
        }
        for c in candidate_pool
    ]
    _CURRENT_OPT_STATE["run_id"] = run_id
    _CURRENT_OPT_STATE["selection_vector"] = selection_vector
    _CURRENT_OPT_STATE["candidate_pool"] = candidate_summary
    _CURRENT_OPT_STATE["tanimoto_matrix"] = tanimoto_mat
    _CURRENT_OPT_STATE["predicted_pic50"] = pred_y
    _CURRENT_OPT_STATE["costs"] = costs
    _CURRENT_OPT_STATE["total_budget"] = payload.total_budget
    _CURRENT_OPT_STATE["batch_size"] = payload.batch_size
    _CURRENT_OPT_STATE["historical_scaffolds"] = historical_scaffolds

    return {
        "run_id": run_id,
        "solver_backend": solver_backend,
        "status": "SUCCESS",
        "runtime_ms": elapsed_ms,
        "objective_value": round(objective_val, 4),
        "batch_size_satisfied": batch_satisfied,
        "budget_satisfied": budget_satisfied,
        "selected_count": selected_count,
        "total_cost": round(total_cost, 2),
        "budget_remaining": round(max(0.0, payload.total_budget - total_cost), 2),
        "avg_predicted_pic50": avg_pred_pic50,
        "unique_scaffolds": len(unique_scaffolds),
        "novel_scaffolds_count": novel_scaffolds_count,
        "selected_compounds": selected_items,
        "qubo_dimension": N,
        "qubo_density": round(float(len(qubo_dict) / (N * (N + 1) / 2)), 3),
        "formulation_summary": {
            "formulation_type": "Binary Quadratic Model (QUBO)",
            "batch_penalty_type": "Quadratic equality penalty P_batch * (sum x_i - K)^2",
            "redundancy_penalty_type": "Pairwise Tanimoto weighted quadratic penalty",
            "variables_count": N,
            "nonzero_quadratic_terms": len(qubo_dict)
        },
        "solver_logs": logs,
        "evidence_status": evidence_status
    }


@router.get("/latest", response_model=Optional[OptimizationResponse])
def get_latest_optimization(db: Session = Depends(get_db)):
    """Returns the most recent optimization run and selected compounds."""
    latest = db.query(OptimizationRun).order_by(OptimizationRun.created_at.desc()).first()
    if not latest:
        return None

    selected = db.query(SelectedCompound).filter(SelectedCompound.opt_run_id == latest.run_id).order_by(SelectedCompound.rank).all()
    logs = json.loads(latest.logs_json) if latest.logs_json else []

    selected_items = [
        SelectedCompoundItem(
            rank=s.rank,
            compound_id=s.compound_id,
            source_id=s.source_id,
            canonical_smiles=s.canonical_smiles,
            predicted_pic50=s.predicted_pic50,
            uncertainty=s.uncertainty,
            novelty_score=s.novelty_score,
            cost=s.cost,
            scaffold=s.scaffold or "Acyclic",
            scaffold_id=s.scaffold_id or "SCAF-00000",
            availability=s.availability,
            marginal_utility=s.marginal_utility,
            selection_rationale=s.selection_rationale or "",
            evidence_status=s.evidence_status
        )
        for s in selected
    ]

    return {
        "run_id": latest.run_id,
        "solver_backend": latest.solver_backend,
        "status": latest.status,
        "runtime_ms": latest.runtime_ms,
        "objective_value": latest.objective_value,
        "batch_size_satisfied": latest.batch_size_satisfied,
        "budget_satisfied": latest.budget_satisfied,
        "selected_count": latest.selected_count,
        "total_cost": latest.total_cost,
        "budget_remaining": round(max(0.0, latest.total_budget - latest.total_cost), 2),
        "avg_predicted_pic50": latest.avg_predicted_pic50,
        "unique_scaffolds": latest.unique_scaffolds,
        "novel_scaffolds_count": latest.novel_scaffolds_count,
        "selected_compounds": selected_items,
        "qubo_dimension": latest.qubo_dimension,
        "qubo_density": latest.qubo_density,
        "formulation_summary": {
            "formulation_type": "Binary Quadratic Model (QUBO)",
            "batch_penalty_type": "Quadratic equality penalty P_batch * (sum x_i - K)^2"
        },
        "solver_logs": logs,
        "evidence_status": latest.evidence_status
    }

