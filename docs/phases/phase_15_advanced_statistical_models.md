# PHASE 15 SPECIFICATION & BENCHMARK CONTRACT
# Advanced Statistical Modeling & Real Historical Walk-Forward Validation

## 1. Objectives & Mandates
1. Real Data Only: Evaluate models against real historical match records from football-data.co.uk (English Premier League across 5 seasons: 2019/20 to 2023/24).
2. Zero Lookahead: Strict temporal ordering across expanding training folds. No future match information may inform parameters $\xi$, $\rho$, $\alpha$, or $\beta$.
3. Model Registry Architecture: Formal Champion/Challenger model registry with objective statistical promotion gates based on out-of-sample Brier score and minimum sample size.
4. Baseline Comparison: Quantify predictive edge relative to the uninformative naive prior ($p=1/3$).

---

## 2. Statistical Architecture

### Dixon-Coles Bivariate Poisson (`python/models/dixon_coles.py`)
- **Intensity Equations**:
  $$\lambda_k = \alpha_i \beta_j \gamma$$
  $$\mu_k = \alpha_j \beta_i$$
- **Low-Score Dependence Correction ($\tau$)**:
  $$\tau(0,0) = 1 - \lambda \mu \rho$$
  $$\tau(1,0) = 1 + \mu \rho$$
  $$\tau(0,1) = 1 + \lambda \rho$$
  $$\tau(1,1) = 1 - \rho$$
  $$\tau(x,y) = 1 \quad \text{otherwise}$$
- **Dynamic Time Decay ($\xi$)**: Matches weighted by $w_k = \exp(-\xi \cdot \Delta t_k)$, where $\xi = 0.0019$ corresponds to an empirical half-life of 365 days.
- **Identifiability Constraint**: $\sum_{i=1}^M \alpha_i = M$.

### Model Registry & Promotion Gate (`python/models/model_registry.py`)
- Artifact persistence with SHA-256 weight integrity hashing.
- `evaluate_promotion(model_name, challenger, champion)`:
  - Requires $N \ge 100$ test matches.
  - Requires Brier score improvement $\ge 0.0020$ (0.2 percentage points).

---

## 3. Real Walk-Forward Benchmark Execution (`scripts/run_historical_walkforward.py`)
- Dataset: 1,900 Premier League matches (seasons 2019/20 through 2023/24).
- 21 expanding temporal folds evaluated.
- Output report persisted to `docs/MODEL_BENCHMARK_RESULTS.md`.
