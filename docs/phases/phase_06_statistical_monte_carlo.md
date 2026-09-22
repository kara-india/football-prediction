# PHASE 6 — CORE STATISTICAL MODELS & PATH-DEPENDENT MONTE CARLO

## 1. Goal
Completely overhaul the mathematical core of the prediction engine. Replace unstable Dixon-Coles heuristics with a rigorously identifiable bivariate Poisson model with estimated temporal decay $\xi$. Separate generic EWMA form into multi-dimensional performance metrics. Replace stubbed Monte Carlo loops with a vectorized competing-hazard simulator that models in-play state transitions (scoreline dynamics, red cards, time decay) with mathematically derived standard error convergence.

## 2. Criticality
**P1 — HIGH** (Provides the core probability engine powering all prediction calculations).

## 3. Prerequisites
- Phase 3 (Historical match dataset) completed.
- Pinned Python scientific libraries (`scipy`, `numpy`, `pandas`) verified.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 6.1 [Dixon-Coles Model Overhaul]**: Rewrite `python/models/dixon_coles.py`:
  - Enforce sum-to-one attack identifiability: $\frac{1}{N} \sum_{i=1}^N \alpha_i = 1$.
  - Implement time-decay weighting function $w(t_k) = e^{-\xi (T - t_k)}$, estimating $\xi$ via profile log-likelihood.
  - Model home attack $\alpha_i$, away defense $\beta_j$, home advantage $\gamma$, and low-score dependence $\rho$.
  - Optimize negative log-likelihood via L-BFGS-B with robust parameter bounds.
  - Serialize fitted parameters to JSON and persist in Supabase `model_versions`.
- **Task 6.2 [Multi-Dimensional Dynamic Form]**: Rewrite `python/models/form.py`:
  - Eliminate fixed $\alpha = 0.3$.
  - Compute distinct exponential moving averages (EWMA) for:
    - Attacking form (goals scored, shots on target)
    - Defensive form (goals conceded, shots on target allowed)
    - Set-piece & territorial form (corners won/conceded)
    - Disciplinary form (yellow/red cards, fouls)
  - Estimate half-life decay parameter via temporal validation.
- **Task 6.3 [Negative Binomial Count Models]**: Rewrite `python/models/count_models.py`:
  - Build specialized count distributions for secondary markets:
    - `GoalCountModel`: Poisson / Negative Binomial with overdispersion check.
    - `CardCountModel`: Negative Binomial conditioned on referee strictness, team aggression, and match intensity.
    - `CornerCountModel`: Negative Binomial conditioned on team wing play and shot volume.
- **Task 6.4 [Vectorized Path-Dependent Monte Carlo]**: Rewrite `python/simulation/vectorized_mc.py`:
  - Simulate in-play match progression minute-by-minute or event-by-event using competing hazards:
    $$\lambda_{\text{event}}(t) = \lambda_0(t) \cdot \exp\left(\sum \beta_k X_k(t)\right)$$
  - Dynamically adjust hazard intensities based on score state (trailing team increases attack hazard and defensive vulnerability) and red cards (immediate 35% reduction in goal intensity).
  - Vectorize across $N = 10,000$ to $50,000$ simulation paths.
  - Compute running standard error: $\text{SE} = \sqrt{\frac{\hat{p}(1-\hat{p})}{N}}$.
  - Halt simulation early when $\text{SE} \le 0.004$ (target 95% CI width $< \pm 0.8\%$).

### Sequential Tasks (Follows 6.1 - 6.4)
- **Task 6.5 [Convergence & Reproducibility Suite]**: Test simulation repeatability with fixed random seeds; verify that simulated goal distributions match theoretical Dixon-Coles marginals within 1%.
- **Task 6.6 [Model Serialization Smoke Test]**: Verify saving and reloading model checkpoints from Supabase `model_versions`.

## 5. Files / Modules Affected
- `python/models/dixon_coles.py`
- `python/models/elo.py`
- `python/models/form.py`
- `python/models/count_models.py`
- `python/simulation/monte_carlo.py`
- `python/simulation/vectorized_mc.py`
- `tests/test_statistical_models.py` [NEW]
- `tests/test_monte_carlo.py` [NEW]

## 6. Database Changes
- Add schema columns to `model_versions`: `parameters JSONB`, `metrics JSONB`, `git_sha TEXT`, `dataset_version TEXT`.

## 7. Tests Required
- `tests/test_statistical_models.py`:
  1. Test identifiability: verify mean attack parameter equals 1.0000.
  2. Verify time decay downweights matches from 3 years ago relative to last week.
  3. Test optimizer convergence on historical Premier League sample.
- `tests/test_monte_carlo.py`:
  1. Test that score-state conditioning shifts intensity when home team falls behind.
  2. Test red card event reduces team expected goals.
  3. Verify standard error decreases monotonically as $\frac{1}{\sqrt{N}}$ and matches theoretical formula.

## 8. Acceptance Criteria
- [ ] Dixon-Coles optimizer converges reliably without floating-point overflow or singular matrix warnings.
- [ ] Vectorized Monte Carlo simulates 10,000 paths in $< 250\text{ms}$ on CPU.
- [ ] Standard error is calculated strictly from empirical variance, never hardcoded.
- [ ] In-play hazard simulation accurately models state transitions for scorelines and cards.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Implement rewritten models and simulation engine.
  2. Execute `pytest tests/test_statistical_models.py tests/test_monte_carlo.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Trigger initial parameter fitting across 5 years of historical matches:
     ```powershell
     python -m python.models.dixon_coles --fit-all-leagues --save-baseline
     ```
  2. Check Supabase `model_versions` table to confirm active champion model row is registered.

## 11. Rollback Plan
- Revert active model version pointer in Supabase `engine_settings.active_model_version` to fallback baseline.

## 12. Risks
- Numerical instability during joint optimization of $\alpha, \beta, \gamma, \rho$. Handled by L-BFGS-B parameter bounding ($\alpha_i, \beta_i \in [0.1, 5.0]$, $\rho \in [-0.2, 0.2]$) and regularization.

## 13. What Must NOT Be Considered Complete
- Any Monte Carlo simulator returning fixed iterations without standard error estimation.
- Using hardcoded multiplier heuristics in place of data-calibrated state transitions.
