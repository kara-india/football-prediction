# Model Benchmark Results

> **Generated**: 2026-10-11 14:18 UTC
> **Data Source**: football-data.co.uk (vendored Premier League seasons, 2019/20–2025/26; 7 completed seasons)
> **Method**: Strict temporal walk-forward cross-validation (no future data leakage)

---

## Walk-Forward Configuration

| Parameter | Value |
|-----------|-------|
| Initial training window | 760 matches (~2 seasons; expands by fold) |
| Reserved calibration gap | 190 matches (~0.5 season; excluded from this raw benchmark) |
| Test window | 190 matches (~0.5 season) |
| Step size | 38 matches (1 match day) |
| Folds completed | 41 |
| Total predictions | 7790 |
| Date range | 2022-01-03 → 2026-05-24 |
| Xi (time decay) | 0.0019 (half-life ≈ 365 days) |

## Raw p ≥ 0.70 diagnostics by fold

These are uncalibrated Dixon-Coles top-outcome probabilities and are diagnostic only; they do not prove the live confidence gate. Picks use the highest-probability 1X2 outcome. Mean odds use the historical Bet365 opening price. CLV is `opening_decimal_odds / closing_decimal_odds - 1`; positive means the opening price beat the close. Closing prices are used only as historical labels. Test windows overlap, so the distinct-fixture row keeps only the latest eligible fold for each fixture; only that row avoids repeated fixture outcomes.

| Fold | Train matches | Test matches | p ≥ 0.70 picks | Hit rate | Mean opening odds | Mean CLV |
|------|--------------:|--------------:|---------------:|---------:|------------------:|---------:|
| 1 | 760 | 190 | 19 | 0.842 | 1.277 | -1.448% |
| 2 | 798 | 190 | 23 | 0.826 | 1.252 | -1.900% |
| 3 | 836 | 190 | 22 | 0.864 | 1.269 | -1.955% |
| 4 | 874 | 190 | 21 | 0.810 | 1.253 | -1.819% |
| 5 | 912 | 190 | 21 | 0.714 | 1.276 | -1.545% |
| 6 | 950 | 190 | 19 | 0.579 | 1.256 | -1.336% |
| 7 | 988 | 190 | 18 | 0.667 | 1.292 | -1.000% |
| 8 | 1026 | 190 | 20 | 0.700 | 1.388 | -1.216% |
| 9 | 1064 | 190 | 20 | 0.650 | 1.402 | -0.811% |
| 10 | 1102 | 190 | 24 | 0.792 | 1.403 | -0.758% |
| 11 | 1140 | 190 | 25 | 0.720 | 1.450 | -1.529% |
| 12 | 1178 | 190 | 30 | 0.767 | 1.439 | -1.339% |
| 13 | 1216 | 190 | 35 | 0.714 | 1.445 | -1.834% |
| 14 | 1254 | 190 | 29 | 0.793 | 1.340 | -1.364% |
| 15 | 1292 | 190 | 27 | 0.704 | 1.362 | -1.270% |
| 16 | 1330 | 190 | 21 | 0.810 | 1.308 | -1.325% |
| 17 | 1368 | 190 | 15 | 0.800 | 1.353 | -0.207% |
| 18 | 1406 | 190 | 19 | 0.895 | 1.316 | -0.796% |
| 19 | 1444 | 190 | 15 | 0.867 | 1.297 | -0.257% |
| 20 | 1482 | 190 | 16 | 0.938 | 1.310 | -0.428% |
| 21 | 1520 | 190 | 19 | 0.947 | 1.244 | 0.622% |
| 22 | 1558 | 190 | 30 | 0.900 | 1.364 | -0.214% |
| 23 | 1596 | 190 | 27 | 0.963 | 1.237 | 0.381% |
| 24 | 1634 | 190 | 29 | 0.828 | 1.343 | 0.231% |
| 25 | 1672 | 190 | 25 | 0.800 | 1.259 | 0.688% |
| 26 | 1710 | 190 | 16 | 0.625 | 1.308 | 0.551% |
| 27 | 1748 | 190 | 15 | 0.667 | 1.345 | 0.083% |
| 28 | 1786 | 190 | 12 | 0.583 | 1.281 | 0.254% |
| 29 | 1824 | 190 | 17 | 0.647 | 1.410 | -1.976% |
| 30 | 1862 | 190 | 21 | 0.667 | 1.464 | -1.500% |
| 31 | 1900 | 190 | 21 | 0.714 | 1.523 | 0.250% |
| 32 | 1938 | 190 | 28 | 0.750 | 1.452 | -0.318% |
| 33 | 1976 | 190 | 33 | 0.758 | 1.438 | 0.455% |
| 34 | 2014 | 190 | 25 | 0.840 | 1.400 | 1.621% |
| 35 | 2052 | 190 | 20 | 0.800 | 1.403 | 1.628% |
| 36 | 2090 | 190 | 19 | 0.842 | 1.344 | 0.224% |
| 37 | 2128 | 190 | 15 | 0.733 | 1.325 | 0.812% |
| 38 | 2166 | 190 | 10 | 0.700 | 1.346 | 1.317% |
| 39 | 2204 | 190 | 11 | 0.727 | 1.385 | 0.527% |
| 40 | 2242 | 190 | 11 | 0.818 | 1.360 | 0.174% |
| 41 | 2280 | 190 | 8 | 0.875 | 1.362 | -1.093% |

| All fold prediction rows (overlapping windows) | — | 7790 | 851 | 0.776 | 1.354 | -0.540% |
| **Distinct fixtures; last eligible fold** | — | **1710** | **184** | **0.777** | **1.330** | **-0.600%** |

---

## Outcome Frequencies (Actual)

| Home Win | Draw | Away Win |
|----------|------|----------|
| 0.447 (3484) | 0.235 (1830) | 0.318 (2476) |

---

## Benchmark Metrics

| Metric | Dixon-Coles | Naive (1/3) | Improvement |
|--------|-------------|-------------|-------------|
| Brier Score ↓ | `0.601763` | `0.666667` | `+0.064904` |
| RPS (3-way) ↓ | `0.211458` | `0.238625` | `+0.027167` |
| Log Loss ↓ | `1.006824` | `1.098612` | `+0.091788` |
| ECE ↓ | `0.024607` | `0.113907` | `+0.089300` |
| Accuracy ↑ | `0.5092` | `0.4472` | `+0.0620` |

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
