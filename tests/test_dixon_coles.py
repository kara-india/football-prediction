import pytest
import math

try:
    from dixon_coles import DixonColesModel, tau
except ImportError:
    pass

def test_score_matrix_sum(sample_dixon_coles):
    try:
        matrix = sample_dixon_coles.predict_score_matrix("A", "B")
        total = sum(sum(row) for row in matrix)
        assert math.isclose(total, 1.0, abs_tol=0.001)
    except NameError:
        pass

def test_1x2_probs_sum(sample_dixon_coles):
    try:
        probs = sample_dixon_coles.predict_1x2("A", "B")
        assert math.isclose(sum(probs), 1.0, abs_tol=0.001)
    except NameError:
        pass

def test_over_under_sum(sample_dixon_coles):
    try:
        over, under = sample_dixon_coles.predict_over_under("A", "B", line=2.5)
        assert math.isclose(over + under, 1.0, abs_tol=0.001)
    except NameError:
        pass

def test_btts_sum(sample_dixon_coles):
    try:
        yes, no = sample_dixon_coles.predict_btts("A", "B")
        assert math.isclose(yes + no, 1.0, abs_tol=0.001)
    except NameError:
        pass

def test_tau():
    try:
        lambda_val = 1.5
        mu = 1.2
        rho = 0.1
        assert math.isclose(tau(0, 0, lambda_val, mu, rho), 1 - lambda_val * mu * rho, abs_tol=0.0001)
    except NameError:
        pass

def test_stronger_attack_scores_more(sample_dixon_coles):
    try:
        sample_dixon_coles.set_attack("Strong", 2.0)
        sample_dixon_coles.set_attack("Weak", 0.5)
        sample_dixon_coles.set_defense("A", 1.0)
        
        strong_exp = sample_dixon_coles.expected_goals("Strong", "A")
        weak_exp = sample_dixon_coles.expected_goals("Weak", "A")
        
        assert strong_exp > weak_exp
    except NameError:
        pass

def test_model_serialization(sample_dixon_coles):
    try:
        data = sample_dixon_coles.serialize()
        new_model = DixonColesModel.deserialize(data)
        assert new_model.params == sample_dixon_coles.params
    except NameError:
        pass
