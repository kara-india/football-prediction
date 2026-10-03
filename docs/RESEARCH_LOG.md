# RESEARCH LOG & QUANTITATIVE METHODOLOGY NOTES
## Football Prediction Intelligence Platform

This document logs architectural investigations, empirical validations, and quantitative methodology decisions across the platform lifecycle.

---

## Entry 001: Multi-Checkpoint Forecasting & Lineup Information Value (LIV)
**Date**: September 24, 2026  
**Topic**: Quantifying the Value of Confirmed Starting Lineups in Association Football

### 1. Context & Motivation
Traditional sports prediction systems often conflate pre-match predictions into a single static probability generated 24–48 hours in advance, or silently overwrite predictions when team sheets arrive. In elite professional football, confirmed starting XIs announced at $T-60\text{m}$ introduce critical private information:
- Rest and rotation of key attacking players (e.g., star strikers rested for continental cup fixtures).
- Tactical formation shifts (e.g., transition from 4-3-3 to 5-4-1 low-block against dominant opposition).
- Backup goalkeeper deployments.

### 2. Formalization of Multi-Checkpoint Snapshots
To evaluate this information without lookahead bias, we formalize distinct immutable prediction checkpoints for fixture $k$:
- **Checkpoint A ($T_1 \approx T-48\text{h}$)**: $\hat{p}_A = \mathcal{M}(\mathcal{F}_{T_1})$. Based on expected rosters, historical form, and base Poisson intensities.
- **Checkpoint B ($T_2 \approx T-60\text{m}$)**: $\hat{p}_B = \mathcal{M}(\mathcal{F}_{T_2} \cup \mathcal{L}_{\text{confirmed}})$. Lineup-conditioned probability.
- **Checkpoint C ($T_3 \approx T-5\text{m}$)**: $\hat{p}_C = \mathcal{M}(\mathcal{F}_{T_3} \cup \mathcal{O}_{\text{closing}})$. Final pre-kickoff probability incorporating closing market prices.

### 3. Mathematical Metric: Lineup Information Value (LIV)
We define the empirical Information Value of confirmed lineups as the reduction in out-of-sample forecast error:

$$\text{LIV}_{\text{Brier}} = \frac{1}{M}\sum_{k=1}^M \left[ ( \hat{p}_{A,k} - y_k )^2 - ( \hat{p}_{B,k} - y_k )^2 \right]$$
$$\text{LIV}_{\text{LogLoss}} = \frac{1}{M}\sum_{k=1}^M \left[ \ell(\hat{p}_{A,k}, y_k) - \ell(\hat{p}_{B,k}, y_k) \right]$$

A positive $\text{LIV}$ indicates that confirmed lineups systematically enhance predictive accuracy. If $\text{LIV} \le 0$ in certain secondary leagues, the model detects that starting XI variance is uninformative or noisy, avoiding over-fitting.

---

## Entry 002: Error Taxonomy & Causal Decomposition
**Date**: September 24, 2026  
**Topic**: Rigorous Classification of Forecast Errors Post-Settlement

Post-match settlement must not treat every lost prediction as uniform Bernoulli failure. We establish a 11-category taxonomy:
1. `TEAM_STRENGTH_MISS`: Residual explained by sustained multi-match deviation in core Elo/Dixon-Coles parameters.
2. `LINEUP_MISASSESSMENT`: Residual caused by unpredicted squad rotation or tactical alteration.
3. `PLAYER_PROJECTION_ERROR`: Key player underperformance relative to individual historical distribution.
4. `TACTICAL_MISMATCH`: High-press vs low-block tactical incompatibility.
5. `LIVE_STATE_ERROR`: Early red card, penalty, or extreme in-play state transition.
6. `ODDS_STALENESS`: Divergence between model prediction time and market closing movement.
7. `SOURCE_CONFLICT`: Discrepancy in upstream provider feeds.
8. `DATA_MISSING`: Truncated match coverage or missing metrics.
9. `CALIBRATION_ERROR`: Deviation attributable to uncalibrated probability binning.
10. `PARAMETER_DRIFT`: Macro regime shift in competition goal scoring.
11. `RANDOM_VARIANCE`: Unavoidable stochastic variance inherent in Poisson/multinomial trials.

