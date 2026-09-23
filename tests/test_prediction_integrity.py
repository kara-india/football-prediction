import types

import numpy as np
import pandas as pd
import pytest

from python.adapters.api_football import APIError, APIFootballAdapter
from python.backtesting.walk_forward import WalkForwardValidator
from python.models.dixon_coles import DixonColesModel
from python.workers.analysis_worker import AnalysisWorker


def test_api_football_refuses_request_without_configured_key():
    adapter = APIFootballAdapter(api_key=None)
    with pytest.raises(APIError, match="API_FOOTBALL_KEY is not configured"):
        adapter._make_request("status")


def test_analysis_worker_never_invents_odds_or_calibration():
    worker = AnalysisWorker(calibrator=None)
    predictions = worker.generate_forecasts(
        match_id="integrity-test",
        competition="Test Competition",
        stage="INITIAL",
        home_rate=1.4,
        away_rate=1.1,
        odds_dict=None,
        lineup_confirmed=False,
        dry_run=True,
    )

    assert predictions
    assert all(p["decimal_odds"] is None for p in predictions)
    assert all(p["expected_value"] is None for p in predictions)
    assert all(p["value_edge"] is None for p in predictions)
    assert all(p["calibration_version"] == "UNAVAILABLE" for p in predictions)
    assert all(p["calibration_applied"] is False for p in predictions)
    assert all(p["recommended_action"] == "NO_BET" for p in predictions)
    assert all("ODDS_UNAVAILABLE" in p["no_bet_reasons"] for p in predictions)
    assert all("MODEL_UNCALIBRATED" in p["no_bet_reasons"] for p in predictions)


def test_analysis_worker_persists_actual_simulation_count():
    worker = AnalysisWorker(calibrator=None)
    worker.simulator.MIN_SIMULATIONS = 50
    worker.simulator.MAX_SIMULATIONS = 100
    worker.simulator.TARGET_STD_ERROR = 1.0

    predictions = worker.generate_forecasts(
        match_id="mc-count-test",
        competition="Test Competition",
        stage="INITIAL",
        home_rate=1.4,
        away_rate=1.1,
        odds_dict=None,
        lineup_confirmed=False,
        dry_run=True,
    )

    count = predictions[0]["simulation_count"]
    assert count >= 50
    assert count <= 100


def test_dixon_coles_xi_profile_restores_best_fit():
    model = DixonColesModel(xi=0.5)
    matches = pd.DataFrame([
        {"home_id": 1, "away_id": 2, "home_goals": 1, "away_goals": 0, "date": "2024-01-01"},
        {"home_id": 2, "away_id": 1, "home_goals": 0, "away_goals": 1, "date": "2024-01-08"},
    ])

    fitted_states = {
        0.1: ({"A": 1.1}, {"A": 0.9}, 1.2, -0.1, 10.0),
        0.2: ({"A": 1.2}, {"A": 0.8}, 1.3, -0.2, 5.0),
    }

    def fake_fit(self, _matches, xi=None, max_iter=60):
        attack, defense, home_advantage, rho, nll = fitted_states[xi]
        self.xi = xi
        self.attack_params = dict(attack)
        self.defense_params = dict(defense)
        self.home_advantage = home_advantage
        self.rho = rho
        self.teams = ["A"]
        self.metrics = {"final_neg_log_lik": nll}
        self.fitted = True
        return self

    model.fit = types.MethodType(fake_fit, model)
    best = model.estimate_xi_profile_likelihood(matches, xi_grid=[0.1, 0.2])

    assert best == pytest.approx(0.2)
    assert model.xi == pytest.approx(0.2)
    assert model.attack_params == {"A": 1.2}
    assert model.defense_params == {"A": 0.8}
    assert model.home_advantage == pytest.approx(1.3)


def test_walk_forward_model_comparison_does_not_fabricate_p_value():
    validator = WalkForwardValidator()
    result = validator.compare_models(
        champion_metrics={"mean_brier": 0.20, "total_predictions": 250},
        challenger_metrics={"mean_brier": 0.19, "total_predictions": 250},
    )

    assert result["recommendation"] == "INSUFFICIENT_DATA"
    assert result["winner"] is None
    assert result["p_value"] is None
