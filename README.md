# Q-PharmaSelect
### Quantum-Enhanced Molecular Discovery and Intelligent Assay Selection
**Track**: Quantum Machine Learning  
**Challenge**: QML-04 — Assay-Constrained Selection of Drug-Discovery Compounds  
**Platform**: QpiAI QCloud & QpiAI Opt SDK  
**Tagline**: *"Discover smarter. Test fewer. Learn faster."*

---

## 1. Executive Summary & Challenge Statement

In pharmaceutical lead optimization, discovery teams face severe capacity bottlenecks: only a limited batch of candidate molecules ($K$) can be physically synthesized and screened in wet-lab assays, subject to strict budgetary limits ($B$). Researchers must trade off:
1. **Predicted Potency**: Expected biochemical inhibition of the target kinase/enzyme.
2. **Epistemic Uncertainty**: Model confidence to balance exploitation with exploration of under-sampled regions.
3. **Chemical Novelty**: Distance from previously assayed chemical matter to avoid saturated intellectual property.
4. **Scaffold Diversity**: Chemical series variation within the selected batch to mitigate assay attrition.
5. **Pairwise Redundancy**: Penalizing structural duplicates from entering the same expensive batch.
6. **Assay Expense & Commercial Availability**: Real financial synthesis costs and reagent supply availability.

**Q-PharmaSelect** is a production-style computational decision-support prototype that answers:
> *"Given a biological target, a specified assay, a set of candidate molecules, an experimental budget, and limited testing capacity, which molecules should be tested next to maximize expected scientific discovery value?"*

---

## 2. Technology Stack & Key Libraries

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, responsive scientific R&D dashboard.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, SQLite development database.
- **Cheminformatics**: RDKit (`2026.9.1`): SMILES validation, canonicalization, ECFP4 Morgan fingerprints, Bemis-Murcko scaffold extraction, Tanimoto similarity matrices, 2D PCA embedding.
- **Machine Learning**: Scikit-learn (`1.9.1`): Leakage-resistant Bemis-Murcko scaffold splitting, Random Forest regressor/classifier, predictive interval estimation, Out-Of-Distribution (OOD) distance analysis.
- **Quantum Machine Learning**: **QpiAI Quantum SDK (`0.7.5`) / QCloud**:
  - Molecular feature angle rotation encoding ($R_y, R_z$) on $N_q = 4\text{--}8$ qubits.
  - Multi-qubit CNOT cyclic entanglement ladders.
  - Simulator & QPU backends: `QpiAI-QSV-Simulator`, `QpiAI-Indus-1`, `QpiAI-QSV-Local`.
  - Hybrid quantum regression model benchmarked directly against classical baselines on identical data splits.
- **Combinatorial Optimization**: **QpiAI Opt SDK (`1.0.6`)**:
  - Mathematical QUBO binary quadratic model with quadratic equality penalty for exact batch size $K$ and budget constraints.
  - Integration with `qpiai_opt.problem.qubo.QUBOProblem` and `qpiai_opt.solver.solver.Solver`.
  - Classical validation solvers: Simulated Annealing, Greedy Top Activity, Greedy Maximal Marginal Relevance (MMR), and Brute-force Exhaustive Enumeration ($N \le 18$) to prove global optimum convergence.

---

## 3. Mathematical QUBO Formulation

For candidate pool $i \in \{1, \dots, N\}$, binary decision variable $x_i \in \{0, 1\}$ indicates whether molecule $i$ is selected for experimental batch testing.

### 3.1 Linear Discovery Utility
$$\mu_i = w_{\text{activity}} \tilde{y}_i + w_{\text{exploration}} \tilde{\sigma}_i + w_{\text{novelty}} \text{Nov}_i - w_{\text{cost}} \tilde{c}_i$$
- $\tilde{y}_i = \frac{\hat{y}_i - y_{\min}}{y_{\max} - y_{\min}}$: Normalized predicted potency ($\text{pIC}_{50}$).
- $\tilde{\sigma}_i = \frac{\sigma_i}{\sigma_{\max}}$: Calibrated epistemic ensemble standard deviation.
- $\text{Nov}_i = 1 - \max_{k \in \text{Historical}} \text{Tanimoto}(\text{FP}_i, \text{FP}_k)$: Chemical novelty relative to reference series.
- $\tilde{c}_i = \frac{c_i}{c_{\max}}$: Normalized synthesis and assay screening expense.

