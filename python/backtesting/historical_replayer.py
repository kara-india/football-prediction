import pandas as pd
from typing import Dict, List, Any

class HistoricalReplayer:
    def replay_match(self, 
                     match: dict,
                     snapshot_minutes: list[int],
                     feature_engineer: Any,
                     prediction_models: dict,
                     monte_carlo: Any,
                     calibrator: Any,
                     no_bet_gate: Any) -> list[dict]:
        results = []
        for minute in snapshot_minutes:
            state = self._reconstruct_state_at(match, match.get('events', []), minute)
            features = {}
            if not self.validate_no_lookahead(features, minute, match.get('events', [])):
                raise ValueError("Lookahead detected")
            
            # Run prediction pipeline logic here
            prediction = {"minute": minute, "prediction": {}}
            results.append(prediction)
            
        return results

    def _reconstruct_state_at(self, match: dict, events: list[dict], minute: int) -> dict:
        valid_events = [e for e in events if e.get('minute', 0) <= minute]
        return {"match": match, "events": valid_events}

    def validate_no_lookahead(self, features: dict, snapshot_minute: int, 
                               match_events: list[dict]) -> bool:
        for event in match_events:
            if event.get('minute', 0) > snapshot_minute:
                if 'used' in event and event['used']:
                    return False
        return True

    def generate_training_snapshots(self, 
                                    historical_matches: list[dict],
                                    snapshot_interval: int = 5) -> pd.DataFrame:
        rows = []
        for match in historical_matches:
            for minute in range(0, 90, snapshot_interval):
                rows.append({"match_id": match.get("id"), "minute": minute})
        return pd.DataFrame(rows)
