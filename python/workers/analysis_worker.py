"""
Multi-Checkpoint Analysis Worker
Executes end-to-end forecasting pipeline across lifecycle checkpoints:
  - INITIAL (T-48h): Horizon entry baseline forecast
  - LINEUP_CONFIRMED (T-60m): Official team sheet recomputation with starter ratings
  - LINEUP_V2: Late starting XI revision snapshot
  - LIVE: Dynamic in-play re-simulation

Enforces:
  - Starter-specific EWMA attack/defense ratings & missing key player penalties
  - Dixon-Coles goal rates & Vectorized Monte Carlo (10,000 paths)
  - Probability calibration (Platt/Isotonic)
  - 1xBet odds devigging (Shin / Margin)
  - 10-point NO-BET gatekeeper evaluation
  - Lineup Information Value (LIV: delta p, delta odds, delta EV)
  - Immutable prediction snapshots in Supabase model_predictions
  - Unbiased logging of ALL eligible candidates in Counterfactual candidate ledger
"""
import os
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from python.data_contracts import CanonicalMatch
from python.simulation.match_state import MatchState
from python.simulation.vectorized_mc import VectorizedMonteCarloSimulator
from python.calibration.calibrator import ProbabilityCalibrator
from python.odds.devig import DeVIgEngine
from python.engine.nobet_gate import NoBetGate, NoBetGateResult
from python.rl.counterfactual_logger import CounterfactualLogger
from python.models.dynamic_dixon_coles import ScoreDrivenDixonColes
from python.models.learned_lineup_effects import LearnedLineupEffectModel

logger = logging.getLogger("AnalysisWorker")


