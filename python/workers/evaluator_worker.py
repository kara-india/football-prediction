"""
Evaluator & Post-Match Settlement Worker
Monitors finished matches (status 'FT'), settles outcomes across all checkpoints,
calculates Closing Line Value (CLV), decomposes loss into the 11-category error taxonomy,
and persists records to prediction_results and prediction_errors under strict idempotency.
"""
import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Union, Tuple

from python.engine.settlement import SettlementEngine
from python.engine.error_evaluator import ErrorEvaluator
from python.data_contracts import CanonicalSettlement, CanonicalForecastError, ErrorCategory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("EvaluatorWorker")


class EvaluatorWorker:
    """Post-match settlement and error classification worker."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        settlement_engine: Optional[SettlementEngine] = None,
        error_evaluator: Optional[ErrorEvaluator] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://qqcxjjkgvqknesrtnwal.supabase.co")
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )
        self.settlement_engine = settlement_engine or SettlementEngine()
        self.error_evaluator = error_evaluator or ErrorEvaluator()
        
        # In-memory settlement ledger enforcing strict idempotency across multiple runs
        self._settled_prediction_ids: Set[Union[str, int]] = set()
        self._settled_results: List[CanonicalSettlement] = []
        self._error_records: List[CanonicalForecastError] = []

    def get_already_settled_prediction_ids(self) -> Set[Union[str, int]]:
        """Fetch previously settled prediction IDs from Supabase and local cache."""
        settled_ids = set(self._settled_prediction_ids)
        if not self.supabase_url or not self.supabase_key:
            return settled_ids

        try:
            url = f"{self.supabase_url}/rest/v1/prediction_results?select=prediction_id"
            req = urllib.request.Request(
                url,
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    for row in data:
                        pid = row.get("prediction_id")
                        if pid is not None:
                            settled_ids.add(pid)
        except Exception as e:
            logger.warning(f"Could not load settled predictions from Supabase: {e}")

        return settled_ids

    def _persist_settlements_to_supabase(
        self,
        settlements: List[CanonicalSettlement],
        errors: List[CanonicalForecastError],
    ) -> None:
        """Write settled records and classified errors to Supabase."""
        if not self.supabase_url or not self.supabase_key:
            return

        # 1. Insert into prediction_results
        try:
            url = f"{self.supabase_url}/rest/v1/prediction_results"
            rows = []
            for s in settlements:
                try:
                    pid_int = int(s.prediction_id) if str(s.prediction_id).isdigit() else None
                except (ValueError, TypeError):
                    pid_int = None

                rows.append({
                    "prediction_id": pid_int,
                    "settled_at": s.settled_at.isoformat(),
                    "outcome": (s.actual_outcome == "WON"),
                    "actual_result": s.actual_outcome,
                    "brier_contribution": s.brier_score_contribution,
                    "clv_odds": s.closing_odds,
                    "clv": s.clv,
                })

            if rows:
                payload = json.dumps(rows).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201):
                        logger.debug(f"Persisted {len(rows)} settlement results to Supabase.")
        except Exception as e:
            logger.warning(f"Could not persist prediction_results: {e}")

        # 2. Insert into prediction_errors
        try:
            url = f"{self.supabase_url}/rest/v1/prediction_errors"
            err_rows = []
            for err in errors:
                try:
                    pid_int = int(err.prediction_id) if str(err.prediction_id).isdigit() else None
                except (ValueError, TypeError):
                    pid_int = None

                err_rows.append({
                    "prediction_id": pid_int,
                    "error_category": err.primary_category.value if isinstance(err.primary_category, ErrorCategory) else str(err.primary_category),
                    "magnitude": err.brier_contribution,
                    "details": {
                        "log_loss_contribution": err.log_loss_contribution,
                        "calibration_residual": err.calibration_residual,
                        "scoreline_error": err.scoreline_error,
                        "evidence_notes": err.evidence_notes,
                    },
                })

            if err_rows:
                payload = json.dumps(err_rows).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201):
                        logger.debug(f"Persisted {len(err_rows)} error classifications to Supabase.")
        except Exception as e:
            logger.warning(f"Could not persist prediction_errors: {e}")

    def settle_predictions(
        self,
        predictions_with_matches: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> Tuple[List[CanonicalSettlement], List[CanonicalForecastError]]:
        """Settle a list of unsettled predictions against verified final match scores.
        
        Strictly idempotent: any prediction already settled is ignored.
        """
        already_settled = self.get_already_settled_prediction_ids()
        new_settlements: List[CanonicalSettlement] = []
        new_errors: List[CanonicalForecastError] = []

        for item in predictions_with_matches:
            pred_id = item.get("prediction_id", item.get("id"))
            if pred_id is None or pred_id in already_settled:
                logger.debug(f"Prediction {pred_id} already settled or invalid. Skipping (idempotency preserved).")
                continue

            match_id = str(item.get("match_id", "match_0"))
            market = item.get("market", "MATCH_1X2")
            selection = item.get("selection", "1")
            line = item.get("line")
            odds_pred = float(item.get("decimal_odds", item.get("odds_at_prediction", 2.0)))
            closing_odds = float(item.get("closing_odds", odds_pred))
            calibrated_p = float(item.get("calibrated_probability", 0.5))

            actual_h = int(item.get("score_home", item.get("actual_home_goals", 0)))
            actual_a = int(item.get("score_away", item.get("actual_away_goals", 0)))
            actual_cards = item.get("actual_cards")
            actual_corners = item.get("actual_corners")

            # 1. Settle via SettlementEngine
            settlement: CanonicalSettlement = self.settlement_engine.settle(
                prediction_id=str(pred_id),
                match_id=match_id,
                market=market,
                selection=selection,
                odds_at_prediction=odds_pred,
                actual_home_goals=actual_h,
                actual_away_goals=actual_a,
                actual_cards=actual_cards,
                actual_corners=actual_corners,
                line=line,
                closing_odds=closing_odds,
                calibrated_prob=calibrated_p,
            )

            # 2. Decompose error into 11-category taxonomy
            err_record: CanonicalForecastError = self.error_evaluator.classify_error(
                settlement=settlement,
                p_calibrated=calibrated_p,
                predicted_home_goals=1.45,
                predicted_away_goals=1.15,
                expected_value=(calibrated_p * odds_pred) - 1.0,
            )

            # Record settlement
            self._settled_prediction_ids.add(pred_id)
            self._settled_results.append(settlement)
            self._error_records.append(err_record)

            new_settlements.append(settlement)
            new_errors.append(err_record)

        if not dry_run and new_settlements:
            self._persist_settlements_to_supabase(new_settlements, new_errors)

        return new_settlements, new_errors

    def run(
        self,
        finished_matches_data: Optional[List[Dict[str, Any]]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute evaluator worker to settle FT matches and log error taxonomy."""
        logger.info(f"Starting EvaluatorWorker execution (dry_run={dry_run})...")

        items_to_settle = finished_matches_data or []

        # If no items provided and not dry_run, query Supabase for finished matches
        if not items_to_settle and not dry_run and self.supabase_url and self.supabase_key:
            try:
                # Query matches where status is 'FT' and their associated predictions
                url = f"{self.supabase_url}/rest/v1/matches?status=eq.FT&select=id,score_home,score_away,model_predictions(id,market,selection,line,decimal_odds,calibrated_probability)&limit=50"
                req = urllib.request.Request(
                    url,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                    },
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        matches = json.loads(resp.read().decode("utf-8"))
                        for m in matches:
                            h_score = m.get("score_home", 0)
                            a_score = m.get("score_away", 0)
                            m_id = m.get("id")
                            for p in m.get("model_predictions", []):
                                items_to_settle.append({
                                    "prediction_id": p.get("id"),
                                    "match_id": m_id,
                                    "market": p.get("market"),
                                    "selection": p.get("selection"),
                                    "line": p.get("line"),
                                    "decimal_odds": p.get("decimal_odds", 2.0),
                                    "calibrated_probability": p.get("calibrated_probability", 0.5),
                                    "score_home": h_score,
                                    "score_away": a_score,
                                })
            except Exception as e:
                logger.warning(f"Could not load finished matches from DB: {e}")

        # In dry run mode, synthesize 1 settled match test item if none provided
        if not items_to_settle and dry_run:
            items_to_settle = [
                {
                    "prediction_id": "dry_run_pred_1",
                    "match_id": "dry_run_match_ft",
                    "market": "MATCH_1X2",
                    "selection": "1",
                    "decimal_odds": 2.10,
                    "closing_odds": 2.05,
                    "calibrated_probability": 0.52,
                    "score_home": 2,
                    "score_away": 1,
                },
                {
                    "prediction_id": "dry_run_pred_2",
                    "match_id": "dry_run_match_ft",
                    "market": "TOTAL_GOALS_2_5",
                    "selection": "OVER",
                    "line": 2.5,
                    "decimal_odds": 1.95,
                    "closing_odds": 1.90,
                    "calibrated_probability": 0.58,
                    "score_home": 2,
                    "score_away": 1,
                },
            ]

        settled, errors = self.settle_predictions(items_to_settle, dry_run=dry_run)
        logger.info(f"EvaluatorWorker finished: settled {len(settled)} predictions with {len(errors)} error classifications.")

        return {
            "status": "success",
            "matches_evaluated": len(items_to_settle),
            "predictions_settled": len(settled),
            "errors_classified": len(errors),
            "errors": [],
        }


def run_evaluator_worker(dry_run: bool = False) -> Dict[str, Any]:
    """CLI / runner entrypoint for evaluator worker."""
    worker = EvaluatorWorker()
    return worker.run(dry_run=dry_run)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    res = run_evaluator_worker(dry_run=is_dry)
    logger.info(f"Evaluator worker completed: {res}")
    sys.exit(0)
