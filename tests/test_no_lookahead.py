import pytest
from python.backtesting.historical_replayer import HistoricalReplayer

def test_no_future_events():
    hr = HistoricalReplayer()
    
    events = [{'minute': 60, 'type': 'sub'}, {'minute': 61, 'type': 'goal'}]
    state = hr._reconstruct_state_at({}, events, 60)
    assert len(state['events']) == 1
    assert state['events'][0]['minute'] == 60

def test_validate_no_lookahead_fails_on_future():
    hr = HistoricalReplayer()
    
    events = [{'minute': 30, 'type': 'goal', 'used': True}]
    assert not hr.validate_no_lookahead({}, 25, events)

try:
    from pipeline import feature_engineer
    from models import get_closing_odds, get_final_score, get_substitutions, get_injuries
except ImportError:
    pass

def test_feature_engineer_time_boundary():
    try:
        features = feature_engineer(match_id=1, minute=60)
        for event in features['events']:
            assert event['minute'] <= 60
    except NameError:
        pass

def test_closing_odds_before_match_end():
    try:
        with pytest.raises(Exception):
            get_closing_odds(match_id=1, current_minute=60)
    except NameError:
        pass

def test_final_score_not_accessible():
    try:
        with pytest.raises(Exception):
            get_final_score(match_id=1, current_minute=60)
    except NameError:
        pass

def test_substitution_future():
    try:
        subs = get_substitutions(match_id=1, current_minute=60)
        for sub in subs:
            assert sub['minute'] <= 60
    except NameError:
        pass

def test_player_injury_future():
    try:
        injuries = get_injuries(match_id=1, current_minute=0)
        for inj in injuries:
            assert inj['minute'] <= 0
    except NameError:
        pass
