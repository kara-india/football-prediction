from datetime import datetime, timedelta, timezone

import pytest

from python import champion_service
from python.simulation.match_state import MatchState
from python.simulation.vectorized_mc import VectorizedMonteCarloSimulator


def _iso_age(seconds: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()


def _payload(*, is_live=True, is_prematch=False, odds=None, age_seconds=10):
    return {
        "home_team": "Napoli",
        "away_team": "Frosinone",
        "is_live": is_live,
        "is_prematch": is_prematch,
        "minute": 15 if is_live else 0,
        "score_home": 0,
        "score_away": 0,
        "odds": odds if odds is not None else {"home": 2.1, "draw": 3.2, "away": 3.6},
        "odds_updated_at": _iso_age(age_seconds) if age_seconds is not None else None,
        "lineup_confirmed": True,
        "home_starters_count": 11,
        "away_starters_count": 11,
        "player_starter_confirmed": True,
        "player_minutes_uncertain": False,
    }


def test_live_fixture_without_prices_reports_market_unavailable_not_stale():
    result = champion_service.decide(_payload(odds=None) | {"odds": {}, "odds_updated_at": None})
    assert result["action"] == "NO_BET"
    assert result["reason"] == "LIVE_1XBET_ODDS_UNAVAILABLE"
    assert [gate["status"] for gate in result["gateDiagnostics"]] == [
        "PASS", "FAIL", "SKIPPED", "SKIPPED", "SKIPPED"
    ]


def test_prices_without_source_timestamp_are_not_called_stale_or_fresh():
    result = champion_service.decide(_payload(age_seconds=None))
    assert result["action"] == "NO_BET"
    assert result["reason"] == "ODDS_TIMESTAMP_UNAVAILABLE"
    assert result["gateDiagnostics"][2]["status"] == "FAIL"
    assert "parseable source update timestamp" in result["gateDiagnostics"][2]["detail"]


@pytest.mark.parametrize(
    ("is_live", "is_prematch", "age_seconds", "expected_limit"),
    [
        (True, False, 61, 60),
        (False, True, 901, 900),
    ],
)
def test_stale_timestamp_uses_mode_specific_freshness_limit(
    is_live, is_prematch, age_seconds, expected_limit
):
    result = champion_service.decide(
        _payload(is_live=is_live, is_prematch=is_prematch, age_seconds=age_seconds)
    )
    assert result["action"] == "NO_BET"
    assert result["reason"] == "STALE_ODDS"
    assert result["maxOddsAgeSeconds"] == expected_limit
    assert result["gateDiagnostics"][2]["status"] == "FAIL"


def test_fresh_prematch_market_reaches_model_instead_of_live_only_guard(monkeypatch):
    def model_sentinel():
        raise RuntimeError("MODEL_PRECHECK_REACHED")

    monkeypatch.setattr(champion_service, "_load_artifact", model_sentinel)
    result = champion_service.decide(
        _payload(is_live=False, is_prematch=True, age_seconds=60)
    )
    assert result["reason"] == "MODEL_PRECHECK_REACHED"
    assert result["gateDiagnostics"][0]["status"] == "PASS"
    assert result["gateDiagnostics"][1]["status"] == "PASS"
    assert result["gateDiagnostics"][2]["status"] == "PASS"
    assert result["gateDiagnostics"][3]["status"] == "FAIL"


def test_unconfirmed_or_finished_status_is_not_mistaken_for_prematch():
    result = champion_service.decide(
        _payload(is_live=False, is_prematch=False)
    )
    assert result["action"] == "NO_BET"
    assert result["reason"] == "FIXTURE_STATUS_NOT_ELIGIBLE"
    assert result["gateDiagnostics"][0]["status"] == "FAIL"



def test_prematch_simulation_does_not_apply_live_hazard_corrections():
    class ForbiddenLiveHazard:
        fitted = True

        def correction_multiplier(self, **_kwargs):
            raise AssertionError("in-play hazard correction must not run pre-match")

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
        lineup_confirmed=False,
    )
    simulator = VectorizedMonteCarloSimulator(seed=7)
    paths = simulator.simulate_batch(
        state, home_lambda_per_min=0.02, away_lambda_per_min=0.02,
        n_simulations=100, live_hazard_model=ForbiddenLiveHazard(),
    )
    assert paths.shape == (100, 2)



def test_missing_market_surfaces_provider_suspension_diagnostic():
    result = champion_service.decide(
        _payload(odds={}, age_seconds=None)
        | {
            "odds": {},
            "odds_updated_at": None,
            "odds_feed_issue": "API-Football account is suspended; restore provider access.",
        }
    )
    assert result["reason"] == "LIVE_1XBET_ODDS_UNAVAILABLE"
    market_gate = next(g for g in result["gateDiagnostics"] if g["id"] == "REAL_1XBET_ODDS")
    assert market_gate["status"] == "FAIL"
    assert "account is suspended" in market_gate["detail"]



def test_refreshed_artifact_with_old_validation_cutoff_stays_blocked(monkeypatch):
    # A new trained_at timestamp must not relabel a model trained/validated on
    # old data as current. BET decisions require a recent holdout window.
    old_test_end = (datetime.now(timezone.utc) - timedelta(
        days=champion_service.MAX_ARTIFACT_AGE_DAYS + 1
    )).isoformat()
    artifact = {
        "dynamic_dixon_coles": {},
        "calibration": {},
        "validation": {"test_end": old_test_end},
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    monkeypatch.setattr(champion_service, "_load_artifact", lambda: artifact)
    monkeypatch.setattr(
        champion_service.ScoreDrivenDixonColes, "deserialize", lambda _raw: object()
    )
    monkeypatch.setattr(
        champion_service.ProbabilityCalibrator, "from_dict", lambda _raw: object()
    )

    result = champion_service.decide(_payload(age_seconds=10))
    assert result["action"] == "NO_BET"
    assert result["reason"] == "MODEL_ARTIFACT_STALE"
    assert result["maxArtifactAgeDays"] == champion_service.MAX_ARTIFACT_AGE_DAYS
    assert result["gateDiagnostics"][3]["status"] == "FAIL"
    assert result["gateDiagnostics"][4]["status"] == "SKIPPED"
