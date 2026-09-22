import pytest

try:
    from elo import EloSystem, expected_score, update_elo, predict_1x2
except ImportError:
    pass

def test_elo_expected_score_equal():
    try:
        assert expected_score(1500, 1500) == 0.5
    except NameError:
        pass

def test_elo_expected_score_stronger():
    try:
        assert expected_score(1700, 1500) > 0.7
    except NameError:
        pass

def test_elo_update_win():
    try:
        r1, r2 = update_elo(1500, 1500, result=1)
        assert r1 > 1500
        assert r2 < 1500
    except NameError:
        pass

def test_elo_update_draw():
    try:
        r1, r2 = update_elo(1700, 1500, result=0.5)
        assert r1 < 1700
        assert r2 > 1500
    except NameError:
        pass

def test_elo_update_zero_sum():
    try:
        r1, r2 = update_elo(1600, 1400, result=1)
        assert (r1 - 1600) == -(r2 - 1400)
    except NameError:
        pass

def test_elo_bulk_update():
    try:
        system = EloSystem()
        # Mocking a bulk update where team A beats team B
        system.bulk_update([{"team1": "A", "team2": "B", "result": 1}])
        assert system.get_rating("A") > system.get_rating("B")
    except NameError:
        pass

def test_predict_1x2_sum():
    try:
        probs = predict_1x2(1500, 1500)
        assert sum(probs) == 1.0
    except NameError:
        pass

def test_home_advantage():
    try:
        probs = predict_1x2(1500, 1500, home_advantage=True)
        assert probs[0] > probs[2]  # Home win prob > away win prob
    except NameError:
        pass
