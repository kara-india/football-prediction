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
MAX_ARTIFACT_AGE_DAYS = 365

def _age_seconds(value: Optional[str]) -> float:
    if not value:
        return float("inf")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return float("inf")

def _is_valid_decimal_odd(value: Any) -> bool:
    """Return true only for finite decimal odds greater than 1.0."""
    try:
        odd = float(value)
        return math.isfinite(odd) and odd > 1.0
    except (TypeError, ValueError):
        return False


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

def _gate_diagnostics(
    fixture_status: str,
    odds_status: str = "SKIPPED",
    freshness_status: str = "SKIPPED",
    model_status: str = "SKIPPED",
    value_status: str = "SKIPPED",
    details: Optional[Dict[str, str]] = None,
) -> List[Dict[str, str]]:
    """Consistent five-stage decision trace; SKIPPED means that input prerequisites were absent."""
    details = details or {}
    gates = [
        ("FIXTURE_STATUS", "Fixture status supports a decision", fixture_status),
        ("REAL_1XBET_ODDS", "Real 1xBet market available", odds_status),
        ("ODDS_FRESHNESS", "Odds timestamp within applicable freshness limit", freshness_status),
        ("MODEL_READY", "Champion model and forecast ready", model_status),
        ("CONFIDENCE_AND_VALUE", "Confidence and value thresholds passed", value_status),
    ]
    return [
        {"id": gate_id, "label": label, "status": status, "detail": details.get(gate_id, "")}
        for gate_id, label, status in gates
    ]


def _preflight_no_bet(
    base: Dict[str, Any],
    reason: str,
    gates: List[Dict[str, str]],
    **extra: Any,
) -> Dict[str, Any]:
    return {**base, "action": "NO_BET", "reason": reason, "gateDiagnostics": gates, **extra}


