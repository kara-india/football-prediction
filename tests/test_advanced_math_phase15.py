import math
import numpy as np
import pandas as pd

from python.models.count_models import GoalCountModel
from python.models.dynamic_dixon_coles import DynamicDCConfig, ScoreDrivenDixonColes
from python.models.learned_lineup_effects import LearnedLineupEffectModel
from python.models.live_hazard import LearnedLiveHazard


def test_goal_count_model_selects_by_bic_on_overdispersed_data():
    rng = np.random.default_rng(11)
    # Negative-binomial synthetic data with clear overdispersion.
    mean = 2.4
    phi = 0.45
    r = 1.0 / phi
    p = r / (r + mean)
    goals = rng.negative_binomial(r, p, size=1200)

    model = GoalCountModel().fit(goals)

    assert model.fitted
    assert model.selected_distribution in {"poisson", "negative_binomial"}
    assert model.bic_poisson is not None
    assert model.bic_negative_binomial is not None
    assert model.selected_distribution == "negative_binomial"


def test_dynamic_dixon_coles_is_temporal_and_probabilities_sum():
    rng = np.random.default_rng(21)
    teams = list(range(1, 7))
    attack = {1: 0.25, 2: 0.15, 3: 0.05, 4: -0.05, 5: -0.15, 6: -0.25}
    defence = {1: -0.10, 2: -0.05, 3: 0.00, 4: 0.05, 5: 0.10, 6: 0.15}

    rows = []
    base = pd.Timestamp("2024-01-01", tz="UTC")
    for i in range(180):
        h, a = rng.choice(teams, size=2, replace=False)
        lam_h = math.exp(math.log(1.25) + math.log(1.12) + attack[h] - defence[a])
        lam_a = math.exp(math.log(1.25) + attack[a] - defence[h])
        rows.append({
            "home_id": int(h),
            "away_id": int(a),
            "home_goals": int(rng.poisson(lam_h)),
            "away_goals": int(rng.poisson(lam_a)),
            "date": base + pd.Timedelta(days=i * 3),
        })

    df = pd.DataFrame(rows)
    model = ScoreDrivenDixonColes(
        DynamicDCConfig(max_iter=40)
    ).fit(df)

    p = model.predict_1x2(1, 2)
    assert math.isclose(sum(p), 1.0, rel_tol=1e-6)
    h_xg, a_xg = model.get_expected_goals(1, 2)
    assert h_xg > 0
    assert a_xg > 0
    assert model.metrics["n_matches"] == 180
    assert model.metrics["mean_one_step_log_likelihood"] < 0


def test_lineup_effect_model_learns_player_direction_without_manual_multiplier():
    rng = np.random.default_rng(31)
    rows = []
    players = [str(i) for i in range(1, 13)]

    for _ in range(400):
        own = rng.choice(players, size=3, replace=False).tolist()
        opp = rng.choice(players, size=3, replace=False).tolist()

        own_effect = 0.30 if "1" in own else 0.0
        opp_effect = -0.20 if "12" in opp else 0.0
        lam = math.exp(math.log(1.25) + own_effect + opp_effect)
        rows.append({
            "goals": int(rng.poisson(lam)),
            "baseline_log_rate": math.log(1.25),
            "own_starters": own,
            "opponent_starters": opp,
        })

    model = LearnedLineupEffectModel(l2_attack=2.0, l2_defence=2.0).fit(
        pd.DataFrame(rows)
    )

    strong = model.predict_log_rate_delta(["1"], [])
    neutral = model.predict_log_rate_delta(["2"], [])
    assert strong > neutral


def test_live_hazard_fits_and_changes_correction_from_observed_state():
    rng = np.random.default_rng(41)
    rows = []
    for _ in range(1800):
        minute = float(rng.integers(1, 91))
        score_diff = float(rng.integers(-2, 3))
        red_diff = float(rng.integers(-1, 2))
        sot_diff = float(rng.normal())
        xg_diff = float(rng.normal())
        sub_diff = float(rng.normal())
        knockout = float(rng.integers(0, 2))
        home = float(rng.integers(0, 2))

        eta = (
            -3.65
            + 0.30 * (minute / 90.0)
            - 0.18 * red_diff
            + 0.05 * score_diff
            + 0.04 * sot_diff
            + 0.03 * xg_diff
            + 0.02 * sub_diff
            + 0.02 * knockout
            + 0.03 * home
        )
        prob = 1.0 - math.exp(-math.exp(eta))
        goal = int(rng.random() < prob)

        rows.append({
            "minute": minute,
            "score_diff": score_diff,
            "red_card_diff": red_diff,
            "shots_on_target_diff": sot_diff,
            "xg_diff": xg_diff,
            "substitution_diff": sub_diff,
            "knockout_context": knockout,
            "home_indicator": home,
            "goal": goal,
        })

    model = LearnedLiveHazard(l2=1.0).fit(pd.DataFrame(rows))
    neutral = float(model.correction_multiplier(
        minute=50, score_diff=0, red_card_diff=0,
        shots_on_target_diff=0, xg_diff=0, substitution_diff=0,
        knockout_context=0, home_indicator=1
    )[0])
    state_changed = float(model.correction_multiplier(
        minute=50, score_diff=0, red_card_diff=1,
        shots_on_target_diff=0, xg_diff=0, substitution_diff=0,
        knockout_context=0, home_indicator=1
    )[0])

    assert model.fitted
    assert np.isfinite(neutral)
    assert np.isfinite(state_changed)
    assert neutral > 0
    assert state_changed > 0
    assert not math.isclose(neutral, state_changed, rel_tol=1e-3, abs_tol=1e-6)


def test_dynamic_dixon_coles_fit_as_of_excludes_future_rows():
    base = pd.Timestamp("2025-01-01", tz="UTC")
    rows = []
    for i in range(80):
        rows.append({
            "home_id": 1 if i % 2 == 0 else 2,
            "away_id": 2 if i % 2 == 0 else 1,
            "home_goals": 1,
            "away_goals": 0,
            "date": base + pd.Timedelta(days=i),
        })

    df = pd.DataFrame(rows)
    model = ScoreDrivenDixonColes(
        DynamicDCConfig(max_iter=20)
    ).fit_as_of(df, base + pd.Timedelta(days=40))

    assert model.metrics["n_matches"] == 40


def test_analysis_worker_requires_real_rate_source():
    from python.workers.analysis_worker import AnalysisWorker

    worker = AnalysisWorker()
    try:
        worker._resolve_baseline_goal_rates({
            "match_id": "test",
            "home_team_id": 1,
            "away_team_id": 2,
        })
    except RuntimeError as exc:
        assert "No fitted point-in-time goal-rate source" in str(exc)
    else:
        raise AssertionError("Worker accepted missing model rates.")
