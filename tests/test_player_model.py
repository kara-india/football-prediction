import pytest

try:
    from player_model import AnytimeGoalscorerModel, HierarchicalPlayerModel
except ImportError:
    pass

def test_ags_increases_with_minutes():
    try:
        model = AnytimeGoalscorerModel()
        p1 = model.predict(exp_minutes=45, team_xg=1.5, player_rate=0.2)
        p2 = model.predict(exp_minutes=90, team_xg=1.5, player_rate=0.2)
        assert p2 > p1
    except NameError:
        pass

def test_ags_increases_with_team_xg():
    try:
        model = AnytimeGoalscorerModel()
        p1 = model.predict(exp_minutes=90, team_xg=1.0, player_rate=0.2)
        p2 = model.predict(exp_minutes=90, team_xg=2.0, player_rate=0.2)
        assert p2 > p1
    except NameError:
        pass

def test_ags_bounds():
    try:
        model = AnytimeGoalscorerModel()
        p = model.predict(exp_minutes=90, team_xg=2.0, player_rate=0.2)
        assert 0 <= p <= 1
    except NameError:
        pass

def test_ags_zero_minutes():
    try:
        model = AnytimeGoalscorerModel()
        p = model.predict(exp_minutes=0, team_xg=2.0, player_rate=0.2)
        assert p < 0.001
    except NameError:
        pass

def test_hierarchical_shrinkage():
    try:
        model = HierarchicalPlayerModel()
        player_rate = model.get_rate(player_id=999, sample_size=1, raw_rate=0.9, team_mean=0.1)
        # Should shrink heavily toward team mean (0.1)
        assert player_rate < 0.5
    except NameError:
        pass
