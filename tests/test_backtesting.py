import pytest
from datetime import date
import pandas as pd
from python.backtesting.historical_replayer import HistoricalReplayer
from python.backtesting.walk_forward import WalkForwardValidator
from python.backtesting.clv_tracker import CLVTracker
from python.learning.evaluator import PredictionEvaluator

def test_reconstruct_state_at():
    hr = HistoricalReplayer()
    events = [{'minute': 65, 'type': 'goal'}, {'minute': 70, 'type': 'goal'}]
    
    state_65 = hr._reconstruct_state_at({}, events, 65)
    assert len(state_65['events']) == 1
    assert state_65['events'][0]['minute'] == 65
    
    state_70 = hr._reconstruct_state_at({}, events, 70)
    assert len(state_70['events']) == 2

def test_validate_no_lookahead():
    hr = HistoricalReplayer()
    assert hr.validate_no_lookahead({}, 65, [{'minute': 70, 'used': True}]) == False

def test_walk_forward_folds():
    wf = WalkForwardValidator(initial_train_months=12, validation_months=1, step_months=1)
    start_date = date(2020, 1, 1)
    end_date = date(2021, 3, 1)
    folds = wf.generate_folds(pd.DataFrame(), start_date, end_date)
    assert len(folds) == 2
    assert folds[0]['val_start'] >= folds[0]['train_end']
    assert folds[0]['val_start'] == date(2021, 1, 1)
    assert folds[0]['val_end'] == date(2021, 2, 1)

def test_clv_computation():
    tracker = CLVTracker()
    clv = tracker.compute_clv(2.0, 1.8)
    assert clv > 0

def test_error_classification():
    evaluator = PredictionEvaluator()
    assert evaluator.classify_error({'calibrated_prob': 0.9, 'prediction': 1}, {'outcome': 0}, {}) == 'MODEL_OVERCONFIDENCE'
    assert evaluator.classify_error({'calibrated_prob': 0.5, 'prediction': 1}, {'outcome': 0, 'red_card_after_prediction': True}, {}) == 'RED_CARD_EFFECT'

def test_calculate_roi():
    evaluator = PredictionEvaluator()
    paper_bets = [{'stake': 100, 'pnl': 20}, {'stake': 100, 'pnl': -100}]
    assert evaluator.calculate_roi(paper_bets) == -80 / 200
