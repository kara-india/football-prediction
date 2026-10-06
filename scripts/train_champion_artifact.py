from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import os
import httpx

from python.calibration.calibrator import ProbabilityCalibrator
from python.data.historical_repository import HistoricalMatchRepository
from python.models.dynamic_dixon_coles import DynamicDCConfig, ScoreDrivenDixonColes

OUT = Path("python/models/champion_artifact.json")
MARKETS = [
    "MATCH_1X2:1", "MATCH_1X2:X", "MATCH_1X2:2",
    "TOTAL_GOALS_2_5:OVER", "TOTAL_GOALS_2_5:UNDER",
]

def main() -> None:
    df = HistoricalMatchRepository().fetch()
    if len(df) < 1000:
        raise RuntimeError(f"Need at least 1000 real historical matches; found {len(df)}.")
    df = df.sort_values("date", kind="mergesort").reset_index(drop=True)
    # Keep the most recent chronological window for operational retraining.
    # The dynamic model already down-weights older observations; this cap keeps
    # optimizer runtime bounded without introducing look-ahead.
    if len(df) > 2500:
        df = df.tail(2500).reset_index(drop=True)

    train_end = int(len(df) * 0.70)
    cal_end = int(len(df) * 0.85)
    train = df.iloc[:train_end].copy()
    calibration = df.iloc[train_end:cal_end].copy()
    test = df.iloc[cal_end:].copy()

    model = ScoreDrivenDixonColes(config=DynamicDCConfig(max_iter=20)).fit(train)
    raw = {k: [] for k in MARKETS}
    truth = {k: [] for k in MARKETS}

    for row in calibration.itertuples(index=False):
        h, d, a = model.predict_1x2(str(row.home_id), str(row.away_id))
        over, under = model.predict_over_under(str(row.home_id), str(row.away_id), 2.5)
        values = {
            "MATCH_1X2:1": h, "MATCH_1X2:X": d, "MATCH_1X2:2": a,
            "TOTAL_GOALS_2_5:OVER": over, "TOTAL_GOALS_2_5:UNDER": under,
        }
        outcomes = {
            "MATCH_1X2:1": int(row.home_goals > row.away_goals),
            "MATCH_1X2:X": int(row.home_goals == row.away_goals),
            "MATCH_1X2:2": int(row.home_goals < row.away_goals),
            "TOTAL_GOALS_2_5:OVER": int(row.home_goals + row.away_goals > 2),
            "TOTAL_GOALS_2_5:UNDER": int(row.home_goals + row.away_goals < 3),
        }
        for key in MARKETS:
            raw[key].append(values[key])
            truth[key].append(outcomes[key])

    calibrator = ProbabilityCalibrator(method="isotonic")
    for key in MARKETS:
        calibrator.fit(np.asarray(truth[key]), np.asarray(raw[key]), market=key)

    metrics = {}
    for key in MARKETS:
        predictions, outcomes = [], []
        for row in test.itertuples(index=False):
            h, d, a = model.predict_1x2(str(row.home_id), str(row.away_id))
            over, under = model.predict_over_under(str(row.home_id), str(row.away_id), 2.5)
            values = {
                "MATCH_1X2:1": h, "MATCH_1X2:X": d, "MATCH_1X2:2": a,
                "TOTAL_GOALS_2_5:OVER": over, "TOTAL_GOALS_2_5:UNDER": under,
            }
            outcome = {
                "MATCH_1X2:1": int(row.home_goals > row.away_goals),
                "MATCH_1X2:X": int(row.home_goals == row.away_goals),
                "MATCH_1X2:2": int(row.home_goals < row.away_goals),
                "TOTAL_GOALS_2_5:OVER": int(row.home_goals + row.away_goals > 2),
                "TOTAL_GOALS_2_5:UNDER": int(row.home_goals + row.away_goals < 3),
            }
            predictions.append(float(calibrator.calibrate(values[key], market=key)))
            outcomes.append(outcome[key])
        p = np.asarray(predictions)
        y = np.asarray(outcomes)
        metrics[key] = {
            "brier": float(np.mean((p - y) ** 2)),
            "log_loss": float(-np.mean(
                y * np.log(np.clip(p, 1e-6, 1 - 1e-6))
                + (1 - y) * np.log(np.clip(1 - p, 1e-6, 1 - 1e-6))
            )),
        }

    artifact = {
        "schema_version": 1,
        "champion_version": "champion-python-v3.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dynamic_dixon_coles": model.serialize(),
        "calibration": calibrator.serialize(),
        "live_hazard": {
            "status": "unavailable",
            "reason": "match_events_has_no_training_rows",
        },
        "validation": {
            "training_sample_size": len(train),
            "calibration_sample_size": len(calibration),
            "test_sample_size": len(test),
            "metrics": metrics,
            "training_start": str(train.date.min()),
            "training_end": str(train.date.max()),
            "calibration_start": str(calibration.date.min()),
            "calibration_end": str(calibration.date.max()),
            "test_start": str(test.date.min()),
            "test_end": str(test.date.max()),
        },
    }
    serialized = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    OUT.write_text(serialized, encoding="utf-8")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    if url and key:
        endpoint = f"{url.rstrip('/')}/rest/v1/champion_artifacts"
        headers = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json", "Prefer": "return=minimal"}
        row = {"version": artifact["champion_version"], "artifact": artifact, "validation": artifact["validation"], "is_active": True}
        response = httpx.post(endpoint, headers=headers, json=row, timeout=30.0)
        response.raise_for_status()
    print(json.dumps(artifact["validation"], indent=2))

if __name__ == "__main__":
    main()
