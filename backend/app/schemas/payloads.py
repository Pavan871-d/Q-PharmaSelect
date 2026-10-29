"""
Pydantic Schemas and DTOs for Q-PharmaSelect API.
Defines strict data contracts for scientific inputs, model runs, quantum circuits, and optimization.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Target & Assay Schemas
# ============================================================================

class TargetCreate(BaseModel):
    name: str = Field(..., example="EGFR (Epidermal Growth Factor Receptor)")
    target_id: str = Field(..., example="CHEMBL203")
    organism: str = Field(default="Homo sapiens")
    uniprot_id: Optional[str] = Field(default="P00533")
    description: Optional[str] = Field(default="Receptor tyrosine kinase binding ligands of the EGF family")


class TargetResponse(TargetCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssayCreate(BaseModel):
    target_id: str = Field(..., example="CHEMBL203")
    assay_id: str = Field(..., example="CHEMBL615112")
    assay_name: str = Field(..., example="EGFR Tyrosine Kinase Biochemical Inhibition Assay")
    assay_type: str = Field(default="Biochemical", example="Biochemical")  # Biochemical vs Cell-based
    endpoint: str = Field(default="IC50", example="IC50")  # IC50, Ki, EC50, etc.
    endpoint_unit: str = Field(default="nM", example="nM")
    activity_direction: str = Field(default="LOWER_IS_BETTER", example="LOWER_IS_BETTER")
    activity_threshold_value: float = Field(default=1000.0, description="In endpoint units (e.g. 1000 nM)")
    activity_threshold_pic50: float = Field(default=6.0, description="Converted pIC50 threshold")
    cost_per_compound: float = Field(default=450.0, description="Cost in currency")
    currency: str = Field(default="USD")


class AssayResponse(AssayCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Compound & Provenance Schemas
# ============================================================================

class CompoundBase(BaseModel):
    compound_id: str = Field(..., example="QPS-001")
    source_id: str = Field(..., example="CHEMBL28")
    canonical_smiles: str = Field(..., example="COc1cc2c(ncnc2cc1OC)Nc3cccc(c3)C#C")
    source_database: str = Field(default="ChEMBL")
    source_url: Optional[str] = Field(default="https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL28/")
    cost: float = Field(default=450.0)
    availability: str = Field(default="AVAILABLE", example="AVAILABLE")  # AVAILABLE, UNAVAILABLE, UNKNOWN
    evidence_status: str = Field(default="VERIFIED SOURCE DATA")  # VERIFIED SOURCE DATA, USER-PROVIDED DATA, SYNTHETIC DEMONSTRATION DATA


class CompoundDetail(CompoundBase):
    id: int
    molecular_formula: Optional[str] = None
    mw: Optional[float] = None
    logp: Optional[float] = None
    tpsa: Optional[float] = None
    hbd: Optional[int] = None
    hba: Optional[int] = None
    rotatable_bonds: Optional[int] = None
    ring_count: Optional[int] = None
    scaffold: Optional[str] = None
    scaffold_id: Optional[str] = None
    pca_x: Optional[float] = None
    pca_y: Optional[float] = None
    historical_pic50: Optional[float] = None
    is_historical_hit: Optional[bool] = None

    class Config:
        from_attributes = True


class DatasetSummary(BaseModel):
    total_compounds: int
    total_scaffolds: int
    scaffold_diversity_ratio: float
    total_observations: int
    available_count: int
    unavailable_count: int
    unknown_availability_count: int
    avg_cost: float
    cost_range: List[float]
    evidence_breakdown: Dict[str, int]
    target: Optional[str] = None
    assay: Optional[str] = None


# ============================================================================
# Machine Learning & Uncertainty Schemas
# ============================================================================

class ModelTrainRequest(BaseModel):
    target_id: str = "CHEMBL203"
    assay_id: str = "CHEMBL615112"
    model_type: str = Field(default="random_forest", example="random_forest")  # random_forest, gradient_boosting, quantum_hybrid
    split_method: str = Field(default="scaffold_split", example="scaffold_split")  # scaffold_split, random_split
    test_size: float = Field(default=0.25, ge=0.1, le=0.5)
    random_seed: int = Field(default=42)
    n_estimators: int = Field(default=100)


class ModelEvaluationMetrics(BaseModel):
    r2: float
    rmse: float
    mae: float
    spearman_corr: float
    pearson_corr: float
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    num_train: int
    num_test: int
    model_type: str
    split_method: str
    calibration_slope: Optional[float] = None
    ood_compounds_count: Optional[int] = 0


class PredictionItem(BaseModel):
    compound_id: str
    source_id: str
    canonical_smiles: str
    predicted_pic50: float
    uncertainty: float
    ood_score: float
    is_predicted_active: bool
    novelty_score: float
    scaffold_id: str
    cost: float
    availability: str


# ============================================================================
# Quantum Machine Learning Schemas (QpiAI QCloud)
# ============================================================================

class QuantumRunRequest(BaseModel):
    target_id: str = "CHEMBL203"
    backend_name: str = Field(default="QpiAI-QSV-Simulator", example="QpiAI-QSV-Simulator")
    num_qubits: int = Field(default=6, ge=2, le=12)
    num_shots: int = Field(default=1024, ge=100, le=8192)
    feature_reduction_method: str = Field(default="PCA", example="PCA")
    random_seed: int = 42


class QuantumRunResponse(BaseModel):
    run_id: str
    backend_name: str
    status: str  # SUCCESS, INTEGRATION_PENDING, FAILED
    sdk_version: str
    num_qubits: int
    circuit_depth: int
    num_shots: int
    execution_time_ms: float
    qasm_preview: str
    measurement_counts_summary: Dict[str, int]
    classical_baseline_rmse: float
    quantum_hybrid_rmse: float
    classical_baseline_r2: float
    quantum_hybrid_r2: float
    evidence_status: str
    logs: List[str]


# ============================================================================
# Constrained Optimization Schemas (QpiAI Opt)
# ============================================================================

class OptimizationRequest(BaseModel):
    target_id: str = "CHEMBL203"
    batch_size: int = Field(default=15, ge=3, le=50)
    total_budget: float = Field(default=10000.0, ge=500.0)
    weight_activity: float = Field(default=1.0, ge=0.0, le=5.0)
    weight_exploration: float = Field(default=0.5, ge=0.0, le=5.0)
    weight_novelty: float = Field(default=0.8, ge=0.0, le=5.0)
    weight_diversity: float = Field(default=0.7, ge=0.0, le=5.0)  # Redundancy penalty weight
    weight_cost: float = Field(default=0.3, ge=0.0, le=5.0)
    solver_mode: str = Field(default="QPIAI_OPT_AUTO", example="QPIAI_OPT_AUTO")  # QPIAI_OPT_AUTO, CLASSICAL_SA, EXHAUSTIVE
    unknown_availability_policy: str = Field(default="EXCLUDE", example="EXCLUDE")  # EXCLUDE, INCLUDE, PENALIZE
    random_seed: int = 42


class SelectedCompoundItem(BaseModel):
    rank: int
    compound_id: str
    source_id: str
    canonical_smiles: str
    predicted_pic50: float
    uncertainty: float
    novelty_score: float
    cost: float
    scaffold: str
    scaffold_id: str
    availability: str
    marginal_utility: float
    selection_rationale: str
    evidence_status: str


class OptimizationResponse(BaseModel):
    run_id: str
    solver_backend: str
    status: str
    runtime_ms: float
    objective_value: float
    batch_size_satisfied: bool
    budget_satisfied: bool
    selected_count: int
    total_cost: float
    budget_remaining: float
    avg_predicted_pic50: float
    unique_scaffolds: int
    novel_scaffolds_count: int
    selected_compounds: List[SelectedCompoundItem]
    qubo_dimension: int
    qubo_density: float
    formulation_summary: Dict[str, Any]
    solver_logs: List[str]
    evidence_status: str


# ============================================================================
# Retrospective Validation Schemas
# ============================================================================

class BaselineComparisonItem(BaseModel):
    strategy_name: str
    enrichment_factor: float
    hit_rate: float
    observed_hits: int
    total_cost: float
    cost_per_hit: float
    novel_scaffold_count: int
    scaffold_diversity_ratio: float
    total_observed_utility: float
    batch_size_valid: bool
    budget_valid: bool
    runtime_ms: float


class ValidationRunResponse(BaseModel):
    validation_id: str
    optimization_run_id: str
    evaluated_batch_size: int
    total_held_out_candidates: int
    held_out_hit_prevalence: float
    selected_batch_observed_hits: int
    selected_batch_hit_rate: float
    selected_batch_enrichment_factor: float
    selected_batch_novel_scaffolds: int
    selected_batch_novel_scaffold_pct: float
    selected_batch_total_cost: float
    selected_batch_cost_efficiency: float
    baselines: List[BaselineComparisonItem]
    leakage_check_passed: bool
    evidence_status: str
    evaluation_summary: str

