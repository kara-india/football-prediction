import math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from python.models.dixon_coles import DixonColesModel
from python.models.form import FormCalculator, MultiDimensionalForm
from python.models.count_models import GoalCountModel, CardCountModel, CornerCountModel


class TestDixonColesIdentifiabilityAndTimeDecay:
    """Rigorous tests for Dixon-Coles identifiability and time decay weighting."""

    @pytest.fixture
    def sample_league_matches(self):
        """Generate a realistic 6-team double round-robin match dataset spanning 3 years."""
        teams = [1, 2, 3, 4, 5, 6]
        matches = []
        base_date = datetime(2023, 1, 1)

        # 3 seasons of fixtures with dates
        for season in range(3):
            for i, home in enumerate(teams):
                for away in teams:
                    if home == away:
                        continue
                    # Match date spaced across seasons
                    match_date = base_date + timedelta(days=season * 365 + i * 14)
                    # Team 1 is dominant, Team 6 is weak
                    h_strength = (7 - home) * 0.4
                    a_strength = (7 - away) * 0.3
                    h_goals = int(np.clip(np.random.poisson(max(0.5, h_strength)), 0, 7))
                    a_goals = int(np.clip(np.random.poisson(max(0.3, a_strength)), 0, 7))

                    matches.append({
                        "home_id": home,
                        "away_id": away,
                        "home_goals": h_goals,
                        "away_goals": a_goals,
                        "date": match_date.strftime("%Y-%m-%d"),
                    })

        return pd.DataFrame(matches)

    def test_identifiability_mean_attack_equals_one(self, sample_league_matches):
        """Verify sum-to-one identifiability constraint: (1/N) * sum(alpha) == 1.0000."""
        model = DixonColesModel(xi=0.0019)
        model.fit(sample_league_matches, max_iter=100)

        assert model.fitted is True
        alphas = list(model.attack_params.values())
        mean_alpha = float(np.mean(alphas))

        # Must equal 1.0000 within machine precision
        assert math.isclose(mean_alpha, 1.0, abs_tol=1e-5)
        # All attack parameters must be strictly positive
        assert all(a > 0.05 for a in alphas)

    def test_time_decay_downweights_historical_matches(self):
        """Verify time decay weight w(t) downweights 3-year-old matches relative to 7 days ago."""
        times = np.array([0.0, 1000.0, 1088.0, 1095.0])  # Day 0 (3y ago), Day 1095 (now)
        current_time = 1095.0
        xi = 0.0019  # Half life ~ 365 days

        weights = DixonColesModel._calculate_weights(times, current_time, xi)

        # Weight at current time (delta = 0) must be 1.0
        assert math.isclose(weights[3], 1.0, rel_tol=1e-5)
        # Weight 7 days ago must be ~0.987
        assert 0.98 < weights[2] < 1.0
        # Weight ~3 years ago (delta = 1095) must be significantly downweighted (< 0.15)
        assert weights[0] < 0.15
        # Weights must be strictly monotonically increasing with recency
        assert weights[0] < weights[1] < weights[2] <= weights[3]

    def test_optimizer_convergence_without_singular_matrix(self, sample_league_matches):
        """Verify SLSQP optimizer converges reliably without NaN or infinite values."""
        model = DixonColesModel(xi=0.0019)
        model.fit(sample_league_matches, max_iter=150)

        assert model.metrics.get("converged") is True
        assert np.isfinite(model.metrics.get("final_neg_log_lik"))
        assert 0.5 <= model.home_advantage <= 3.0
        assert -0.25 <= model.rho <= 0.25

    def test_model_serialization_roundtrip(self, sample_league_matches):
        """Verify serialize() and from_dict() faithfully preserve all model parameters."""
        model = DixonColesModel(xi=0.0019)
        model.fit(sample_league_matches, max_iter=80)

        serialized = model.serialize()
        assert serialized["model_type"] == "DixonColesModel"
        assert "attack_params" in serialized
        assert "defense_params" in serialized

        reconstructed = DixonColesModel.from_dict(serialized)
        assert reconstructed.fitted is True
        assert reconstructed.home_advantage == model.home_advantage
        assert reconstructed.rho == model.rho
        assert reconstructed.xi == model.xi

        # Compare predicted probabilities
        prob_orig = model.predict_1x2(1, 2)
        prob_recon = reconstructed.predict_1x2(1, 2)
        assert pytest.approx(prob_orig) == prob_recon