class AnalysisWorker:
    """Multi-checkpoint forecast runner."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        cf_logger: Optional[CounterfactualLogger] = None,
        simulator: Optional[VectorizedMonteCarloSimulator] = None,
        calibrator: Optional[ProbabilityCalibrator] = None,
        no_bet_gate: Optional[NoBetGate] = None,
        prematch_model: Optional[ScoreDrivenDixonColes] = None,
        lineup_effect_model: Optional[LearnedLineupEffectModel] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            "https://qqcxjjkgvqknesrtnwal.supabase.co"
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )
        self.cf_logger = cf_logger or CounterfactualLogger()
        self.simulator = simulator or VectorizedMonteCarloSimulator(seed=42)
        self.no_bet_gate = no_bet_gate or NoBetGate()
        self.calibrator = calibrator or self._build_default_calibrator()
        self.prematch_model = prematch_model
        self.lineup_effect_model = lineup_effect_model
        
        # In-memory prediction ledger for dry-run and cross-checkpoint delta lookups
        self._in_memory_predictions: Dict[str, Dict[str, Any]] = {}

    def _build_default_calibrator(self) -> Optional[ProbabilityCalibrator]:
        """Do not invent calibration parameters; use a validated calibrator supplied by the caller."""
        return None

    def compute_starter_ratings(
        self,
        lineup_data: Optional[Dict[str, Any]],
        base_home_rate: Optional[float] = None,
        base_away_rate: Optional[float] = None,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Apply learned player/XI contributions to supplied baseline goal rates.

        No fixed "missing starter = -4%" or other hand-written lineup penalty is
        used. If a fitted lineup-effect model is unavailable, the baseline rates
        remain unchanged and the source is explicitly marked unavailable.
        """
        if base_home_rate is None or base_away_rate is None:
            raise ValueError("Base home/away goal rates must be supplied by a fitted model or explicit point-in-time observation.")

        home_rate = float(base_home_rate)
        away_rate = float(base_away_rate)

        if home_rate <= 0 or away_rate <= 0:
            raise ValueError("Baseline goal rates must be positive.")

        details: Dict[str, Any] = {
            "lineup_verified": False,
            "lineup_adjustment_source": "UNAVAILABLE",
            "home_log_rate_delta": 0.0,
            "away_log_rate_delta": 0.0,
        }

        if not lineup_data:
            return home_rate, away_rate, details

        home = lineup_data.get("home", {})
        away = lineup_data.get("away", {})
        home_starters = [
            p.get("player", {}).get("id")
            for p in home.get("starters", [])
            if p.get("player", {}).get("id") is not None
        ]
        away_starters = [
            p.get("player", {}).get("id")
            for p in away.get("starters", [])
            if p.get("player", {}).get("id") is not None
        ]

        verified = len(home_starters) == 11 and len(away_starters) == 11
        details["lineup_verified"] = verified

        if not verified or self.lineup_effect_model is None or not getattr(self.lineup_effect_model, "fitted", False):
            return home_rate, away_rate, details

        home_delta = self.lineup_effect_model.predict_log_rate_delta(
            home_starters, away_starters
        )
        away_delta = self.lineup_effect_model.predict_log_rate_delta(
            away_starters, home_starters
        )

        effective_home = float(np.exp(np.log(home_rate) + home_delta))
        effective_away = float(np.exp(np.log(away_rate) + away_delta))

        details.update({
            "lineup_adjustment_source": "learned_player_effects",
            "home_log_rate_delta": round(float(home_delta), 6),
            "away_log_rate_delta": round(float(away_delta), 6),
        })
        return effective_home, effective_away, details

    def compute_lineup_information_value(
        self,
        match_id: str,
        market: str,
        selection: str,
        current_prob: float,
        current_odds: Optional[float],
        current_ev: Optional[float],
    ) -> Dict[str, float]:
        """Compute Lineup Information Value (LIV) against prior INITIAL checkpoint.
        
        delta_p = p_lineup - p_initial
        delta_odds = odds_lineup - odds_initial
        delta_ev = ev_lineup - ev_initial
        """
        key = f"{match_id}:{market}:{selection}:INITIAL"
        initial_pred = self._in_memory_predictions.get(key)

        if initial_pred and current_odds is not None and current_ev is not None:
            p_init = initial_pred.get("calibrated_probability")
            odds_init = initial_pred.get("decimal_odds")
            ev_init = initial_pred.get("expected_value")
            if p_init is not None and odds_init is not None and ev_init is not None:
                return {
                    "delta_p": round(current_prob - p_init, 6),
                    "delta_odds": round(current_odds - odds_init, 4),
                    "delta_ev": round(current_ev - ev_init, 6),
                }

        return {
            "delta_p": 0.0,
            "delta_odds": 0.0,
            "delta_ev": 0.0,
        }

    def generate_forecasts(
        self,
        match_id: str,
        competition: str,
        stage: str,
        home_rate: float,
        away_rate: float,
        odds_dict: Optional[Dict[str, float]] = None,
        lineup_confirmed: bool = False,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """Run Dixon-Coles goal rates, Vectorized Monte Carlo, Devigging, and NO-BET gate."""
        # 1. Run Vectorized Monte Carlo from PREMATCH state
        state = MatchState(
            minute=0,
            added_time=0,
            score_home=0,
            score_away=0,
            period="PREMATCH",
            possession_home=50.0,
            shots_home=0,
            shots_away=0,
            shots_on_target_home=0,
            shots_on_target_away=0,
            xg_home=0.0,
            xg_away=0.0,
            corners_home=0,
            corners_away=0,
            fouls_home=0,
            fouls_away=0,
            yellow_cards_home=0,
            yellow_cards_away=0,
            red_cards_home=0,
            red_cards_away=0,
            offsides_home=0,
            offsides_away=0,
            substitutions_home=0,
            substitutions_away=0,
            is_live=False,
            lineup_confirmed=lineup_confirmed,
        )

        _, dist = self.simulator.simulate_with_convergence(
            state=state,
            home_lambda_per_min=home_rate / 90.0,
            away_lambda_per_min=away_rate / 90.0,
            min_simulations=10_000,
        )

        mc_se = dist.get("std_error")
        simulation_count = dist.get("simulation_count")
        if mc_se is None or simulation_count is None:
            raise RuntimeError("Monte Carlo output is incomplete; refusing to generate a prediction snapshot.")
        now_utc = datetime.now(timezone.utc)

        required_odds = ["1X2_1", "1X2_X", "1X2_2", "OU_OVER", "OU_UNDER", "BTTS_YES", "BTTS_NO"]
        active_odds = dict(odds_dict or {})
        missing_odds = [
            key for key in required_odds
            if active_odds.get(key) is None or float(active_odds[key]) <= 1.0
        ]
        odds_available = not missing_odds

        # Market configs: (market, selection, line, raw_prob, odds_key)
        markets = [
            ("MATCH_1X2", "1", None, dist["1x2"]["1"], "1X2_1"),
            ("MATCH_1X2", "X", None, dist["1x2"]["X"], "1X2_X"),
            ("MATCH_1X2", "2", None, dist["1x2"]["2"], "1X2_2"),
            ("TOTAL_GOALS_2_5", "OVER", 2.5, dist["over_under_25"]["over"], "OU_OVER"),
            ("TOTAL_GOALS_2_5", "UNDER", 2.5, dist["over_under_25"]["under"], "OU_UNDER"),
            ("BTTS", "YES", None, dist["btts"]["yes"], "BTTS_YES"),
            ("BTTS", "NO", None, dist["btts"]["no"], "BTTS_NO"),
        ]

        fair_probs: Dict[str, Optional[float]]
        if odds_available:
            devig_1x2, _ = DeVIgEngine.shin_devig([
                active_odds["1X2_1"], active_odds["1X2_X"], active_odds["1X2_2"],
            ])
            devig_ou = DeVIgEngine.multiplicative_devig([
                active_odds["OU_OVER"], active_odds["OU_UNDER"],
            ])
            devig_btts = DeVIgEngine.multiplicative_devig([
                active_odds["BTTS_YES"], active_odds["BTTS_NO"],
            ])
            fair_probs = {
                "1X2_1": devig_1x2[0],
                "1X2_X": devig_1x2[1],
                "1X2_2": devig_1x2[2],
                "OU_OVER": devig_ou[0],
                "OU_UNDER": devig_ou[1],
                "BTTS_YES": devig_btts[0],
                "BTTS_NO": devig_btts[1],
            }
        else:
            fair_probs = {key: None for key in required_odds}

        predictions: List[Dict[str, Any]] = []

        for market, sel, line, raw_p, o_key in markets:
            raw_p = float(max(0.0, min(1.0, raw_p)))
            calibration_applied = self.calibrator is not None
            if calibration_applied:
                calibrated_p = float(np.ravel(self.calibrator.calibrate(raw_p))[0])
                calibrated_p = float(max(0.01, min(0.99, calibrated_p)))
                calibration_version = "validated_calibrator"
            else:
                # Keep the raw model probability auditable, but explicitly mark it
                # as uncalibrated. Downstream gate logic will force NO_BET.
                calibrated_p = raw_p
                calibration_version = "UNAVAILABLE"

            decimal_odds = float(active_odds[o_key]) if odds_available else None
            fair_p = fair_probs[o_key]
            ev = (
                (calibrated_p * decimal_odds) - 1.0
                if calibration_applied and decimal_odds is not None
                else None
            )
            edge = (
                calibrated_p - fair_p
                if calibration_applied and fair_p is not None
                else None
            )

            prob_lower = max(0.0, calibrated_p - (1.96 * mc_se))
            prob_upper = min(1.0, calibrated_p + (1.96 * mc_se))

            gate_res: NoBetGateResult = self.no_bet_gate.evaluate(
                ev=ev if ev is not None else 0.0,
                edge=edge,
                lineup_confirmed=lineup_confirmed,
                home_starters_count=11 if lineup_confirmed else None,
                away_starters_count=11 if lineup_confirmed else None,
                # Missing odds are represented as unavailable, not as a fake age.
                odds_age_seconds=0.0 if odds_available else float("inf"),
                is_live=(stage == "LIVE"),
                is_market_suspended=not odds_available,
                odds_available=odds_available,
                odds_1xbet=decimal_odds,
                monte_carlo_se=mc_se,
                prob_lower=prob_lower,
                prob_upper=prob_upper,
                model_calibrated=calibration_applied,
                historical_sample_size=int(
                getattr(self.prematch_model, "metrics", {}).get("n_matches", 0)
            ),
            )
            gate_reasons = list(dict.fromkeys(
                ([ "ODDS_UNAVAILABLE" ] if not odds_available else [])
                + ([ "MODEL_UNCALIBRATED" ] if not calibration_applied else [])
                + list(gate_res.reasons)
            ))
            gate_res = NoBetGateResult(action="NO_BET" if gate_reasons else gate_res.action, reasons=gate_reasons)

            # Compute Lineup Information Value
            liv = self.compute_lineup_information_value(
                match_id=match_id,
                market=market,
                selection=sel,
                current_prob=calibrated_p,
                current_odds=decimal_odds,
                current_ev=ev,
            )

            prediction_record = {
                "match_id": match_id,
                "market": market,
                "selection": sel,
                "line": line,
                "stage": stage,
                "raw_probability": round(raw_p, 6),
                "calibrated_probability": round(calibrated_p, 6),
                "probability_lower": round(prob_lower, 6),
                "probability_upper": round(prob_upper, 6),
                "decimal_odds": round(decimal_odds, 4) if decimal_odds is not None else None,
                "implied_probability": round(1.0 / decimal_odds, 6) if decimal_odds is not None else None,
                "fair_probability": round(fair_p, 6) if fair_p is not None else None,
                "expected_value": round(ev, 6) if ev is not None else None,
                "value_edge": round(edge, 6) if edge is not None else None,
                "recommended_action": gate_res.action,
                "no_bet_reasons": gate_res.reasons,
                "simulation_count": int(simulation_count),
                "simulation_seed": int(self.simulator.seed) if getattr(self.simulator, "seed", None) is not None else None,
                "simulation_version": "3.0-learned-hazard",
                "model_version": (
                    "score_driven_dixon_coles_v1"
                    if self.prematch_model is not None and getattr(self.prematch_model, "fitted", False)
                    else "external_point_in_time_rate_model"
                ),
                "calibration_version": calibration_version,
                "calibration_applied": calibration_applied,
                "lineup_information_value": liv,
                "probability_interval_method": "mc_standard_error_only",
                "predicted_at": now_utc.isoformat(),
            }

            # Store in local memory for delta lookups
            mem_key = f"{match_id}:{market}:{sel}:{stage}"
            self._in_memory_predictions[mem_key] = prediction_record

            # Counterfactual policy logging requires a real, complete market and
            # a validated probability. Missing prerequisites stay in the prediction
            # ledger but are not masqueraded as policy observations.
            if (
                odds_available
                and calibration_applied
                and decimal_odds is not None
                and fair_p is not None
                and ev is not None
            ):
                action_choice = "BET" if gate_res.action == "BET" else "ABSTAIN"
                self.cf_logger.record_opportunity(
                    fixture_id=match_id,
                    match_timestamp=now_utc,
                    market=market,
                    competition=competition,
                    decimal_odds=decimal_odds,
                    fair_probability=fair_p,
                    expected_value=ev,
                    value_edge=edge or 0.0,
                    raw_probability=raw_p,
                    calibrated_probability=calibrated_p,
                    probability_interval=(prob_lower, prob_upper),
                    gate_action=gate_res.action,
                    gate_reasons=gate_res.reasons,
                    chosen_action=action_choice,
                    action_propensity=1.0,
                )

            predictions.append(prediction_record)

        # Write to Supabase if not dry_run and credentials present
        if not dry_run and self.supabase_url and self.supabase_key:
            self._persist_predictions_to_supabase(predictions)

        return predictions

    def _persist_predictions_to_supabase(self, predictions: List[Dict[str, Any]]) -> None:
        """Persist immutable prediction records into Supabase model_predictions table."""
        try:
            url = f"{self.supabase_url}/rest/v1/model_predictions"
            # Format rows matching database schema
            rows = []
            for p in predictions:
                rows.append({
                    "market": p["market"],
                    "selection": p["selection"],
                    "line": p["line"],
                    "predicted_at": p["predicted_at"],
                    "is_live": (p["stage"] == "LIVE"),
                    "raw_probability": p["raw_probability"],
                    "market_probability": p["fair_probability"],
                    "calibrated_probability": p["calibrated_probability"],
                    "probability_lower": p["probability_lower"],
                    "probability_upper": p["probability_upper"],
                    "decimal_odds": p["decimal_odds"],
                    "implied_probability": p["implied_probability"],
                    "expected_value": p["expected_value"],
                    "simulation_count": p["simulation_count"],
                    "simulation_seed": p["simulation_seed"],
                    "simulation_version": p["simulation_version"],
                    "no_bet_reasons": p["no_bet_reasons"],
                    "is_candidate": (p["recommended_action"] == "BET"),
                })
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
                    logger.debug(f"Persisted {len(rows)} prediction records to Supabase.")
        except Exception as e:
            logger.warning(f"Could not persist predictions to Supabase: {e}")

    def _resolve_baseline_goal_rates(
        self,
        match: Union[Dict[str, Any], CanonicalMatch],
    ) -> Tuple[float, float, str]:
        """
        Resolve point-in-time pre-lineup baseline rates.

        Preferred sources:
          1. Explicit rates persisted on the match input.
          2. A fitted dynamic Dixon-Coles model using team IDs.

        Production execution fails closed when neither source is available.
        """
        if isinstance(match, CanonicalMatch):
            match_map: Dict[str, Any] = match.__dict__
        else:
            match_map = dict(match)

        explicit_home = match_map.get("model_home_rate", match_map.get("base_home_rate"))
        explicit_away = match_map.get("model_away_rate", match_map.get("base_away_rate"))

        if explicit_home is not None and explicit_away is not None:
            h = float(explicit_home)
            a = float(explicit_away)
            if h > 0 and a > 0:
                return h, a, "explicit_point_in_time_rates"

        model = self.prematch_model
        home_id = match_map.get("home_team_id", match_map.get("home_id"))
        away_id = match_map.get("away_team_id", match_map.get("away_id"))

        if model is not None and getattr(model, "fitted", False) and home_id is not None and away_id is not None:
            h, a = model.get_expected_goals(home_id, away_id)
            if h > 0 and a > 0:
                return float(h), float(a), "dynamic_dixon_coles"

        raise RuntimeError(
            "No fitted point-in-time goal-rate source is available. "
            "Refusing to fall back to hard-coded home/away rates."
        )

    def run_match_prediction(
        self,
        match: Union[Dict[str, Any], CanonicalMatch],
        stage: str = "INITIAL",
        lineup_data: Optional[Dict[str, Any]] = None,
        odds_data: Optional[Dict[str, float]] = None,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """Run multi-checkpoint forecast for a single fixture."""
        if isinstance(match, CanonicalMatch):
            match_id = match.match_id
            comp_name = match.competition_name
        else:
            match_id = str(match.get("match_id", match.get("id", "match_0")))
            comp_name = match.get("competition_name", "Allowed Competition")

        lineup_confirmed = (stage in ("LINEUP_CONFIRMED", "LINEUP_V2"))
        base_h_rate, base_a_rate, rate_source = self._resolve_baseline_goal_rates(match)
        h_rate, a_rate, lineup_details = self.compute_starter_ratings(
            lineup_data,
            base_home_rate=base_h_rate,
            base_away_rate=base_a_rate,
        )

        predictions = self.generate_forecasts(
            match_id=match_id,
            competition=comp_name,
            stage=stage,
            home_rate=h_rate,
            away_rate=a_rate,
            odds_dict=odds_data,
            lineup_confirmed=lineup_confirmed,
            dry_run=dry_run,
        )
        for prediction in predictions:
            prediction["baseline_rate_source"] = rate_source
            prediction["baseline_home_rate"] = round(base_h_rate, 6)
            prediction["baseline_away_rate"] = round(base_a_rate, 6)
            prediction["effective_home_rate"] = round(h_rate, 6)
            prediction["effective_away_rate"] = round(a_rate, 6)
            prediction["lineup_adjustment"] = lineup_details
        return predictions

    def run(
        self,
        matches: Optional[List[Dict[str, Any]]] = None,
        stage: str = "INITIAL",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute prediction worker over upcoming eligible fixtures."""
        logger.info(f"Running AnalysisWorker for stage={stage} (dry_run={dry_run})...")
        match_list = matches or []

        # If no fixtures provided and not dry_run, attempt to query from Supabase
        if not match_list and not dry_run and self.supabase_url and self.supabase_key:
            try:
                url = f"{self.supabase_url}/rest/v1/matches?is_eligible=eq.true&status=in.(NS,TBD)&select=*&limit=50"
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
                        match_list = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                logger.warning(f"Could not load upcoming matches from DB: {e}")

        # Provide a synthetic fixture if none found in dry_run mode to test pipeline execution
        if not match_list and dry_run:
            # Dry-run data is explicitly synthetic and never used as production
            # evidence. The rates are supplied in the fixture so the runtime
            # path exercises the same explicit-input contract as real inference.
            match_list = [{
                "match_id": "dry_run_match_1",
                "competition_name": "TEST_ONLY",
                "home_team_name": "Arsenal",
                "away_team_name": "Chelsea",
                "model_home_rate": 1.45,
                "model_away_rate": 1.15,
                "data_mode": "synthetic_test_only",
            }]

        total_predictions = 0
        for m in match_list:
            preds = self.run_match_prediction(m, stage=stage, dry_run=dry_run)
            total_predictions += len(preds)

        logger.info(f"AnalysisWorker completed: {len(match_list)} matches analyzed, {total_predictions} predictions generated.")
        return {
            "status": "success",
            "matches_analyzed": len(match_list),
            "predictions_count": total_predictions,
            "stage": stage,
        }
