"""
Tests for Market Settlement Engines
Covers legacy SettlementCalculator as well as Phase 7 Canonical SettlementEngine
resolving TOTAL_GOALS_2_5, MATCH_1X2, BTTS, DOUBLE_CHANCE, PnL, closing odds, and CLV.
"""
import pytest
from datetime import datetime, timezone

from python.calibration.settlement import SettlementCalculator
from python.engine.settlement import SettlementEngine
from python.data_contracts import CanonicalSettlement


# ==========================================
# Legacy SettlementCalculator Unit Tests
# ==========================================

def test_settle_1x2_legacy():
    calc = SettlementCalculator()
    assert calc.settle_1x2(2, 1, '1') == 'win'
    assert calc.settle_1x2(2, 1, 'X') == 'loss'
    assert calc.settle_1x2(2, 1, '2') == 'loss'
    assert calc.settle_1x2(1, 1, 'X') == 'win'
    assert calc.settle_1x2(1, 1, '1') == 'loss'
    assert calc.settle_1x2(0, 2, '2') == 'win'


def test_settle_over_under_legacy():
    calc = SettlementCalculator()
    # .5 line
    assert calc.settle_over_under(3, 2.5, 'over') == 'win'
    assert calc.settle_over_under(2, 2.5, 'over') == 'loss'
    assert calc.settle_over_under(2, 2.5, 'under') == 'win'
    # whole number line
    assert calc.settle_over_under(2, 2.0, 'over') == 'void'
    assert calc.settle_over_under(2, 2.0, 'under') == 'void'
    assert calc.settle_over_under(3, 2.0, 'over') == 'win'


def test_settle_btts_legacy():
    calc = SettlementCalculator()
    assert calc.settle_btts(1, 1, 'yes') == 'win'
    assert calc.settle_btts(2, 0, 'yes') == 'loss'
    assert calc.settle_btts(2, 0, 'no') == 'win'
    assert calc.settle_btts(0, 0, 'no') == 'win'


def test_calculate_paper_pl_legacy():
    calc = SettlementCalculator()
    assert calc.calculate_paper_pl('win', 2.5, 10.0) == 15.0
    assert calc.calculate_paper_pl('loss', 2.5, 10.0) == -10.0
    assert calc.calculate_paper_pl('void', 2.5, 10.0) == 0.0


# ==========================================
# Phase 7 Canonical SettlementEngine Tests
# ==========================================