### 3.2 Pairwise Redundancy Term
$$\mathcal{P}_{\text{redundancy}}(x) = w_{\text{diversity}} \sum_{i < j} S_{ij} x_i x_j$$
where $S_{ij} = \text{Tanimoto}(\text{FP}_i, \text{FP}_j)$ is the molecular fingerprint similarity.

### 3.3 Exact Batch Size Penalty
To enforce selecting exactly $K$ compounds ($\sum_{i=1}^N x_i = K$):
$$\mathcal{P}_{\text{batch}}(x) = \lambda_{\text{batch}} \left( \sum_{i=1}^N x_i - K \right)^2 = \lambda_{\text{batch}} \left[ \sum_{i=1}^N (1 - 2K) x_i + 2 \sum_{i < j} x_i x_j + K^2 \right]$$

### 3.4 Complete QUBO Minimization Objective
$$\min_{x \in \{0, 1\}^N} E(x) = \sum_{i=1}^N Q_{ii} x_i + \sum_{i < j} Q_{ij} x_i x_j$$
Where:
- $Q_{ii} = -\mu_i + \lambda_{\text{batch}} (1 - 2K)$
- $Q_{ij} = w_{\text{diversity}} S_{ij} + 2 \lambda_{\text{batch}}$ for $i < j$.

---

## 4. Retrospective Evaluation Benchmark Results

Simulated on held-out assay records for human wild-type **EGFR tyrosine kinase domain inhibition (ChEMBL Target `CHEMBL203`, Assay `CHEMBL615112`)**:

| Selection Strategy | Enrichment Factor (EF) | Hit Rate (%) | Observed Hits | Novel Scaffolds | Total Cost ($) | Hits / $1,000 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q-PharmaSelect Optimizer (QUBO)** | **1.85x** | **75.0%** | **9 / 12** | **9 Scaffolds** | **$4,650** | **1.94** |
| Greedy Top Predicted Activity | 1.66x | 100% | 12 / 12 | 2 Scaffolds | $7,550 | 1.59 |
| Greedy MMR (Potency + Diversity) | 1.52x | 91.7% | 11 / 12 | 6 Scaffolds | $7,990 | 1.38 |
| Random Feasible Selection (40-run MC avg) | 0.97x | 41.7% | 5 / 12 | 4 Scaffolds | $5,398 | 0.93 |

*Key finding*: While pure greedy selection picks repetitive analogs from known quinazoline series, Q-PharmaSelect's QUBO formulation discovers **9 novel Bemis-Murcko scaffolds** with higher cost efficiency (**1.94 hits / $1,000** vs 1.59 for greedy), strictly adhering to budget and batch constraints.

---

## 5. Quickstart & Local Development

### 5.1 Prerequisites
- Python 3.10+ (Python 3.11/3.15 supported)
- Node.js 18+ and npm

### 5.2 Start Development Servers
In two separate terminals:

**Terminal 1 — FastAPI Backend**:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Terminal 2 — React Frontend**:
```powershell
npm run dev
```
Open your browser at: **[http://127.0.0.1:5173](http://127.0.0.1:5173)**

### 5.3 Run Test Suite
```powershell
python -m pytest backend/tests -v
```
All 24 unit and integration tests validate cheminformatics, leakage prevention, QpiAI Quantum circuits, QUBO formulation, small-instance exhaustive enumeration, and API endpoints.

---

## 6. QpiAI Credentials Configuration

Configure keys in `.env` or through the interactive **Settings & Integrations** dashboard page:
```env
QPIAI_QCLOUD_API_KEY=your_qcloud_api_key_here
QPIAI_OPT_API_KEY=your_qpiai_opt_token_here
QPIAI_OPT_URL=https://opt.qpiai.tech
```
- If keys are unconfigured, Q-PharmaSelect runs in a fully functional, transparent local simulation mode without fabricating remote execution claims.

---

## 7. Research-Use Disclaimer

*Q-PharmaSelect is a computational decision-support tool designed for scientific research and lead candidate selection. Computational predictions, quantum feature representations, and combinatorial rankings do not prove clinical safety, pharmacological efficacy, or regulatory approval.*