def decide(payload: Dict[str, Any]) -> Dict[str, Any]:
    checked = datetime.now(timezone.utc).isoformat()
    base = {"model": "CHAMPION", "version": VERSION, "checkedAt": checked}
    is_live = bool(payload.get("is_live"))
    is_prematch = bool(payload.get("is_prematch"))
    mode = "live" if is_live else "pre-match" if is_prematch else "unsupported"
    if mode == "unsupported":
        return _preflight_no_bet(
            base,
            "FIXTURE_STATUS_NOT_ELIGIBLE",
            _gate_diagnostics(
                "FAIL",
                details={"FIXTURE_STATUS": "Fixture is neither confirmed live nor a confirmed future pre-match fixture."},
            ),
        )

    odds = payload.get("odds") or {}
    required_prices = ("home", "draw", "away", "over25", "under25")
    available_prices = {
        key: float(odds[key])
        for key in required_prices
        if odds.get(key) is not None
        and _is_valid_decimal_odd(odds.get(key))
    }
    has_complete_1x2 = all(key in available_prices for key in ("home", "draw", "away"))
    has_complete_totals = all(key in available_prices for key in ("over25", "under25"))
    if not available_prices:
        return _preflight_no_bet(
            base,
            "LIVE_1XBET_ODDS_UNAVAILABLE" if is_live else "PREMATCH_1XBET_ODDS_UNAVAILABLE",
            _gate_diagnostics(
                "PASS", "FAIL", "SKIPPED", "SKIPPED", "SKIPPED",
                {
                    "FIXTURE_STATUS": "Provider confirms the fixture is live." if is_live else "Provider confirms this is an upcoming pre-match fixture.",
                    "REAL_1XBET_ODDS": "No verified 1xBet prices were supplied by the configured feed.",
                    "ODDS_FRESHNESS": "Skipped because no usable price was supplied.",
                    "MODEL_READY": "Skipped because no usable market is available to evaluate.",
                    "CONFIDENCE_AND_VALUE": "Skipped; confidence and expected value were not calculated.",
                },
            ),
        )
    if not (has_complete_1x2 or has_complete_totals):
        return _preflight_no_bet(
            base,
            "INCOMPLETE_LIVE_1XBET_MARKET" if is_live else "INCOMPLETE_PREMATCH_1XBET_MARKET",
            _gate_diagnostics(
                "PASS", "FAIL", "SKIPPED", "SKIPPED", "SKIPPED",
                {
                    "FIXTURE_STATUS": f"Provider confirms the fixture is {mode}.",
                    "REAL_1XBET_ODDS": "Some prices exist, but no supported market has all required outcomes.",
                    "ODDS_FRESHNESS": "Skipped until a complete market is available.",
                    "MODEL_READY": "Skipped because no complete market can be evaluated.",
                    "CONFIDENCE_AND_VALUE": "Skipped; candidate probabilities and expected value were not calculated.",
                },
            ),
        )

    odds_timestamp = payload.get("odds_updated_at")
    age = _age_seconds(odds_timestamp)
    if not odds_timestamp or not math.isfinite(age):
        return _preflight_no_bet(
            base,
            "ODDS_TIMESTAMP_UNAVAILABLE",
            _gate_diagnostics(
                "PASS", "PASS", "FAIL", "SKIPPED", "SKIPPED",
                {
                    "FIXTURE_STATUS": f"Provider confirms the fixture is {mode}.",
                    "REAL_1XBET_ODDS": "A complete supported market is present.",
                    "ODDS_FRESHNESS": "The feed did not provide a parseable source update timestamp; freshness cannot be verified.",
                    "MODEL_READY": "Skipped until market freshness is verified.",
                    "CONFIDENCE_AND_VALUE": "Skipped; no actionable decision is allowed without verified freshness.",
                },
            ),
        )
    max_odds_age = 60 if is_live else 900
    if age > max_odds_age:
        return _preflight_no_bet(
            base,
            "STALE_ODDS",
            _gate_diagnostics(
                "PASS", "PASS", "FAIL", "SKIPPED", "SKIPPED",
                {
                    "FIXTURE_STATUS": f"Provider confirms the fixture is {mode}.",
                    "REAL_1XBET_ODDS": "A complete supported market is present.",
                    "ODDS_FRESHNESS": f"Source timestamp is {round(age, 1)} seconds old; {mode} limit is {max_odds_age} seconds.",
                    "MODEL_READY": f"Skipped because the {mode} price is stale.",
                    "CONFIDENCE_AND_VALUE": "Skipped; stale prices cannot be used for a bet decision.",
                },
            ),
            oddsAgeSeconds=round(age, 1),
            maxOddsAgeSeconds=max_odds_age,
        )

    try:
        artifact = _load_artifact()
        dc = ScoreDrivenDixonColes.deserialize(artifact["dynamic_dixon_coles"])
        cal = ProbabilityCalibrator.from_dict(artifact["calibration"])
    except Exception as exc:
        return _preflight_no_bet(
            base, str(exc),
            _gate_diagnostics(
                "PASS", "PASS", "PASS", "FAIL", "SKIPPED",
                {
                    "FIXTURE_STATUS": f"Fixture is eligible for {mode} evaluation.",
                    "REAL_1XBET_ODDS": "A complete 1xBet market is present.",
                    "ODDS_FRESHNESS": f"Odds age is within the {max_odds_age}-second {mode} limit.",
                    "MODEL_READY": f"Champion model could not load: {exc}",
                    "CONFIDENCE_AND_VALUE": "Skipped because the model could not run.",
                },
            ),
        )

    artifact_test_end = artifact.get("validation", {}).get("test_end")
    artifact_age = _age_seconds(artifact_test_end)
    if artifact_age > MAX_ARTIFACT_AGE_DAYS * 86400:
        return _preflight_no_bet(
            base, "MODEL_ARTIFACT_STALE",
            _gate_diagnostics(
                "PASS", "PASS", "PASS", "FAIL", "SKIPPED",
                {
                    "FIXTURE_STATUS": f"Fixture is eligible for {mode} evaluation.",
                    "REAL_1XBET_ODDS": "A complete 1xBet market is present.",
                    "ODDS_FRESHNESS": f"Odds age is within the {max_odds_age}-second {mode} limit.",
                    "MODEL_READY": "Champion artifact is outside the allowed age window.",
                    "CONFIDENCE_AND_VALUE": "Skipped because the model artifact is stale.",
                },
            ),
            artifactTestEnd=artifact_test_end,
            artifactAgeDays=None if math.isinf(artifact_age) else round(artifact_age / 86400, 1),
            maxArtifactAgeDays=MAX_ARTIFACT_AGE_DAYS,
        )

    home, away = str(payload.get("home_team") or ""), str(payload.get("away_team") or "")
    if not home or not away:
        return _preflight_no_bet(
            base, "TEAM_IDENTITIES_UNAVAILABLE",
            _gate_diagnostics(
                "PASS", "PASS", "PASS", "FAIL", "SKIPPED",
                {"MODEL_READY": "Team identities were missing; no model inference was run."},
            ),
        )

    # Champion v3 is trained on club-league historical data. Never infer
    # national-team strength by silently falling back to zero team effects.
    trained_teams = set(str(team) for team in getattr(dc, "teams", []))
    if home not in trained_teams or away not in trained_teams:
        return _preflight_no_bet(
            base, "TEAM_OUTSIDE_TRAINING_DOMAIN",
            _gate_diagnostics(
                "PASS", "PASS", "PASS", "FAIL", "SKIPPED",
                {"MODEL_READY": "At least one club is outside the validated Champion training domain."},
            ),
            trainingDomain="club_leagues_only",
            missingTeams=[team for team in (home, away) if team not in trained_teams],
        )

    try:
        pre_h, pre_a = dc.get_expected_goals(home, away)
    except Exception as exc:
        return _preflight_no_bet(
            base, "DYNAMIC_DC_FAILURE",
            _gate_diagnostics(
                "PASS", "PASS", "PASS", "FAIL", "SKIPPED",
                {"MODEL_READY": f"Dynamic Dixon-Coles inference failed: {exc}"},
            ),
            error=str(exc),
        )

    hazard = None
    hazard_data = artifact.get("live_hazard")
    if hazard_data and hazard_data.get("status") == "fitted":
        hazard = LearnedLiveHazard.deserialize(hazard_data)

    minute = int(payload.get("minute") or 0)
    state = MatchState(
        minute=minute, added_time=int(payload.get("added_time") or 0),
        score_home=int(payload.get("score_home") or 0), score_away=int(payload.get("score_away") or 0),
        period=("second_half" if minute >= 45 else "first_half") if is_live else "PREMATCH",
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
        is_live=is_live, lineup_confirmed=bool(payload.get("lineup_confirmed", False)),
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

    lineup_confirmed = bool(payload.get("lineup_confirmed", False))
    home_starters_count = payload.get("home_starters_count")
    away_starters_count = payload.get("away_starters_count")
    player_starter_confirmed = payload.get("player_starter_confirmed")
    player_minutes_uncertain = bool(payload.get("player_minutes_uncertain", False))

    for market, prices, selections, raw_probs, method in specs:
        fair = DeVIgEngine.devig_market(prices, method=method)
        calibrated_probs: List[float] = []
        calibration_flags: List[bool] = []
        for selection, raw_p in zip(selections, raw_probs):
            try:
                p = float(_calibrate(cal, f"{market}:{selection}", float(raw_p)))
                calibrated = True
            except Exception:
                p = float(raw_p)
                calibrated = False
            calibrated_probs.append(p)
            calibration_flags.append(calibrated)

        # Independent binary calibration of 1/X/2 can violate the probability
        # simplex. Normalize the three calibrated probabilities before EV/edge.
        if market == "MATCH_1X2":
            total = sum(max(0.0, p) for p in calibrated_probs)
            if total <= 0.0:
                calibrated_probs = [1.0 / len(calibrated_probs)] * len(calibrated_probs)
            else:
                calibrated_probs = [max(0.0, p) / total for p in calibrated_probs]

        for idx, (selection, price) in enumerate(zip(selections, prices)):
            p = float(calibrated_probs[idx])
            calibrated = calibration_flags[idx]
            lower = max(0.0, p - 1.96 * float(dist["std_error"]))
            upper = min(1.0, p + 1.96 * float(dist["std_error"]))
            ev = EdgeCalculator.compute_ev(p, price)
            edge = EdgeCalculator.compute_edge(p, fair[idx])
            gate_res = gate.evaluate(
                ev=ev, edge=edge,
                lineup_confirmed=lineup_confirmed,
                home_starters_count=int(home_starters_count) if home_starters_count is not None else None,
                away_starters_count=int(away_starters_count) if away_starters_count is not None else None,
                odds_age_seconds=age, is_live=is_live, is_market_suspended=False,
                odds_available=True, odds_1xbet=price,
                monte_carlo_se=float(dist["std_error"]),
                prob_lower=lower, prob_upper=upper,
                model_calibrated=calibrated,
                player_starter_confirmed=player_starter_confirmed,
                player_minutes_uncertain=player_minutes_uncertain,
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
        candidate_failures = sorted({
            reason for candidate in candidates for reason in candidate.get("noBetReasons", [])
        })
        if not any(candidate["confidence"] >= MIN_CONFIDENCE for candidate in candidates):
            candidate_failures.append(f"CONFIDENCE_BELOW_{int(MIN_CONFIDENCE * 100)}_PERCENT")
        gate_diagnostics = _gate_diagnostics(
            "PASS", "PASS", "PASS", "PASS", "FAIL",
            {
                "FIXTURE_STATUS": f"Fixture is eligible for {mode} evaluation.",
                "REAL_1XBET_ODDS": "At least one complete real 1xBet market was evaluated.",
                "ODDS_FRESHNESS": f"Odds age is {round(age, 1)} seconds (limit {max_odds_age}).",
                "MODEL_READY": "Champion model, calibration and simulation completed.",
                "CONFIDENCE_AND_VALUE": ", ".join(sorted(set(candidate_failures))) or "No candidate cleared every value/risk gate.",
            },
        )
        return {
            **base, "action": "NO_BET", "reason": "NO_MARKET_PASSES_CHAMPION_GATE",
            "confidence": max([c["confidence"] for c in candidates], default=None),
            "candidates": candidates,
            "gateDiagnostics": gate_diagnostics,
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
        "gateDiagnostics": _gate_diagnostics(
            "PASS", "PASS", "PASS", "PASS", "PASS",
            {
                "FIXTURE_STATUS": f"Fixture is eligible for {mode} evaluation.",
                "REAL_1XBET_ODDS": "Real 1xBet prices and a complete supported market were found.",
                "ODDS_FRESHNESS": f"Odds age is {round(age, 1)} seconds (limit {max_odds_age}).",
                "MODEL_READY": "Champion model, calibration and simulation completed.",
                "CONFIDENCE_AND_VALUE": "Best candidate passed the confidence threshold and all NoBetGate risk checks.",
            },
        ),
        "simulation": {"count": winner["simulationCount"], "stdError": float(dist["std_error"])},
        "componentStatus": components,
        "researchStack": ["dynamic_dixon_coles", "learned_live_hazard_if_fitted",
                          "vectorized_monte_carlo", "probability_calibration", "1xbet_devig",
                          "ev_edge", "authoritative_no_bet_gate", "candidate_ranking"],
    }
