"""Authoritative live Champion inference using the validated Python research stack."""
from __future__ import annotations
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from python.calibration.calibrator import ProbabilityCalibrator
from python.engine.edge_calculator import EdgeCalculator
from python.engine.nobet_gate import NoBetGate
from python.odds.devig import DeVIgEngine
from python.simulation.match_state import MatchState
from python.simulation.vectorized_mc import VectorizedMonteCarloSimulator
from python.models.dynamic_dixon_coles import ScoreDrivenDixonColes
from python.models.live_hazard import LearnedLiveHazard

ARTIFACT_PATH = Path(__file__).resolve().parent / "models" / "champion_artifact.json"
VERSION = "champion-python-v3.0"
MIN_CONFIDENCE = 0.55

def _age_seconds(value: Optional[str]) -> float:
    if not value:
        return float("inf")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return float("inf")

def _load_artifact() -> Dict[str, Any]:
    if ARTIFACT_PATH.exists():
        with ARTIFACT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
    if not url or not key:
        raise RuntimeError("CHAMPION_ARTIFACT_UNAVAILABLE")
    endpoint = f"{url.rstrip('/')}/rest/v1/champion_artifacts?select=artifact&is_active=eq.true&order=created_at.desc&limit=1"
    response = httpx.get(endpoint, headers={"apikey": key, "Authorization": "Bearer " + key}, timeout=10.0)
    response.raise_for_status()
    rows = response.json()
    if not rows:
        raise RuntimeError("CHAMPION_ARTIFACT_UNAVAILABLE")
    return rows[0]["artifact"]

def _calibrate(cal: ProbabilityCalibrator, market: str, p: float) -> float:
    if market not in cal.calibrators:
        raise RuntimeError(f"CALIBRATION_UNAVAILABLE:{market}")
    return float(cal.calibrate(float(p), market=market))

