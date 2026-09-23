"""
Historical Match Replayer & Bridge
Integrates with PointInTimeReplayer while maintaining backwards compatibility
for match timeline in-play simulation.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .point_in_time_replayer import PointInTimeReplayer


class HistoricalReplayer:
    """Historical timeline replayer for match simulation."""

    def __init__(self):
        self.pit_replayer = PointInTimeReplayer()

    def replay_match(
        self,
        match: dict,
        snapshot_minutes: list[int],
        feature_engineer: Any,
        prediction_models: dict,
        monte_carlo: Any,
        calibrator: Any,
        no_bet_gate: Any,
    ) -> list[dict]:
        results = []
        events = match.get("events", [])
        for minute in snapshot_minutes:
            state = self._reconstruct_state_at(match, events, minute)
            features = {}
            if hasattr(feature_engineer, "compute_live_features"):
                features = feature_engineer.compute_live_features(
                    match=match,
                    live_state={"minute": minute, "score_home": 0, "score_away": 0},
                    home_team_stats={},
                    away_team_stats={},
                )
            features["minute"] = minute

            if not self.validate_no_lookahead(features, minute, events):
                raise ValueError(f"Lookahead detected at minute {minute}")

            prediction = {"minute": minute, "prediction": {}, "state": state}
            results.append(prediction)

        return results

    def _reconstruct_state_at(self, match: dict, events: list[dict], minute: int) -> dict:
        valid_events = self.pit_replayer.filter_inplay_events(events, minute)
        return {"match": match, "events": valid_events, "minute": minute}

    def validate_no_lookahead(
        self, features: dict, snapshot_minute: int, match_events: list[dict]
    ) -> bool:
        for event in match_events:
            if event.get("minute", 0) > snapshot_minute:
                if event.get("used", False):
                    return False
        return True

    def generate_training_snapshots(
        self, historical_matches: list[dict], snapshot_interval: int = 5
    ) -> pd.DataFrame:
        rows = []
        for match in historical_matches:
            for minute in range(0, 95, snapshot_interval):
                rows.append({"match_id": match.get("id") or match.get("match_id"), "minute": minute})
        return pd.DataFrame(rows)
