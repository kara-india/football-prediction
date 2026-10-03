# Model Benchmark Results

> **Generated**: 2026-10-03 08:39 UTC  
> **Data Source**: football-data.co.uk (Premier League, 5 seasons: 2019/20–2023/24)  
> **Method**: Strict temporal walk-forward cross-validation (no future data leakage)

---

## Walk-Forward Configuration

| Parameter | Value |
|-----------|-------|
| Training window | 760 matches (~2 seasons) |
| Calibration window | 190 matches (~0.5 season) |
| Test window | 190 matches (~0.5 season) |
| Step size | 38 matches (1 match day) |
| Folds completed | 21 |
| Total predictions | 3990 |
| Date range | 2022-01-03 → 2024-05-19 |
| Xi (time decay) | 0.0019 (half-life ≈ 365 days) |

---

## Outcome Frequencies (Actual)

| Home Win | Draw | Away Win |
|----------|------|----------|
| 0.472 (1884) | 0.219 (873) | 0.309 (1233) |

---

## Benchmark Metrics

| Metric | Dixon-Coles | Naive (1/3) | Improvement |
|--------|-------------|-------------|-------------|
| Brier Score ↓ | `0.595925` | `0.666667` | `+0.070742` |
| RPS (3-way) ↓ | `0.212551` | `0.241312` | `+0.028761` |
| Log Loss ↓ | `0.999971` | `1.098612` | `+0.098641` |
| ECE ↓ | `0.024471` | `0.138847` | `+0.114376` |
| Accuracy ↑ | `0.5208` | `0.4722` | `+0.0486` |

> **Interpretation**: Positive improvement = Dixon-Coles better than naive baseline.  
> Brier Score and RPS are negatively oriented (lower = better).  
> Log Loss is negatively oriented (lower = better).

---

## Methodology Notes

- **Strict temporal ordering**: test matches are *never* in the training split.
- **Xi selection**: Fixed at 0.0019 (half-life ≈ 365 days). Not selected on test data.
- **Rho**: Fitted via MLE on training data only (Dixon-Coles low-score correction).
- **Identifiability**: Attack parameters sum-to-one constraint enforced algebraically.
- **New teams**: Teams unseen in training fallback to default alpha=1.0, beta=1.0.
- **RPS formula**: `(1/2) * mean_i( sum_{k=1}^2 (cumF_k - cumO_k)^2 )` for K=3 outcomes.

---

## Naive Baseline

The naive baseline assigns uniform probability `1/3` to each outcome (Home/Draw/Away).
This is the simplest possible baseline and the minimum bar for any model to clear.

---

*Results are fully reproducible by running `scripts/run_historical_walkforward.py`.*
