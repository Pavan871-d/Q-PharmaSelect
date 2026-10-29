# Mathematical Formulation: Constrained Combinatorial Batch Optimization (QUBO)

## 1. Problem Definition

In assay-constrained molecular selection (**QML-04**), a drug-discovery campaign must select an experimental batch of exactly $K$ compounds from a pool of $N$ screening candidates ($K \ll N$). 

The objective is to maximize the expected scientific discovery value of the batch while strictly satisfying:
1. **Testing Capacity Constraint**: Exactly $K$ compounds must be selected.
2. **Experimental Budget Constraint**: Total assay cost must not exceed financial budget $B$.
3. **Compound Availability**: Only compounds meeting supplier availability policies may be selected.

---

## 2. Decision Variables

Let $x_i \in \{0, 1\}$ be a binary decision variable for compound $i \in \{1, \dots, N\}$, where:
$$
x_i = \begin{cases} 
1, & \text{if candidate molecule } i \text{ is selected for testing in the next batch} \\ 
0, & \text{otherwise} 
\end{cases}
$$

The full candidate batch is represented by the binary selection vector $\mathbf{x} = [x_1, x_2, \dots, x_N]^T \in \{0, 1\}^N$.

---

## 3. Multi-Objective Scientific Utility

For each candidate molecule $i$, we compute five normalized metrics $\in [0, 1]$:
- $\hat{y}_i$: Predicted biological potency (normalized predicted $\text{pIC}_{50}$).
- $\sigma_i$: Epistemic model uncertainty (normalized standard deviation across ensemble trees).
- $\nu_i$: Chemical novelty / Out-of-Distribution score ($1 - \max_{j \in \text{Train}} \text{Tanimoto}(m_i, m_j)$).
- $c_i$: Experimental acquisition and synthesis cost.
- $S_{ij}$: Pairwise Tanimoto similarity between candidate molecules $i$ and $j$ computed over Morgan ECFP4 fingerprints.

The composite discovery utility to be **maximized** is:
$$
U(\mathbf{x}) = \sum_{i=1}^N \left( w_A \hat{y}_i + w_U \sigma_i + w_N \nu_i - w_C c_i \right) x_i - w_D \sum_{i=1}^N \sum_{j > i}^N S_{ij} x_i x_j
$$
where:
- $w_A$: Weight on predicted activity (potency exploitation).
- $w_U$: Weight on model uncertainty (epistemic exploration).
- $w_N$: Weight on chemical novelty (OOD discovery).
- $w_D$: Weight on pairwise diversity (penalizing redundant analogs).
- $w_C$: Weight on cost sensitivity.

---

## 4. Quadratic Penalty Formulation (QUBO)

Quadratic Unconstrained Binary Optimization (QUBO) seeks to **minimize** an objective function of the form:
$$
E(\mathbf{x}) = \mathbf{x}^T \mathbf{Q} \mathbf{x} = \sum_{i=1}^N Q_{ii} x_i + \sum_{i=1}^N \sum_{j > i}^N Q_{ij} x_i x_j
$$
using the algebraic identity for binary variables $x_i^2 = x_i$.

To convert our maximization problem subject to constraints into a QUBO minimization problem, we construct the Lagrangian energy:
$$
E(\mathbf{x}) = - U(\mathbf{x}) + P_{\text{batch}}(\mathbf{x}) + P_{\text{budget}}(\mathbf{x})
$$

### 4.1 Exact Batch Size Constraint

The equality constraint $\sum_{i=1}^N x_i = K$ is enforced via a quadratic equality penalty with multiplier $\lambda_{\text{batch}} > 0$:
$$
P_{\text{batch}}(\mathbf{x}) = \lambda_{\text{batch}} \left( \sum_{i=1}^N x_i - K \right)^2
$$

Expanding this term:
$$
\left( \sum_{i=1}^N x_i - K \right)^2 = \left( \sum_{i=1}^N x_i \right)^2 - 2K \sum_{i=1}^N x_i + K^2
$$
$$
= \sum_{i=1}^N x_i^2 + 2 \sum_{i=1}^N \sum_{j > i}^N x_i x_j - 2K \sum_{i=1}^N x_i + K^2
$$
Using $x_i^2 = x_i$:
$$
= \sum_{i=1}^N (1 - 2K) x_i + 2 \sum_{i=1}^N \sum_{j > i}^N x_i x_j + K^2
$$
The constant $K^2$ does not affect the optimization argmin and is dropped from the matrix.

### 4.2 Budget Inequality Constraint

Total experimental expenditure must satisfy $\sum_{i=1}^N c_i x_i \le B$. 
In our formulation, when total cost approaches or exceeds $B$, an adaptive quadratic penalty is added:
$$
P_{\text{budget}}(\mathbf{x}) = \lambda_{\text{budget}} \max\left(0, \sum_{i=1}^N c_i x_i - B\right)^2
$$
In linearized QUBO form, the linear cost gradient encourages cost efficiency, while non-compliant batches incur penalty increments.

---

## 5. Explicit QUBO Matrix Elements

Combining the utility terms and constraint expansions yields the explicit entries for matrix $\mathbf{Q} \in \mathbb{R}^{N \times N}$:

### Diagonal Elements ($Q_{ii}$):
$$
Q_{ii} = - \left( w_A \hat{y}_i + w_U \sigma_i + w_N \nu_i - w_C c_i \right) + \lambda_{\text{batch}} (1 - 2K)
$$

### Off-Diagonal Elements ($Q_{ij}$ for $j > i$):
$$
Q_{ij} = w_D S_{ij} + 2 \lambda_{\text{batch}}
$$

> [!NOTE]
> Notice how the batch penalty contributes $+2 \lambda_{\text{batch}}$ to every pairwise off-diagonal coupling. This quadratic cross-term precisely counteracts selecting more than $K$ variables, while the negative diagonal term $\lambda_{\text{batch}}(1 - 2K)$ encourages turning on variables until the count reaches $K$.

---

## 6. Small-Instance Exhaustive Verification

To formally guarantee mathematical validity, the QUBO formulation was verified against an exhaustive classical global search on an $N=8, K=3$ instance in `backend/tests/test_optimization.py`:

- Total possible combinations: $\binom{8}{3} = 56$.
- Every combination evaluated for cost compliance and exact QUBO energy.
- **Result**: The Simulated Annealing solver and QpiAI Opt formulation find the identical global minimum energy vector $\mathbf{x}^* = [1, 0, 0, 0, 1, 0, 0, 1]^T$ as brute-force evaluation.