class TestMultiDimensionalForm:
    """Tests for multi-channel dynamic form decomposition and decay."""

    def test_multidimensional_form_channels(self):
        fc = FormCalculator(half_life_matches=5.0)
        results = [
            {
                "date": "2024-03-01",
                "goals_scored": 3,
                "shots_on_target": 7,
                "goals_conceded": 0,
                "shots_on_target_conceded": 2,
                "corners_won": 8,
                "corners_conceded": 2,
                "yellow_cards": 1,
                "red_cards": 0,
                "fouls": 9,
            },
            {
                "date": "2024-02-23",
                "goals_scored": 2,
                "shots_on_target": 5,
                "goals_conceded": 1,
                "shots_on_target_conceded": 3,
                "corners_won": 6,
                "corners_conceded": 4,
                "yellow_cards": 2,
                "red_cards": 0,
                "fouls": 11,
            },
        ]

        form = fc.calculate_multidimensional_form(results)
        assert isinstance(form, MultiDimensionalForm)
        assert form.attacking_form > 1.0
        assert form.defensive_form < form.attacking_form
        assert form.territorial_form > 0.50  # Won more corners than conceded
        assert form.disciplinary_form > 0.0
        assert form.composite_index > 1.0

    def test_form_half_life_decay(self):
        """Recent matches must exert greater influence on EWMA than older matches."""
        fc = FormCalculator(half_life_matches=3.0)
        # Recent explosion of goals vs old dry spell
        results = [
            {"date": "2024-03-10", "goals_scored": 4},  # Most recent
            {"date": "2024-03-01", "goals_scored": 3},
            {"date": "2024-02-01", "goals_scored": 0},
            {"date": "2024-01-01", "goals_scored": 0},
        ]
        ewma = fc.calculate_ewma_form(results, "goals_scored")
        # Unweighted average is 1.75; EWMA with recent high scores should be significantly higher (> 2.0)
        assert ewma > 2.0


class TestCountModels:
    """Tests for specialized Goal, Card, and Corner count distributions."""

    def test_goal_count_overdispersion_detection(self):
        # 1. Equidispersed sample (Poisson-like)
        equi_goals = np.array([2, 1, 3, 2, 2, 1, 2, 3, 2, 1, 2, 2])
        model_equi = GoalCountModel().fit(equi_goals)
        assert model_equi.is_overdispersed is False

        # 2. Highly overdispersed sample (variance >> mean)
        over_goals = np.array([0, 0, 7, 0, 6, 0, 5, 0, 0, 8, 1, 0])
        model_over = GoalCountModel().fit(over_goals)
        assert model_over.is_overdispersed is True
        assert model_over.phi > 0.0

        # Exact and cumulative predictions sum properly
        p0 = model_over.predict_exact(0)
        p_over, p_under = model_over.predict_over_under(2.5)
        assert 0.0 <= p0 <= 1.0
        assert math.isclose(p_over + p_under, 1.0, rel_tol=1e-5)

    def test_card_count_conditioning(self):
        model = CardCountModel(base_cards=4.0, phi=0.15)
        # Strict referee and high-aggression derby
        derby_pred = model.predict_cards_conditioned(
            referee_strictness=1.3,
            team_home_aggression=1.2,
            team_away_aggression=1.2,
            match_intensity=1.25,
        )
        # Calm friendly match
        friendly_pred = model.predict_cards_conditioned(
            referee_strictness=0.8,
            team_home_aggression=0.8,
            team_away_aggression=0.8,
            match_intensity=0.8,
        )

        assert derby_pred["expected_cards"] > friendly_pred["expected_cards"]
        assert derby_pred["over_45"] > friendly_pred["over_45"]

    def test_corner_count_conditioning(self):
        model = CornerCountModel(base_corners=10.0, phi=0.10)
        # High crossing, high shot volume
        attacking_game = model.predict_corners_conditioned(
            home_wing_factor=1.3,
            away_wing_factor=1.2,
            total_shot_volume_factor=1.25,
        )
        # Low shot volume, central congestion
        congested_game = model.predict_corners_conditioned(
            home_wing_factor=0.8,
            away_wing_factor=0.8,
            total_shot_volume_factor=0.8,
        )

        assert attacking_game["expected_corners"] > congested_game["expected_corners"]
        assert attacking_game["over_95"] > congested_game["over_95"]
