"""
SQLAlchemy ORM Entities for Q-PharmaSelect.
Maintains full relational structure for targets, assays, compounds, predictions, quantum runs, and optimizations.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from ..db.session import Base


class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String(64), unique=True, index=True, nullable=False)  # e.g. CHEMBL203
    name = Column(String(255), nullable=False)
    organism = Column(String(128), default="Homo sapiens")
    uniprot_id = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assays = relationship("Assay", back_populates="target", cascade="all, delete-orphan")


class Assay(Base):
    __tablename__ = "assays"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String(64), ForeignKey("targets.target_id"), nullable=False)
    assay_id = Column(String(64), unique=True, index=True, nullable=False)
    assay_name = Column(String(255), nullable=False)
    assay_type = Column(String(64), default="Biochemical")  # Biochemical or Cell-based
    endpoint = Column(String(32), default="IC50")  # IC50, Ki, EC50
    endpoint_unit = Column(String(32), default="nM")
    activity_direction = Column(String(32), default="LOWER_IS_BETTER")
    activity_threshold_value = Column(Float, default=1000.0)
    activity_threshold_pic50 = Column(Float, default=6.0)
    cost_per_compound = Column(Float, default=450.0)
    currency = Column(String(16), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)

    target = relationship("Target", back_populates="assays")


class Compound(Base):
    __tablename__ = "compounds"

    id = Column(Integer, primary_key=True, index=True)
    compound_id = Column(String(64), unique=True, index=True, nullable=False)
    source_id = Column(String(64), index=True, nullable=False)  # e.g. CHEMBL ID
    canonical_smiles = Column(Text, nullable=False)
    molecular_formula = Column(String(128), nullable=True)
    mw = Column(Float, nullable=True)
    logp = Column(Float, nullable=True)
    tpsa = Column(Float, nullable=True)
    hbd = Column(Integer, nullable=True)
    hba = Column(Integer, nullable=True)
    rotatable_bonds = Column(Integer, nullable=True)
    ring_count = Column(Integer, nullable=True)
    scaffold = Column(Text, nullable=True)
    scaffold_id = Column(String(64), index=True, nullable=True)
    source_database = Column(String(64), default="ChEMBL")
    source_url = Column(Text, nullable=True)
    cost = Column(Float, default=450.0)
    availability = Column(String(32), default="AVAILABLE")  # AVAILABLE, UNAVAILABLE, UNKNOWN
    evidence_status = Column(String(64), default="VERIFIED SOURCE DATA")
    pca_x = Column(Float, nullable=True)
    pca_y = Column(Float, nullable=True)
    historical_pic50 = Column(Float, nullable=True)
    is_historical_hit = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssayObservation(Base):
    __tablename__ = "assay_observations"

    id = Column(Integer, primary_key=True, index=True)
    compound_id = Column(String(64), ForeignKey("compounds.compound_id"), nullable=False)
    assay_id = Column(String(64), nullable=False)
    endpoint = Column(String(32), default="IC50")
    raw_value = Column(Float, nullable=False)
    raw_unit = Column(String(32), default="nM")
    converted_pic50 = Column(Float, nullable=False)
    assay_date = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False)
    split = Column(String(32), default="UNASSIGNED")  # TRAIN, TEST, VALIDATION
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    target_id = Column(String(64), nullable=False)
    assay_id = Column(String(64), nullable=False)
    model_type = Column(String(64), nullable=False)
    split_method = Column(String(64), nullable=False)
    test_size = Column(Float, default=0.25)
    random_seed = Column(Integer, default=42)
    num_train = Column(Integer, nullable=False)
    num_test = Column(Integer, nullable=False)
    r2 = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    spearman = Column(Float, nullable=False)
    pearson = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    calibration_slope = Column(Float, nullable=True)
    ood_count = Column(Integer, default=0)
    parameters_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuantumRun(Base):
    __tablename__ = "quantum_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    target_id = Column(String(64), nullable=False)
    backend_name = Column(String(64), nullable=False)
    num_qubits = Column(Integer, nullable=False)
    circuit_depth = Column(Integer, nullable=False)
    num_shots = Column(Integer, nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    status = Column(String(32), nullable=False)  # SUCCESS, INTEGRATION_PENDING, FAILED
    qasm_code = Column(Text, nullable=True)
    counts_json = Column(Text, nullable=True)
    baseline_rmse = Column(Float, default=0.0)
    quantum_rmse = Column(Float, default=0.0)
    baseline_r2 = Column(Float, default=0.0)
    quantum_r2 = Column(Float, default=0.0)
    logs_json = Column(Text, nullable=True)
    evidence_status = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    target_id = Column(String(64), nullable=False)
    solver_backend = Column(String(64), nullable=False)
    batch_size = Column(Integer, nullable=False)
    total_budget = Column(Float, nullable=False)
    weight_activity = Column(Float, nullable=False)
    weight_exploration = Column(Float, nullable=False)
    weight_novelty = Column(Float, nullable=False)
    weight_diversity = Column(Float, nullable=False)
    weight_cost = Column(Float, nullable=False)
    status = Column(String(32), nullable=False)
    runtime_ms = Column(Float, nullable=False)
    objective_value = Column(Float, nullable=False)
    batch_size_satisfied = Column(Boolean, default=True)
    budget_satisfied = Column(Boolean, default=True)
    selected_count = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    avg_predicted_pic50 = Column(Float, nullable=False)
    unique_scaffolds = Column(Integer, nullable=False)
    novel_scaffolds_count = Column(Integer, nullable=False)
    qubo_dimension = Column(Integer, default=0)
    qubo_density = Column(Float, default=0.0)
    formulation_json = Column(Text, nullable=True)
    logs_json = Column(Text, nullable=True)
    evidence_status = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SelectedCompound(Base):
    __tablename__ = "selected_compounds"

    id = Column(Integer, primary_key=True, index=True)
    opt_run_id = Column(String(64), ForeignKey("optimization_runs.run_id"), nullable=False)
    compound_id = Column(String(64), nullable=False)
    source_id = Column(String(64), nullable=False)
    canonical_smiles = Column(Text, nullable=False)
    rank = Column(Integer, nullable=False)
    marginal_utility = Column(Float, nullable=False)
    predicted_pic50 = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)
    novelty_score = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    scaffold = Column(Text, nullable=True)
    scaffold_id = Column(String(64), nullable=True)
    availability = Column(String(32), default="AVAILABLE")
    selection_rationale = Column(Text, nullable=True)
    evidence_status = Column(String(64), default="VERIFIED SOURCE DATA")


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    validation_id = Column(String(64), unique=True, index=True, nullable=False)
    opt_run_id = Column(String(64), ForeignKey("optimization_runs.run_id"), nullable=False)
    evaluated_batch_size = Column(Integer, nullable=False)
    total_held_out_candidates = Column(Integer, nullable=False)
    held_out_hit_prevalence = Column(Float, nullable=False)
    observed_hits = Column(Integer, nullable=False)
    hit_rate = Column(Float, nullable=False)
    enrichment_factor = Column(Float, nullable=False)
    novel_scaffolds = Column(Integer, nullable=False)
    novel_scaffold_pct = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    cost_efficiency = Column(Float, nullable=False)
    baselines_json = Column(Text, nullable=True)
    leakage_check_passed = Column(Boolean, default=True)
    evidence_status = Column(String(64), nullable=False)
    evaluation_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