def decide(payload: Dict[str, Any]) -> Dict[str, Any]:
    checked = datetime.now(timezone.utc).isoformat()
    base = {"model": "CHAMPION", "version": VERSION, "checkedAt": checked}
    if not payload.get("is_live"):
        return {**base, "action": "NO_BET", "reason": "LIVE_ONLY_DECISION_ENGINE"}

    odds = payload.get("odds") or {}
    age = _age_seconds(payload.get("odds_updated_at"))
    if age > 60:
        return {**base, "action": "NO_BET", "reason": "STALE_ODDS",
                "oddsAgeSeconds": None if math.isinf(age) else round(age, 1)}

    try:
        artifact = _load_artifact()
        dc = ScoreDrivenDixonColes.deserialize(artifact["dynamic_dixon_coles"])
        cal = ProbabilityCalibrator.from_dict(artifact["calibration"])
    except Exception as exc:
        return {**base, "action": "NO_BET", "reason": str(exc)}

    home, away = str(payload.get("home_team") or ""), str(payload.get("away_team") or "")
    if not home or not away:
        return {**base, "action": "NO_BET", "reason": "TEAM_IDENTITIES_UNAVAILABLE"}

    try:
        pre_h, pre_a = dc.get_expected_goals(home, away)
    except Exception as exc:
        return {**base, "action": "NO_BET", "reason": "DYNAMIC_DC_FAILURE", "error": str(exc)}

    hazard = None
    hazard_data = artifact.get("live_hazard")
    if hazard_data and hazard_data.get("status") == "fitted":
        hazard = LearnedLiveHazard.deserialize(hazard_data)

    minute = int(payload.get("minute") or 0)
    state = MatchState(
        minute=minute, added_time=int(payload.get("added_time") or 0),
        score_home=int(payload.get("score_home") or 0), score_away=int(payload.get("score_away") or 0),
        period="second_half" if minute >= 45 else "first_half",
        possession_home=float(payload.get("possession_home") or 50),
        shots_home=int(payload.get("shots_home") or 0), shots_away=int(payload.get("shots_away") or 0),
        shots_on_target_home=int(payload.get("shots_on_target_home") or 0),
        shots_on_target_away=int(payload.get("shots_on_target_away") or 0),
        xg_home=float(payload.get("xg_home") or 0), xg_away=float(payload.get("xg_away") or 0),
        corners_home=0, corners_away=0, fouls_home=0, fouls_away=0,
        yellow_cards_home=0, yellow_cards_away=0,
        red_cards_home=int(payload.get("red_cards_home") or 0),
        red_cards_away=int(payload.get("red_cards_away") or 0),
        offsides_home=0, offsides_away=0,
        substitutions_home=int(payload.get("substitutions_home") or 0),
        substitutions_away=int(payload.get("substitutions_away") or 0),
        is_live=True, lineup_confirmed=True,
        knockout_context=float(payload.get("knockout_context") or 0),
    )

    sim = VectorizedMonteCarloSimulator(seed=42, live_hazard_model=hazard)
    _, dist = sim.simulate_with_convergence(
        state, pre_h / 90.0, pre_a / 90.0,
        min_simulations=10000, max_simulations=50000,
        target_std_error=0.004, batch_size=5000,
        live_hazard_model=hazard,
    )

    candidates: List[Dict[str, Any]] = []
    specs = []
    if all(odds.get(k) is not None and float(odds[k]) > 1 for k in ("home", "draw", "away")):
        specs.append(("MATCH_1X2",
                      [float(odds["home"]), float(odds["draw"]), float(odds["away"])],
                      ["1", "X", "2"],
                      [dist["1x2"]["1"], dist["1x2"]["X"], dist["1x2"]["2"]], "shin"))
    if all(odds.get(k) is not None and float(odds[k]) > 1 for k in ("over25", "under25")):
        specs.append(("TOTAL_GOALS_2_5",
                      [float(odds["over25"]), float(odds["under25"])],
                      ["OVER", "UNDER"],
                      [dist["over_under_25"]["over"], dist["over_under_25"]["under"]], "multiplicative"))

    historical = int(artifact.get("validation", {}).get("training_sample_size", 0))
    gate = NoBetGate()

    for market, prices, selections, raw_probs, method in specs:
        fair = DeVIgEngine.devig_market(prices, method=method)
        for idx, (selection, raw_p, price) in enumerate(zip(selections, raw_probs, prices)):
            try:
                p = _calibrate(cal, f"{market}:{selection}", float(raw_p))
                calibrated = True
            except Exception:
                p = float(raw_p)
                calibrated = False
            lower = max(0.0, p - 1.96 * float(dist["std_error"]))
            upper = min(1.0, p + 1.96 * float(dist["std_error"]))
            ev = EdgeCalculator.compute_ev(p, price)
            edge = EdgeCalculator.compute_edge(p, fair[idx])
            gate_res = gate.evaluate(
                ev=ev, edge=edge, lineup_confirmed=True,
                odds_age_seconds=age, is_live=True, is_market_suspended=False,
                odds_available=True, odds_1xbet=price,
                monte_carlo_se=float(dist["std_error"]),
                prob_lower=lower, prob_upper=upper,
                model_calibrated=calibrated,
                historical_sample_size=historical,
            )
            candidates.append({
                "market": market, "selection": selection, "odds": price,
                "modelProbability": p, "fairOdds": 1 / p if p > 0 else None,
                "impliedProbability": 1 / price, "devigProbability": fair[idx],
                "edge": edge, "expectedValue": ev, "confidence": p,
                "probabilityLower": lower, "probabilityUpper": upper,
                "simulationCount": int(dist["simulation_count"]),
                "decision": gate_res.action, "noBetReasons": gate_res.reasons,
                "score": max(0, ev) * p,
            })

    valid = [c for c in candidates if c["decision"] == "BET" and c["confidence"] >= MIN_CONFIDENCE]
    valid.sort(key=lambda c: c["score"], reverse=True)
    candidates.sort(key=lambda c: (c["decision"] == "BET", c["score"]), reverse=True)

    components = {
        "dynamic_dixon_coles": "ACTIVE",
        "monte_carlo": "ACTIVE",
        "calibration": "ACTIVE",
        "devig": "ACTIVE",
        "ev_edge": "ACTIVE",
        "no_bet_gate": "ACTIVE",
        "candidate_ranker": "ACTIVE",
        "live_hazard": "ACTIVE" if hazard else "NOT_AVAILABLE_NO_TRAINING_DATA",
        "negative_binomial": "CHALLENGER_NOT_SELECTED_FOR_GOAL_MARKET",
    }

    if not valid:
        return {
            **base, "action": "NO_BET", "reason": "NO_MARKET_PASSES_CHAMPION_GATE",
            "confidence": max([c["confidence"] for c in candidates], default=None),
            "candidates": candidates,
            "simulation": {"count": int(dist["simulation_count"]), "stdError": float(dist["std_error"])},
            "componentStatus": components,
            "researchStack": ["dynamic_dixon_coles", "learned_live_hazard_if_fitted",
                              "vectorized_monte_carlo", "probability_calibration", "1xbet_devig",
                              "ev_edge", "authoritative_no_bet_gate", "candidate_ranking"],
        }

    winner = valid[0]
    label = ("Draw" if winner["selection"] == "X" else
             home if winner["selection"] == "1" else
             away if winner["selection"] == "2" else winner["selection"])
    return {
        **base, "action": "BET", "reason": "BEST_VALUE_MARKET",
        "confidence": winner["confidence"], "selection": winner["selection"],
        "market": winner["market"], "odds": winner["odds"], "label": label,
        "fairOdds": winner["fairOdds"], "modelProbability": winner["modelProbability"],
        "impliedProbability": winner["impliedProbability"], "devigProbability": winner["devigProbability"],
        "edge": winner["edge"], "expectedValue": winner["expectedValue"],
        "probabilityLower": winner["probabilityLower"], "probabilityUpper": winner["probabilityUpper"],
        "candidates": candidates,
        "simulation": {"count": winner["simulationCount"], "stdError": float(dist["std_error"])},
        "componentStatus": components,
        "researchStack": ["dynamic_dixon_coles", "learned_live_hazard_if_fitted",
                          "vectorized_monte_carlo", "probability_calibration", "1xbet_devig",
                          "ev_edge", "authoritative_no_bet_gate", "candidate_ranking"],
    }
