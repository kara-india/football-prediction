"""
Closing Line Value (CLV) Tracker
Tracks early prediction odds against closing kickoff odds to compute empirical edge.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np


class CLVTracker:
    def __init__(self):
        self.predictions = {}
        self.closings = {}

    def record_prediction_odds(
        self,
        prediction_id: str,
        odds_at_prediction: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.predictions[prediction_id] = {"odds": odds_at_prediction, "time": timestamp}

    def record_closing_odds(
        self,
        prediction_id: str,
        odds_at_kickoff: float,
    ) -> None:
        self.closings[prediction_id] = odds_at_kickoff

    def compute_clv(
        self,
        odds_at_prediction: float,
        closing_odds: float,
    ) -> float:
        """
        Compute Closing Line Value (CLV):
        CLV = (o_pred / o_close) - 1.0
        """
        if odds_at_prediction <= 1.0 or closing_odds <= 1.0:
            return 0.0
        return (odds_at_prediction / closing_odds) - 1.0

    def get_clv_summary(self, predictions: Optional[List[Dict[str, Any]]] = None) -> dict:
        """
        Compute empirical CLV statistics from recorded or passed prediction entries.
        """
        clv_list = []
        if predictions:
            for p in predictions:
                o_p = p.get("odds_at_prediction") or p.get("odds")
                o_c = p.get("closing_odds")
                if o_p is not None and o_c is not None and o_p > 1.0 and o_c > 1.0:
                    clv_list.append(self.compute_clv(float(o_p), float(o_c)))
        else:
            for pid, pred_info in self.predictions.items():
                if pid in self.closings:
                    o_p = pred_info["odds"]
                    o_c = self.closings[pid]
                    if o_p > 1.0 and o_c > 1.0:
                        clv_list.append(self.compute_clv(o_p, o_c))

        if not clv_list:
            return {"mean_clv": 0.0, "median_clv": 0.0, "sample_size": 0}

        arr = np.asarray(clv_list, dtype=float)
        return {
            "mean_clv": round(float(np.mean(arr)), 6),
            "median_clv": round(float(np.median(arr)), 6),
            "std_clv": round(float(np.std(arr)), 6),
            "sample_size": len(arr),
            "positive_clv_pct": round(float(np.mean(arr > 0)), 4),
        }
