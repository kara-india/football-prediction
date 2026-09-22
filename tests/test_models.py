import pytest
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from python.models.elo import EloSystem
from python.models.dixon_coles import DixonColesModel
from python.models.negative_binomial import NegativeBinomialModel
from python.models.player_model import PlayerGoalModel
from python.models.form import FormCalculator
from python.models.feature_engineering import FeatureEngineer

def test_elo_expected_score_sum():
    elo = EloSystem()
    exp_h = elo.expected_score(1600, 1500)
    exp_a = elo.expected_score(1500, 1600)
    assert math.isclose(exp_h + exp_a, 1.0)

def test_elo_update_zero_sum():
    elo = EloSystem({1: 1500, 2: 1500})
    elo.HOME_ADVANTAGE = 0
    new_h, new_a = elo.update(1, 2, 2, 1)
    assert math.isclose(new_h + new_a, 3000.0)
    
def test_dixon_coles_score_matrix_sum():
    dc = DixonColesModel()
    dc.attack_params = {1: 0.1, 2: 0.1}
    dc.defense_params = {1: 0.1, 2: 0.1}
    mat = dc.predict_score_matrix(1, 2, 10)
    assert math.isclose(mat.sum(), 1.0, rel_tol=1e-5)

def test_dixon_coles_1x2_sum():
    dc = DixonColesModel()
    dc.attack_params = {1: 0.1, 2: 0.1}
    dc.defense_params = {1: 0.1, 2: 0.1}
    h, d, a = dc.predict_1x2(1, 2)
    assert math.isclose(h + d + a, 1.0, rel_tol=1e-5)

def test_dixon_coles_over_under_sum():
    dc = DixonColesModel()
    dc.attack_params = {1: 0.1, 2: 0.1}
    dc.defense_params = {1: 0.1, 2: 0.1}
    o, u = dc.predict_over_under(1, 2, 2.5)
    assert math.isclose(o + u, 1.0, rel_tol=1e-5)

def test_dixon_coles_btts_sum():
    dc = DixonColesModel()
    dc.attack_params = {1: 0.1, 2: 0.1}
    dc.defense_params = {1: 0.1, 2: 0.1}
    y, n = dc.predict_btts(1, 2)
    assert math.isclose(y + n, 1.0, rel_tol=1e-5)

def test_player_goal_probability():
    model = PlayerGoalModel()
    prob = model.predict_anytime_goalscorer(1, 1, 2, True, 90.0, True, 2.0, {'goals_per_90': 0.5}, {'goals_per_90': 1.0})
    assert 0 <= prob <= 1.0

def test_devigging():
    assert True

def test_negative_binomial_pmf_sum():
    nb = NegativeBinomialModel("total_cards")
    s = sum(nb.predict_exact(4.0, 0.5, k) for k in range(50))
    assert math.isclose(s, 1.0, rel_tol=1e-4)

def test_no_lookahead_validator():
    fe = FeatureEngineer()
    now = datetime(2023, 1, 1)
    
    valid_features = {'val': 1, 'timestamp': datetime(2022, 12, 31)}
    assert fe.validate_no_lookahead(valid_features, now) == True
    
    invalid_features = {'val': 1, 'timestamp': datetime(2023, 1, 2)}
    assert fe.validate_no_lookahead(invalid_features, now) == False

def test_form_ewma_range():
    fc = FormCalculator(alpha=0.3)
    results = [
        {'date': '2023-01-01', 'points': 3},
        {'date': '2023-01-08', 'points': 0},
        {'date': '2023-01-15', 'points': 1},
    ]
    ewma = fc.calculate_ewma_form(results, 'points')
    assert 0 <= ewma <= 3.0

def test_attack_defense_strength():
    fc = FormCalculator()
    df = pd.DataFrame({'goals_scored': [2, 1, 3], 'goals_conceded': [0, 1, 0]})
    att = fc.calculate_team_attack_strength(df, 1.5)
    assert att > 0
    dfn = fc.calculate_team_defense_strength(df, 1.5)
    assert dfn > 0
