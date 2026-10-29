import {
  DatasetSummary,
  Compound,
  ModelMetrics,
  QuantumRunResult,
  OptimizationResult,
  ValidationResult,
  IntegrationStatus
} from '../types';

const API_BASE = '/api';

export const api = {
  // Health
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  // Data
  getDatasetSummary: async (): Promise<DatasetSummary> => {
    const res = await fetch(`${API_BASE}/data/summary`);
    if (!res.ok) throw new Error('Failed to fetch dataset summary');
    return res.json();
  },

  getCompounds: async (skip = 0, limit = 50, search?: string, scaffoldId?: string): Promise<Compound[]> => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (search) params.append('search', search);
    if (scaffoldId) params.append('scaffold_id', scaffoldId);
    const res = await fetch(`${API_BASE}/data/compounds?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch compounds');
    return res.json();
  },

  getCompoundDetail: async (compoundId: string): Promise<Compound> => {
    const res = await fetch(`${API_BASE}/data/compounds/${compoundId}`);
    if (!res.ok) throw new Error('Failed to fetch compound');
    return res.json();
  },

  uploadCsv: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/data/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'CSV upload failed');
    }
    return res.json();
  },

  // Models
  trainModel: async (params: {
    model_type: string;
    split_method: string;
    test_size?: number;
    random_seed?: number;
  }): Promise<ModelMetrics> => {
    const res = await fetch(`${API_BASE}/models/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Training failed');
    }
    return res.json();
  },

  getLatestModel: async (): Promise<ModelMetrics | null> => {
    const res = await fetch(`${API_BASE}/models/latest`);
    if (!res.ok) return null;
    return res.json();
  },

  // Quantum
  runQuantumExperiment: async (params: {
    backend_name: string;
    num_qubits: number;
    num_shots: number;
  }): Promise<QuantumRunResult> => {
    const res = await fetch(`${API_BASE}/quantum/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Quantum run failed');
    }
    return res.json();
  },

  getLatestQuantumRun: async (): Promise<QuantumRunResult | null> => {
    const res = await fetch(`${API_BASE}/quantum/latest`);
    if (!res.ok) return null;
    return res.json();
  },

  // Optimization
  runOptimization: async (params: {
    batch_size: number;
    total_budget: number;
    weight_activity: number;
    weight_exploration: number;
    weight_novelty: number;
    weight_diversity: number;
    weight_cost: number;
    solver_mode?: string;
    unknown_availability_policy?: string;
  }): Promise<OptimizationResult> => {
    const res = await fetch(`${API_BASE}/optimization/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Optimization failed');
    }
    return res.json();
  },

  getLatestOptimization: async (): Promise<OptimizationResult | null> => {
    const res = await fetch(`${API_BASE}/optimization/latest`);
    if (!res.ok) return null;
    return res.json();
  },

  // Validation
  runValidation: async (): Promise<ValidationResult> => {
    const res = await fetch(`${API_BASE}/validation/run`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Validation failed');
    }
    return res.json();
  },

  getLatestValidation: async (): Promise<ValidationResult | null> => {
    const res = await fetch(`${API_BASE}/validation/latest`);
    if (!res.ok) return null;
    return res.json();
  },

  // Integrations & Diagnostics
  getIntegrationsStatus: async (): Promise<IntegrationStatus> => {
    const res = await fetch(`${API_BASE}/integrations/status`);
    if (!res.ok) throw new Error('Failed to fetch integration status');
    return res.json();
  },

  updateCredentials: async (credentials: {
    qpiai_qcloud_api_key?: string;
    qpiai_opt_api_key?: string;
  }): Promise<any> => {
    const res = await fetch(`${API_BASE}/integrations/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    return res.json();
  },

  // Export URLs
  getSelectedCsvUrl: () => `${API_BASE}/reports/export/selected-csv`,
  getFullJsonReport: async () => {
    const res = await fetch(`${API_BASE}/reports/export/full-json`);
    return res.json();
  }
};