---

## Entry 003: Subordinated Reinforcement Learning & Offline Policy Evaluation
**Date**: September 24, 2026  
**Topic**: Contextual Bandits as Decision Layers Under Strict Statistical Subordination

### 1. Principle of Statistical Subordination
Reinforcement learning must never replace calibrated probability estimation. Instead, the contextual bandit operates strictly as an action-selection layer ($a \in \{\text{ABSTAIN}, \text{BET}_1, \dots, \text{BET}_K\}$).
If any data quality or statistical gate is tripped (`LINEUP_UNCONFIRMED`, `ODDS_STALE`, `MARGIN_EXCESSIVE`), the action space is restricted to $a = \text{ABSTAIN}$.

### 2. Offline Policy Evaluation (OPE)
To safely evaluate challenger policies without real financial risk:
- We log all decision opportunities with their propensity scores $\pi_0(a \mid x)$.
- We evaluate candidate policy $\pi_{\text{new}}$ using **Doubly Robust (DR)** estimation:

$$\hat{V}_{\text{DR}}(\pi_{\text{new}}) = \frac{1}{N}\sum_{i=1}^N \left[ \hat{Q}(x_i, \pi_{\text{new}}(x_i)) + \frac{\mathbb{I}(a_i = \pi_{\text{new}}(x_i))}{\pi_0(a_i \mid x_i)} \left( r_i - \hat{Q}(x_i, a_i) \right) \right]$$

This guarantees that policy improvements are rigorously validated out-of-sample before promotion to Champion.

---

## Entry 004: Real Historical Out-of-Sample Walk-Forward Benchmark (Premier League)
**Date**: October 3, 2026  
**Topic**: Empirical Verification of Dixon-Coles Bivariate Poisson Across 21 Expanding Temporal Folds

### 1. Experimental Protocol
- **Dataset**: 1,900 official Premier League fixtures across 5 full seasons (2019/20 to 2023/24) from `football-data.co.uk`.
- **Training Window**: 760 matches (~2 full seasons) expanding by 38 matches per fold.
- **Test Window**: 190 matches (~0.5 season) evaluated out-of-sample with zero lookahead.
- **Folds Completed**: 21 folds totaling 3,990 test predictions.
- **Model Specification**: Dixon-Coles (1997) bivariate Poisson with dynamic time decay ($\xi = 0.0019$, 365-day half-life), low-score dependency parameter $\rho$, and algebraic sum-to-one attack parameter identifiability constraint.

### 2. Empirical Verification vs. Naive Uniform Prior ($p = 1/3$)

| Metric | Dixon-Coles (Fitted) | Naive Benchmark ($1/3$) | Empirical Improvement |
| :--- | :--- | :--- | :--- |
| **Brier Score** (↓) | `0.595925` | `0.666667` | `+0.070742` |
| **Ranked Probability Score (RPS)** (↓) | `0.212551` | `0.241312` | `+0.028761` |
| **Multi-class Log Loss** (↓) | `0.999971` | `1.098612` | `+0.098641` |
| **Expected Calibration Error (ECE)** (↓) | `0.024471` | `0.138847` | `+0.114376` |
| **Top-1 Win Accuracy** (↑) | `52.08%` | `47.22%` | `+4.86 pp` |

### 3. Quantitative Takeaways
1. **Calibration Excellence**: Dixon-Coles achieves an out-of-sample Expected Calibration Error (ECE) of **2.45%**, representing a 11.4 percentage-point reduction in probability miscalibration relative to naive assignments.
2. **Strict Super-Random Edge**: The statistical model outperforms the naive baseline on all five formal scoring rules without manual parameter tuning or lookahead leakage.
3. **Reproducibility**: Artifact and fold metrics are fully reproducible via `scripts/run_historical_walkforward.py` and saved in `docs/MODEL_BENCHMARK_RESULTS.md`.
