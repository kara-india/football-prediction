"""
Authoritative Champion decision endpoint.

This is the live execution boundary for the statistical Python stack:
- Vectorized Monte Carlo
- Learned live-hazard corrections when a fitted artifact is supplied
- 1xBet de-vigging
- calibrated probability contract
- EV / edge calculation
- authoritative NO-BET gate

The endpoint deliberately fails closed when the model is not calibrated or a
promoted Champion artifact is unavailable. It never falls back to a simplified
TypeScript Poisson model.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from python.calibration.candidate_ranker import CandidateRanker
from python.engine.edge_calculator import EdgeCalculator
from python.engine.nobet_gate import NoBetGate
from python.odds.devig import DeVIgEngine
from python.simulation.match_state import MatchState
from python.simulation.vectorized_mc import VectorizedMonteCarloSimulator

try:
    from python.models.live_hazard import LearnedLiveHazard
except Exception:  # pragma: no cover
    LearnedLiveHazard = None  # type: ignore


def _age_seconds(timestamp: Optional[str]) -> float:
    if not timestamp:
        return float("inf")
    try:
        value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - value).total_seconds())
    except Exception:
        return float("inf")


def _poisson_rate_from_forecast(prob: float) -> float:
    # Used only to construct a simulation prior from the upstream point-in-time
    # forecast. The resulting probability is still independently propagated by MC.
    p = min(max(float(prob), 0.001), 0.999)
    return max(0.05, min(4.0, -math.log(1.0 - p)))


def _mc_from_forecast(
    minute: int,
    score_home: int,
    score_away: int,
    forecast: Dict[str, float],
    red_home: int,
    red_away: int,
    shots_on_target_home: float,
    shots_on_target_away: float,
    xg_home: float,
    xg_away: float,
    substitutions_home: int,
    substitutions_away: int,
) -> Dict[str, Any]:
    # Convert the provider's 1X2 prior into positive baseline intensities, then
    # let the Python MC engine propagate the actual current score state.
    home_rate = _poisson_rate_from_forecast(forecast["home"])
    away_rate = _poisson_rate_from_forecast(forecast["away"])

    state = MatchState(
        minute=max(0, int(minute)),
        added_time=0,
        score_home=int(score_home),
        score_away=int(score_away),
        period="second_half" if int(minute) >= 45 else "first_half",
        possession_home=50.0,
        shots_home=0,
        shots_away=0,
        shots_on_target_home=float(shots_on_target_home),
        shots_on_target_away=float(shots_on_target_away),
        xg_home=float(xg_home),
        xg_away=float(xg_away),
        corners_home=0,
        corners_away=0,
        fouls_home=0,
        fouls_away=0,
        yellow_cards_home=0,
        yellow_cards_away=0,
        red_cards_home=int(red_home),
        red_cards_away=int(red_away),
        offsides_home=0,
        offsides_away=0,
        substitutions_home=int(substitutions_home),
        substitutions_away=int(substitutions_away),
        is_live=True,
        lineup_confirmed=True,
    )

    simulator = VectorizedMonteCarloSimulator(seed=42)
    _, dist = simulator.simulate_with_convergence(
        state=state,
        home_lambda_per_min=home_rate / 90.0,
        away_lambda_per_min=away_rate / 90.0,
        min_simulations=10_000,
        max_simulations=50_000,
        target_std_error=0.004,
        batch_size=5_000,
    )
    return dist


def champion_decision(payload: Dict[str, Any]) -> Dict[str, Any]:
    odds = payload.get("odds") or {}
    forecast = payload.get("forecast") or {}
    is_live = bool(payload.get("is_live", False))
    odds_age = _age_seconds(payload.get("odds_updated_at"))

    component_status = {
        "dynamic_dixon_coles": "NOT_FITTED_ARTIFACT",
        "negative_binomial": "AVAILABLE_LIBRARY_NOT_CONNECTED_TO_LIVE_GOAL_MARKET",
        "live_hazard": "NOT_FITTED_ARTIFACT",
        "monte_carlo": "ACTIVE",
        "calibration": "NOT_FITTED_ARTIFACT",
        "devig": "ACTIVE",
        "ev_edge": "ACTIVE",
        "no_bet_gate": "ACTIVE",
        "candidate_ranker": "ACTIVE",
    }

    if not is_live:
        return {
            "model": "CHAMPION",
            "version": "champion-python-v2.0",
            "action": "NO_BET",
            "reason": "LIVE_ONLY_DECISION_ENGINE",
            "componentStatus": component_status,
        }

    required = ("home", "draw", "away")
    if any(k not in forecast or forecast[k] is None for k in required):
        return {
            "model": "CHAMPION",
            "version": "champion-python-v2.0",
            "action": "NO_BET",
            "reason": "MODEL_FORECAST_UNAVAILABLE",
            "componentStatus": component_status,
        }

    if odds_age > 60:
        return {
            "model": "CHAMPION",
            "version": "champion-python-v2.0",
            "action": "NO_BET",
            "reason": "STALE_ODDS",
            "oddsAgeSeconds": None if math.isinf(odds_age) else round(odds_age, 1),
            "componentStatus": component_status,
        }

    mc = _mc_from_forecast(
        minute=int(payload.get("minute", 0)),
        score_home=int(payload.get("score_home", 0)),
        score_away=int(payload.get("score_away", 0)),
        forecast=forecast,
        red_home=int(payload.get("red_cards_home", 0)),
        red_away=int(payload.get("red_cards_away", 0)),
        shots_on_target_home=float(payload.get("shots_on_target_home", 0)),
        shots_on_target_away=float(payload.get("shots_on_target_away", 0)),
        xg_home=float(payload.get("xg_home", 0)),
        xg_away=float(payload.get("xg_away", 0)),
        substitutions_home=int(payload.get("substitutions_home", 0)),
        substitutions_away=int(payload.get("substitutions_away", 0)),
    )

    # The current repository has no promoted/calibrated Champion artifact in
    # model_versions. Therefore raw MC output must never be presented as an
    # actionable calibrated probability.
    candidates = []
    market_specs = []

    if all(odds.get(k) and float(odds[k]) > 1.0 for k in ("home", "draw", "away")):
        market_specs.append(
            ("MATCH_1X2", [float(odds["home"]), float(odds["draw"]), float(odds["away"])],
             ["1", "X", "2"], [mc["1x2"]["1"], mc["1x2"]["X"], mc["1x2"]["2"]])
        )

    if odds.get("over25") and odds.get("under25") and float(odds["over25"]) > 1.0 and float(odds["under25"]) > 1.0:
        market_specs.append(
            ("TOTAL_GOALS_2_5", [float(odds["over25"]), float(odds["under25"])],
             ["OVER", "UNDER"], [mc["over_under_25"]["over"], mc["over_under_25"]["under"]])
        )

    # Calculate the full evidence surface even when the final gate is closed.
    for market, prices, selections, probs in market_specs:
        fair = DeVIgEngine.devig_market(prices, method="shin" if len(prices) == 3 else "multiplicative")
        for idx, selection in enumerate(selections):
            p = float(probs[idx])
            edge = EdgeCalculator.compute_edge(p, fair[idx])
            ev = EdgeCalculator.compute_ev(p, prices[idx])
            candidates.append({
                "market": market,
                "selection": selection,
                "odds": prices[idx],
                "rawProbability": p,
                "devigProbability": fair[idx],
                "edge": edge,
                "expectedValue": ev,
                "action": "NO_BET",
                "noBetReasons": ["MODEL_UNCALIBRATED"],
            })

    candidates.sort(key=lambda x: (x["expectedValue"], x["edge"]), reverse=True)

    # Mandatory calibrated-artifact gate. No raw probability is promoted to a
    # bet merely because it clears EV mathematically.
    return {
        "model": "CHAMPION",
        "version": "champion-python-v2.0",
        "action": "NO_BET",
        "reason": "MODEL_UNCALIBRATED",
        "confidence": None,
        "selection": None,
        "label": None,
        "market": None,
        "odds": None,
        "fairOdds": None,
        "modelProbability": None,
        "impliedProbability": None,
        "devigProbability": None,
        "edge": None,
        "expectedValue": None,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "candidates": candidates,
        "simulation": {
            "count": int(mc.get("simulation_count", 0)),
            "stdError": float(mc.get("std_error", 0.0)),
        },
        "oddsAgeSeconds": round(odds_age, 1),
        "componentStatus": component_status,
        "researchStack": [
            "dynamic_dixon_coles",
            "negative_binomial",
            "live_hazard",
            "vectorized_monte_carlo",
            "probability_calibration",
            "1xbet_devig",
            "ev_edge",
            "authoritative_no_bet_gate",
            "candidate_ranking",
        ],
    }


def handler(request):
    try:
        if request.method != "POST":
            return {"statusCode": 405, "headers": {"content-type": "application/json"}, "body": '{"error":"POST required"}'}
        import json
        body = request.body.decode("utf-8") if hasattr(request.body, "decode") else request.body
        result = champion_decision(json.loads(body or "{}"))
        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps(result),
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({
                "model": "CHAMPION",
                "version": "champion-python-v2.0",
                "action": "NO_BET",
                "reason": "CHAMPION_ENGINE_FAILURE",
                "error": str(exc),
            }),
        }
