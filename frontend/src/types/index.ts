export interface Compound {
  id: number;
  compound_id: string;
  source_id: string;
  canonical_smiles: string;
  molecular_formula?: string;
  mw?: number;
  logp?: number;
  tpsa?: number;
  hbd?: number;
  hba?: number;
  rotatable_bonds?: number;
  ring_count?: number;
  scaffold?: string;
  scaffold_id?: string;
  source_database: string;
  source_url?: string;
  cost: number;
  availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  evidence_status: string;
  pca_x?: number;
  pca_y?: number;
  historical_pic50?: number;
  is_historical_hit?: boolean;
}

export interface DatasetSummary {
  total_compounds: number;
  total_scaffolds: number;
  scaffold_diversity_ratio: number;
  total_observations: number;
  available_count: number;
  unavailable_count: number;
  unknown_availability_count: number;
  avg_cost: number;
  cost_range: [number, number];
  evidence_breakdown: Record<string, number>;
  target?: string;
  assay?: string;
}

export interface ModelMetrics {
  r2: number;
  rmse: number;
  mae: number;
  spearman_corr: number;
  pearson_corr: number;
  roc_auc?: number;
  pr_auc?: number;
  num_train: number;
  num_test: number;
  model_type: string;
  split_method: string;
  calibration_slope?: number;
  ood_compounds_count?: number;
}

export interface QuantumRunResult {
  run_id: string;
  backend_name: string;
  status: string;
  sdk_version: string;
  num_qubits: number;
  circuit_depth: number;
  num_shots: number;
  execution_time_ms: number;
  qasm_preview: string;
  measurement_counts_summary: Record<string, number>;
  classical_baseline_rmse: number;
  quantum_hybrid_rmse: number;
  classical_baseline_r2: number;
  quantum_hybrid_r2: number;
  evidence_status: string;
  logs: string[];
}

export interface SelectedCompoundItem {
  rank: number;
  compound_id: string;
  source_id: string;
  canonical_smiles: string;
  predicted_pic50: number;
  uncertainty: number;
  novelty_score: number;
  cost: number;
  scaffold: string;
  scaffold_id: string;
  availability: string;
  marginal_utility: number;
  selection_rationale: string;
  evidence_status: string;
}

export interface OptimizationResult {
  run_id: string;
  solver_backend: string;
  status: string;
  runtime_ms: number;
  objective_value: number;
  batch_size_satisfied: boolean;
  budget_satisfied: boolean;
  selected_count: number;
  total_cost: number;
  budget_remaining: number;
  avg_predicted_pic50: number;
  unique_scaffolds: number;
  novel_scaffolds_count: number;
  selected_compounds: SelectedCompoundItem[];
  qubo_dimension: number;
  qubo_density: number;
  formulation_summary: Record<string, any>;
  solver_logs: string[];
  evidence_status: string;
}

export interface BaselineComparison {
  strategy_name: string;
  enrichment_factor: number;
  hit_rate: number;
  observed_hits: number;
  total_cost: number;
  cost_per_hit: number;
  novel_scaffold_count: number;
  scaffold_diversity_ratio: number;
  total_observed_utility: number;
  batch_size_valid: boolean;
  budget_valid: boolean;
  runtime_ms: number;
}

export interface ValidationResult {
  validation_id: string;
  optimization_run_id: string;
  evaluated_batch_size: number;
  total_held_out_candidates: number;
  held_out_hit_prevalence: number;
  selected_batch_observed_hits: number;
  selected_batch_hit_rate: number;
  selected_batch_enrichment_factor: number;
  selected_batch_novel_scaffolds: number;
  selected_batch_novel_scaffold_pct: number;
  selected_batch_total_cost: number;
  selected_batch_cost_efficiency: number;
  baselines: BaselineComparison[];
  leakage_check_passed: boolean;
  evidence_status: string;
  evaluation_summary: string;
}

export interface IntegrationStatus {
  qcloud: {
    sdk_available: boolean;
    sdk_version: string;
    has_api_key: boolean;
    auth_status: string;
    auth_user?: string;
    supported_devices: string[];
  };
  qpiai_opt: {
    sdk_available: boolean;
    has_api_key: boolean;
    opt_url: string;
    status: string;
    supported_formulations: string[];
  };
  runtime_environment: {
    environment: string;
    database_url: string;
    python_packages: Record<string, string>;
  };
}