class TestSettlementEngine:
    """Rigorous tests for canonical SettlementEngine."""

    def test_settle_total_goals_2_5(self):
        # Home 2, Away 1 -> Total 3 > 2.5
        won_settle = SettlementEngine.settle(
            prediction_id="pred-1",
            match_id="m-1",
            market="TOTAL_GOALS_2_5",
            selection="OVER",
            odds_at_prediction=1.95,
            actual_home_goals=2,
            actual_away_goals=1,
        )
        assert won_settle.actual_outcome == "WON"
        assert won_settle.outcome == "WON"
        assert pytest.approx(won_settle.profit_loss) == 0.95

        # Home 1, Away 1 -> Total 2 < 2.5
        lost_settle = SettlementEngine.settle(
            prediction_id="pred-2",
            match_id="m-2",
            market="TOTAL_GOALS_2_5",
            selection="OVER",
            odds_at_prediction=1.95,
            actual_home_goals=1,
            actual_away_goals=1,
        )
        assert lost_settle.actual_outcome == "LOST"
        assert lost_settle.profit_loss == -1.0

        # Under 2.5 on 1-1 score -> WON
        under_settle = SettlementEngine.settle(
            prediction_id="pred-3",
            match_id="m-2",
            market="TOTAL_GOALS_2_5",
            selection="UNDER",
            odds_at_prediction=1.85,
            actual_home_goals=1,
            actual_away_goals=1,
        )
        assert under_settle.actual_outcome == "WON"
        assert pytest.approx(under_settle.profit_loss) == 0.85

    def test_settle_match_1x2(self):
        # 1: Home Win
        s1 = SettlementEngine.settle("p-1", "m-1", "MATCH_1X2", "1", 2.10, 2, 1)
        assert s1.actual_outcome == "WON"
        assert pytest.approx(s1.profit_loss) == 1.10

        s2 = SettlementEngine.settle("p-2", "m-1", "MATCH_1X2", "X", 3.20, 2, 1)
        assert s2.actual_outcome == "LOST"
        assert s2.profit_loss == -1.0

        s3 = SettlementEngine.settle("p-3", "m-1", "MATCH_1X2", "2", 3.50, 2, 1)
        assert s3.actual_outcome == "LOST"

        # Draw
        s_draw = SettlementEngine.settle("p-4", "m-2", "MATCH_1X2", "X", 3.20, 0, 0)
        assert s_draw.actual_outcome == "WON"

        # Away Win
        s_away = SettlementEngine.settle("p-5", "m-3", "MATCH_1X2", "2", 2.80, 0, 1)
        assert s_away.actual_outcome == "WON"

    def test_settle_btts(self):
        # 2-1: Both scored -> YES wins, NO loses
        btts_yes = SettlementEngine.settle("p-b1", "m-1", "BTTS", "YES", 1.80, 2, 1)
        assert btts_yes.actual_outcome == "WON"

        btts_no = SettlementEngine.settle("p-b2", "m-1", "BTTS", "NO", 2.05, 2, 1)
        assert btts_no.actual_outcome == "LOST"

        # 3-0: Away did not score -> YES loses, NO wins
        btts_clean = SettlementEngine.settle("p-b3", "m-2", "BTTS", "NO", 2.05, 3, 0)
        assert btts_clean.actual_outcome == "WON"

    def test_settle_double_chance(self):
        # 1X: Wins on Home (2-1) and Draw (1-1), Loses on Away (0-1)
        dc_1x_win1 = SettlementEngine.settle("p-dc1", "m-1", "DOUBLE_CHANCE", "1X", 1.35, 2, 1)
        assert dc_1x_win1.actual_outcome == "WON"

        dc_1x_win2 = SettlementEngine.settle("p-dc2", "m-2", "DOUBLE_CHANCE", "1X", 1.35, 1, 1)
        assert dc_1x_win2.actual_outcome == "WON"

        dc_1x_loss = SettlementEngine.settle("p-dc3", "m-3", "DOUBLE_CHANCE", "1X", 1.35, 0, 1)
        assert dc_1x_loss.actual_outcome == "LOST"

        # 12: Wins on Home and Away, Loses on Draw
        dc_12_loss = SettlementEngine.settle("p-dc4", "m-2", "DOUBLE_CHANCE", "12", 1.30, 1, 1)
        assert dc_12_loss.actual_outcome == "LOST"

        # X2: Wins on Draw and Away, Loses on Home
        dc_x2_win = SettlementEngine.settle("p-dc5", "m-3", "DOUBLE_CHANCE", "X2", 1.50, 0, 1)
        assert dc_x2_win.actual_outcome == "WON"

    def test_closing_line_value_clv(self):
        # Prediction odds: 2.20, Closing odds: 2.00 -> CLV = (2.20 / 2.00) - 1.0 = +0.10 (+10%)
        settle_beat_close = SettlementEngine.settle(
            prediction_id="p-clv1",
            match_id="m-1",
            market="MATCH_1X2",
            selection="1",
            odds_at_prediction=2.20,
            actual_home_goals=2,
            actual_away_goals=0,
            closing_odds=2.00,
        )
        assert pytest.approx(settle_beat_close.clv, abs=1e-5) == 0.10

        # Prediction odds: 1.90, Closing odds: 2.00 -> CLV = (1.90 / 2.00) - 1.0 = -0.05 (-5%)
        settle_lost_close = SettlementEngine.settle(
            prediction_id="p-clv2",
            match_id="m-1",
            market="MATCH_1X2",
            selection="1",
            odds_at_prediction=1.90,
            actual_home_goals=2,
            actual_away_goals=0,
            closing_odds=2.00,
        )
        assert pytest.approx(settle_lost_close.clv, abs=1e-5) == -0.05

    def test_records_observed_match_outcomes(self):
        settle = SettlementEngine.settle(
            prediction_id="p-obs",
            match_id="m-obs",
            market="TOTAL_GOALS_2_5",
            selection="OVER",
            odds_at_prediction=1.90,
            actual_home_goals=3,
            actual_away_goals=2,
            actual_cards=5,
            actual_corners=11,
            calibrated_prob=0.60,
        )

        assert isinstance(settle, CanonicalSettlement)
        assert settle.actual_home_goals == 3
        assert settle.actual_away_goals == 2
        assert settle.actual_cards == 5
        assert settle.actual_corners == 11
        assert settle.actual_score_home == 3
        assert settle.actual_score_away == 2
        # Brier contribution: outcome is WON (1), p = 0.60 -> (0.60 - 1.0)^2 = 0.16
        assert pytest.approx(settle.brier_score_contribution, abs=1e-5) == 0.16

    def test_whole_number_line_push(self):
        settle_push = SettlementEngine.settle(
            prediction_id="p-push",
            match_id="m-push",
            market="TOTAL_GOALS",
            selection="OVER",
            line=2.0,
            odds_at_prediction=1.90,
            actual_home_goals=1,
            actual_away_goals=1,
        )
        assert settle_push.actual_outcome == "PUSH"
        assert settle_push.profit_loss == 0.0
