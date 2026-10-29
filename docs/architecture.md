# Q-PharmaSelect System Architecture

## 1. Executive Summary

**Q-PharmaSelect** (*"Discover smarter. Test fewer. Learn faster."*) is a production-grade research prototype designed for assay-constrained compound selection in drug discovery (Challenge **QML-04**).

The system addresses the complete experimental decision-support lifecycle:
1. Ingesting bioassay records with strict unit validation (IC50 / Kd / Ki $\to$ pIC50).
2. Cheminformatics processing via RDKit (canonicalization, Bemis-Murcko scaffolds, ECFP4 Morgan fingerprints).
3. Leakage-free scaffold splitting and hybrid quantum-classical predictive modeling via **QpiAI QCloud / Quantum SDK**.
4. Epistemic uncertainty estimation and out-of-distribution (OOD) novelty scoring.
5. Multi-objective combinatorial batch optimization under capacity and budget constraints using **QpiAI Opt**.
6. Retrospective enrichment analysis on held-out assay observations against three classical baselines.
7. Transparent provenance audit logging and full data dossier export.

---

## 2. High-Level System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                  USER / RESEARCHER INTERFACE                                      |
|                 React 18 + TypeScript + Vite + Tailwind CSS + Lucide + Charting (Port 5173)       |
+---------------------------------------------------------------------------------------------------+
                                                  |  REST API / JSON
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                     FASTAPI BACKEND (Port 8000)                                   |
|  /api/health  |  /api/targets  |  /api/data  |  /api/models  |  /api/quantum  |  /api/optimization |
+---------------------------------------------------------------------------------------------------+
         |                                |                                   |
         v                                v                                   v
+------------------+             +------------------+             +-------------------------+
| CHEMINFORMATICS  |             |  QUANTUM ENGINE  |             |   OPTIMIZATION ENGINE   |
|   (RDKit Core)   |             | (QpiAI QCloud)   |             |       (QpiAI Opt)       |
|                  |             |                  |             |                         |
| - SMILES Canon   |             | - QpiAI SDK      |             | - QUBO Formulation      |
| - ECFP4 (1024b)  |             | - Angle Encoding |             | - Batch Penalty         |
| - Murcko Scaff   |             | - CNOT Entangle  |             | - Tanimoto Diversity    |
| - Tanimoto Mat   |             | - QSV Simulator  |             | - Budget Constraints    |
| - 2D PCA Embed   |             | - OpenQASM 2.0   |             | - Simulated Annealing   |
+------------------+             +------------------+             +-------------------------+
         |                                |                                   |
         +--------------------------------+-----------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       RETROSPECTIVE VALIDATOR         |
                      | - Zero-Leakage Scaffold Evaluation    |
                      | - Enrichment Factor (EF_f)            |
                      | - Novel Scaffold Count & %            |
                      | - Cost Efficiency (Hits / $1,000)     |
                      | - Baseline Comparison (Greedy/Random) |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |         PERSISTENCE & EXPORT          |
                      | - SQLite Database (qpharmaselect.db)  |
                      | - JSON Audit Dossier Export           |
                      | - Selected Batch CSV Export           |
                      +---------------------------------------+
```

---

## 3. Technology Stack

| Layer | Component | Technology | Version | Purpose |
|---|---|---|---|---|
| **Frontend** | Framework | React + TypeScript | 18.3.1 | Responsive scientific user interface |
| | Build Tool | Vite | 5.4.21 | Hot module replacement & fast bundling |
| | Styling | Tailwind CSS | 3.4.1 | Production design system & badges |
| | Icons | Lucide React | 0.344.0 | UI iconography |
| **Backend** | Framework | FastAPI | 0.115.11 | High-throughput asynchronous REST API |
| | Validation | Pydantic | 2.11.1 | Strict schema contracts & data validation |
| | Server | Uvicorn | 0.34.0 | ASGI web server |
| **Cheminformatics** | Core | RDKit | 2026.9.1 | Molecular descriptors, Morgan ECFP4, Bemis-Murcko scaffolds |
| | Numerics | NumPy / SciPy | 2.2.3 / 1.15.2 | Vectorized similarity matrices & statistics |
| | Machine Learning | Scikit-learn | 1.6.1 | Random Forest, Gradient Boosting, PCA |
| **Quantum** | QCloud SDK | `qpiai-quantum` | 0.7.5 | Quantum circuit synthesis, angle rotation, simulator execution |
| **Optimization** | Opt SDK | `qpiai-opt-api` | 1.0.6 | QUBOProblem representation & cloud solver interface |
| **Database** | ORM | SQLAlchemy | 2.1.6 | Entity persistence & session lifecycle |
| | Engine | SQLite | 3.x | Local zero-config embedded ACID database |

---

## 4. Database Schema Specification

The relational persistence model contains 8 primary entities:

1. **`targets`**: Biological target metadata (`target_id`, `name`, `organism`, `uniprot_id`, `description`).
2. **`assays`**: Assay experimental configuration (`assay_id`, `target_id`, `endpoint`, `endpoint_unit`, `activity_direction`, `activity_threshold_pic50`, `cost_per_compound`).
3. **`compounds`**: Library molecules (`compound_id`, `source_id`, `name`, `smiles`, `canonical_smiles`, `scaffold_smiles`, `scaffold_id`, `cost`, `availability`, `lead_time_days`, `molecular_weight`, `logp`, `tpsa`, `hbd`, `hba`, `pca_x`, `pca_y`).
4. **`assay_observations`**: Experimental measurements linked to compounds (`compound_id`, `assay_id`, `raw_endpoint_value`, `endpoint_unit`, `converted_pic50`, `is_active`, `is_held_out`, `evidence_status`).
5. **`model_runs`**: Predictive model training records (`model_id`, `model_type`, `split_method`, `r2`, `rmse`, `mae`, `spearman_corr`, `train_count`, `test_count`).
6. **`quantum_runs`**: QpiAI Quantum execution audits (`run_id`, `sdk_version`, `backend_name`, `num_qubits`, `circuit_depth`, `shots`, `execution_status`, `qml_rmse`, `classical_rmse`, `qasm_code`).
7. **`optimization_runs`**: Batch selection optimization runs (`run_id`, `solver_name`, `target_batch_size`, `total_budget`, `selected_count`, `total_cost`, `qubo_energy`, `batch_satisfied`, `budget_satisfied`).
8. **`selected_compounds`**: Junction table mapping selected compounds to optimization runs with marginal utility breakdown.

---

## 5. Security & Sandbox Boundary Compliance

- Local development uses standard localhost loopback (`127.0.0.1:8000` for backend, `127.0.0.1:5173` for frontend).
- API keys for QpiAI Quantum and QpiAI Opt are passed via environment variables or frontend session headers and are never persisted in source control or cleartext database tables.
- All SMILES input undergoes sanitization and RDKit valence verification prior to processing.

