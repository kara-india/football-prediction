#!/usr/bin/env python3
"""
Historical Walk-Forward Benchmark
Runs Dixon-Coles model on real Premier League data from football-data.co.uk
Produces authentic out-of-sample metrics. No synthetic data.
"""
import sys
import os
import glob
import hashlib
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.metrics import log_loss

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.models.dixon_coles import DixonColesModel

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / '.cache' / 'football_data'
OUTPUT_FILE = Path(__file__).parent.parent / 'docs' / 'MODEL_BENCHMARK_RESULTS.md'


def load_pl_data() -> pd.DataFrame:
    """Load all Premier League CSVs and parse dates."""
    pattern = str(CACHE_DIR / 'E0_*.csv')
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f'No E0 CSVs found in {CACHE_DIR}')

    dfs = []
    for fpath in files:
        # Read with BOM handling
        try:
            df = pd.read_csv(fpath, encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(fpath, encoding='latin-1')

        # Rename columns: strip BOM and whitespace
        df.columns = [c.strip().lstrip('\ufeff').lstrip('ï»¿') for c in df.columns]

        # Keep only required columns
        needed = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'Date']
        # Some files have 'Div' or other prefixes — find case-insensitively
        col_map = {c.lower(): c for c in df.columns}
        needed_found = []
        for n in needed:
            if n in df.columns:
                needed_found.append(n)
            elif n.lower() in col_map:
                df.rename(columns={col_map[n.lower()]: n}, inplace=True)
                needed_found.append(n)
            else:
                logger.warning(f'Column {n} not found in {fpath}, available: {list(df.columns[:10])}')

        df = df[needed].dropna(subset=['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'Date'])
        df['FTHG'] = pd.to_numeric(df['FTHG'], errors='coerce').astype('Int64')
        df['FTAG'] = pd.to_numeric(df['FTAG'], errors='coerce').astype('Int64')
        df = df.dropna(subset=['FTHG', 'FTAG'])

        # Parse date: DD/MM/YYYY
        df['date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['date'])

        logger.info(f'  Loaded {len(df)} matches from {Path(fpath).name}')
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values('date').reset_index(drop=True)
    logger.info(f'Total PL matches loaded: {len(combined)} from {combined["date"].min().date()} to {combined["date"].max().date()}')
    return combined


def build_team_mapping(df: pd.DataFrame) -> Dict[str, int]:
    """Build a stable team-name -> integer ID mapping (sorted alphabetically for reproducibility)."""
    all_teams = sorted(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique()))
    return {team: idx + 1 for idx, team in enumerate(all_teams)}


def outcome_to_vector(fthg: int, ftag: int) -> List[int]:
    """Convert goals to one-hot outcome vector [home_win, draw, away_win]."""
    if fthg > ftag:
        return [1, 0, 0]
    if fthg == ftag:
        return [0, 1, 0]
    return [0, 0, 1]


def brier_multiclass(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Multi-class Brier Score: mean over matches of sum-of-squared-errors across 3 outcomes."""
    return float(np.mean(np.sum((probs - outcomes) ** 2, axis=1)))


def rps_3way(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """
    Ranked Probability Score for 3-way outcomes (home win, draw, away win).
    RPS = (1/(K-1)) * mean over matches of sum_{k=1}^{K-1} (cumF_k - cumO_k)^2
    where K=3.
    """
    cum_probs = np.cumsum(probs, axis=1)[:, :-1]    # shape (N, 2)
    cum_outcomes = np.cumsum(outcomes, axis=1)[:, :-1]  # shape (N, 2)
    return float(np.mean(np.sum((cum_probs - cum_outcomes) ** 2, axis=1)) / (3 - 1))


def compute_ece(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
    """
    Expected Calibration Error (ECE) for the predicted winning outcome probability.
    Uses the max-probability class as the 'confidence' and checks if that outcome occurred.
    """
    confidence = np.max(probs, axis=1)
    predicted_class = np.argmax(probs, axis=1)
    actual_class = np.argmax(outcomes, axis=1)
    correct = (predicted_class == actual_class).astype(float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(confidence)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        in_bin = (confidence >= lo) & (confidence < hi)
        if in_bin.sum() == 0:
            continue
        bin_acc = correct[in_bin].mean()
        bin_conf = confidence[in_bin].mean()
        ece += (in_bin.sum() / n) * abs(bin_acc - bin_conf)
    return float(ece)


def accuracy_top1(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Was the highest-probability outcome the actual outcome?"""
    predicted = np.argmax(probs, axis=1)
    actual = np.argmax(outcomes, axis=1)
    return float(np.mean(predicted == actual))


def prepare_matches_for_model(df_subset: pd.DataFrame, team_map: Dict[str, int]) -> pd.DataFrame:
    """Convert raw match dataframe to the format expected by DixonColesModel."""
    out = pd.DataFrame({
        'home_id': df_subset['HomeTeam'].map(team_map),
        'away_id': df_subset['AwayTeam'].map(team_map),
        'home_goals': df_subset['FTHG'].astype(int),
        'away_goals': df_subset['FTAG'].astype(int),
        'date': df_subset['date'],
    })
    return out.dropna(subset=['home_id', 'away_id'])


def run_walkforward_benchmark():
    print('[WalkForward] Loading Premier League data...')
    df = load_pl_data()

    # Build stable team mapping from entire dataset
    team_map = build_team_mapping(df)
    print(f'[WalkForward] {len(team_map)} unique teams identified.')

    # -------------------------------------------------------------------------
    # Walk-forward fold definition
    # PL season = 380 matches (20 teams * 19 home games each)
    # But actual season sizes vary slightly; use match counts
    # Initial train: 2 seasons = 760 matches
    # Calibration: 0.5 season = 190 matches
    # Test: 0.5 season = 190 matches  (step = 38 matches = 1 match day)
    # -------------------------------------------------------------------------
    TRAIN_SIZE = 760     # ~2 seasons
    CALIB_SIZE = 190     # ~0.5 season
    TEST_SIZE = 190      # ~0.5 season
    STEP_SIZE = 38       # 1 match day

    n_matches = len(df)
    print(f'[WalkForward] Total matches: {n_matches}')

    # Minimum needed to start: TRAIN_SIZE + CALIB_SIZE + 1 test match
    min_start = TRAIN_SIZE + CALIB_SIZE

    all_predictions: List[Dict] = []
    fold_count = 0
    xi = 0.0019  # fixed xi per task spec (no future data for xi selection)

    # Compute walk-forward folds
    # test_start moves from min_start in steps of STEP_SIZE until no more test data
    test_start_indices = range(min_start, n_matches - TEST_SIZE + 1, STEP_SIZE)
    # Actually use a simpler approach: start when we have enough train+calib data
    # and test at the next window
    fold_indices = []
    pos = TRAIN_SIZE + CALIB_SIZE
    while pos + TEST_SIZE <= n_matches:
        train_end = pos - CALIB_SIZE
        calib_start = train_end
        calib_end = pos
        test_start = pos
        test_end = min(pos + TEST_SIZE, n_matches)
        fold_indices.append((0, train_end, calib_start, calib_end, test_start, test_end))
        pos += STEP_SIZE

    print(f'[WalkForward] Will run {len(fold_indices)} folds.')

    for fold_num, (_, train_end, calib_start, calib_end, test_start, test_end) in enumerate(fold_indices):
        train_df = df.iloc[:train_end]
        test_df = df.iloc[test_start:test_end]

        if len(train_df) < 100:
            logger.warning(f'Fold {fold_num}: insufficient training data ({len(train_df)} matches), skipping.')
            continue
        if len(test_df) == 0:
            break

        # Prepare training data
        train_matches = prepare_matches_for_model(train_df, team_map)

        # Fit Dixon-Coles on training window only (strict temporal ordering)
        model = DixonColesModel(xi=xi)
        try:
            model.fit(train_matches, xi=xi, max_iter=200)
        except Exception as e:
            logger.error(f'Fold {fold_num}: fit failed: {e}')
            continue

        if not model.fitted:
            logger.warning(f'Fold {fold_num}: model did not fit properly, skipping.')
            continue

        # Predict on test matches
        for _, row in test_df.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            h_id = team_map.get(home_team)
            a_id = team_map.get(away_team)

            if h_id is None or a_id is None:
                continue

            # Teams not in training set get default parameters (handled by DixonColesModel internally)
            try:
                p_home, p_draw, p_away = model.predict_1x2(h_id, a_id)
            except Exception as e:
                logger.warning(f'Prediction failed for {home_team} vs {away_team}: {e}')
                continue

            # Normalize to ensure they sum to 1
            total = p_home + p_draw + p_away
            if total <= 0 or not np.isfinite(total):
                continue
            p_home /= total
            p_draw /= total
            p_away /= total

            outcome_vec = outcome_to_vector(int(row['FTHG']), int(row['FTAG']))

            all_predictions.append({
                'fold': fold_num,
                'fixture_date': row['date'].date().isoformat(),
                'home_team': home_team,
                'away_team': away_team,
                'p_home': p_home,
                'p_draw': p_draw,
                'p_away': p_away,
                'outcome_home': outcome_vec[0],
                'outcome_draw': outcome_vec[1],
                'outcome_away': outcome_vec[2],
            })

        fold_count += 1
        if (fold_num + 1) % 5 == 0 or fold_num == 0:
            print(f'  [Fold {fold_num + 1}/{len(fold_indices)}] train={len(train_df)}, test={len(test_df)}, '
                  f'preds_so_far={len(all_predictions)}')

    print(f'\n[WalkForward] Completed {fold_count} folds. Total predictions: {len(all_predictions)}')

    if len(all_predictions) == 0:
        print('[WalkForward] ERROR: No predictions generated. Check data loading.')
        return

    # -------------------------------------------------------------------------
    # Compute aggregate metrics
    # -------------------------------------------------------------------------
    preds_df = pd.DataFrame(all_predictions)
    probs = preds_df[['p_home', 'p_draw', 'p_away']].to_numpy()
    outcomes = preds_df[['outcome_home', 'outcome_draw', 'outcome_away']].to_numpy().astype(float)

    # Naive benchmark: uniform 1/3 probabilities
    naive_probs = np.full_like(probs, 1.0 / 3.0)

    # --- Dixon-Coles metrics ---
    dc_brier = brier_multiclass(probs, outcomes)
    dc_rps = rps_3way(probs, outcomes)
    # Multi-class cross-entropy log loss on one-hot outcomes
    probs_clipped = np.clip(probs, 1e-7, 1 - 1e-7)
    dc_logloss = -float(np.mean(np.sum(outcomes * np.log(probs_clipped), axis=1)))
    dc_ece = compute_ece(probs, outcomes)
    dc_acc = accuracy_top1(probs, outcomes)

    # --- Naive benchmark metrics ---
    naive_probs_clipped = np.clip(naive_probs, 1e-7, 1 - 1e-7)
    naive_brier = brier_multiclass(naive_probs, outcomes)
    naive_rps = rps_3way(naive_probs, outcomes)
    naive_logloss = -float(np.mean(np.sum(outcomes * np.log(naive_probs_clipped), axis=1)))
    naive_ece = compute_ece(naive_probs, outcomes)
    naive_acc = accuracy_top1(naive_probs, outcomes)

    # Actual outcome frequencies
    n_preds = len(preds_df)
    n_home_wins = int(outcomes[:, 0].sum())
    n_draws = int(outcomes[:, 1].sum())
    n_away_wins = int(outcomes[:, 2].sum())
    freq_home = n_home_wins / n_preds
    freq_draw = n_draws / n_preds
    freq_away = n_away_wins / n_preds

    # -------------------------------------------------------------------------
    # Print results
    # -------------------------------------------------------------------------
    print('\n' + '=' * 70)
    print('PREMIER LEAGUE WALK-FORWARD BENCHMARK RESULTS')
    print('=' * 70)
    print(f'Matches evaluated:   {n_preds}')
    print(f'Folds completed:     {fold_count}')
    print(f'Date range:          {preds_df["fixture_date"].min()} to {preds_df["fixture_date"].max()}')
    print(f'Outcome frequencies: H={freq_home:.3f}  D={freq_draw:.3f}  A={freq_away:.3f}')
    print()
    print(f'{"Metric":<25} {"Dixon-Coles":>15} {"Naive (1/3)":>15} {"Improvement":>15}')
    print('-' * 70)
    print(f'{"Brier Score":<25} {dc_brier:>15.6f} {naive_brier:>15.6f} {naive_brier - dc_brier:>+15.6f}')
    print(f'{"RPS (3-way)":<25} {dc_rps:>15.6f} {naive_rps:>15.6f} {naive_rps - dc_rps:>+15.6f}')
    print(f'{"Log Loss":<25} {dc_logloss:>15.6f} {naive_logloss:>15.6f} {naive_logloss - dc_logloss:>+15.6f}')
    print(f'{"ECE":<25} {dc_ece:>15.6f} {naive_ece:>15.6f} {naive_ece - dc_ece:>+15.6f}')
    print(f'{"Accuracy (top-1)":<25} {dc_acc:>15.4f} {naive_acc:>15.4f} {dc_acc - naive_acc:>+15.4f}')
    print('=' * 70)

    # -------------------------------------------------------------------------
    # Save results to markdown
    # -------------------------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    md_content = f"""# Model Benchmark Results

> **Generated**: {run_ts}  
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
| Folds completed | {fold_count} |
| Total predictions | {n_preds} |
| Date range | {preds_df["fixture_date"].min()} → {preds_df["fixture_date"].max()} |
| Xi (time decay) | 0.0019 (half-life ≈ 365 days) |

---

## Outcome Frequencies (Actual)

| Home Win | Draw | Away Win |
|----------|------|----------|
| {freq_home:.3f} ({n_home_wins}) | {freq_draw:.3f} ({n_draws}) | {freq_away:.3f} ({n_away_wins}) |

---

## Benchmark Metrics

| Metric | Dixon-Coles | Naive (1/3) | Improvement |
|--------|-------------|-------------|-------------|
| Brier Score ↓ | `{dc_brier:.6f}` | `{naive_brier:.6f}` | `{naive_brier - dc_brier:+.6f}` |
| RPS (3-way) ↓ | `{dc_rps:.6f}` | `{naive_rps:.6f}` | `{naive_rps - dc_rps:+.6f}` |
| Log Loss ↓ | `{dc_logloss:.6f}` | `{naive_logloss:.6f}` | `{naive_logloss - dc_logloss:+.6f}` |
| ECE ↓ | `{dc_ece:.6f}` | `{naive_ece:.6f}` | `{naive_ece - dc_ece:+.6f}` |
| Accuracy ↑ | `{dc_acc:.4f}` | `{naive_acc:.4f}` | `{dc_acc - naive_acc:+.4f}` |

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
- **RPS formula**: `(1/2) * mean_i( sum_{{k=1}}^2 (cumF_k - cumO_k)^2 )` for K=3 outcomes.

---

## Naive Baseline

The naive baseline assigns uniform probability `1/3` to each outcome (Home/Draw/Away).
This is the simplest possible baseline and the minimum bar for any model to clear.

---

*Results are fully reproducible by running `scripts/run_historical_walkforward.py`.*
"""

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f'\n[WalkForward] Results saved to {OUTPUT_FILE}')

    # Return metrics for external use
    return {
        'n_predictions': n_preds,
        'n_folds': fold_count,
        'dc_brier': dc_brier,
        'dc_rps': dc_rps,
        'dc_logloss': dc_logloss,
        'dc_ece': dc_ece,
        'dc_acc': dc_acc,
        'naive_brier': naive_brier,
        'naive_rps': naive_rps,
        'naive_logloss': naive_logloss,
        'naive_ece': naive_ece,
        'naive_acc': naive_acc,
        'freq_home': freq_home,
        'freq_draw': freq_draw,
        'freq_away': freq_away,
    }


if __name__ == '__main__':
    run_walkforward_benchmark()
