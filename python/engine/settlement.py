"""
Market Settlement Engine
Authoritative settlement and reconciliation layer resolving prediction wagers
against verified official match scores and performance metrics.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from python.data_contracts import CanonicalSettlement


class SettlementEngine:
    """Canonical Market Settlement Engine resolving wagers against official results."""

    FLAT_PAPER_STAKE: float = 1.0

    @classmethod
    def settle_total_goals(
        cls,
        home_goals: int,
        away_goals: int,
        selection: str,
        line: float = 2.5,
    ) -> str:
        """Settle Over/Under Total Goals markets.

        - For line 2.5: WON if home + away > 2.5, else LOST.
        - For whole number lines (e.g. 2.0, 3.0): PUSH if total == line.
        """
        total = home_goals + away_goals
        sel = selection.upper().strip()

        if total == line:
            return "PUSH"

        is_over = total > line
        if sel in ("OVER", "OVER_2_5", ">2.5", "YES", "TOTAL_GOALS_2_5", ">"):
            return "WON" if is_over else "LOST"
        elif sel in ("UNDER", "UNDER_2_5", "<2.5", "NO", "<"):
            return "WON" if not is_over else "LOST"
        # Default assumption if unspecified: selection corresponds to line direction
        return "WON" if is_over else "LOST"

    @classmethod
    def settle_1x2(cls, home_goals: int, away_goals: int, selection: str) -> str:
        """Settle Match 1X2 market.

        - '1': Home win
        - 'X': Draw
        - '2': Away win
        """
        if home_goals > away_goals:
            actual = "1"
        elif home_goals == away_goals:
            actual = "X"
        else:
            actual = "2"

        sel = selection.upper().strip()
        if sel in ("1", "HOME"):
            norm_sel = "1"
        elif sel in ("X", "DRAW"):
            norm_sel = "X"
        elif sel in ("2", "AWAY"):
            norm_sel = "2"
        else:
            norm_sel = sel

        return "WON" if norm_sel == actual else "LOST"

    @classmethod
    def settle_btts(cls, home_goals: int, away_goals: int, selection: str) -> str:
        """Settle Both Teams To Score (BTTS) market.

        - 'YES': WON if home > 0 and away > 0, else LOST
        - 'NO': WON if home == 0 or away == 0, else LOST
        """
        btts_actual = (home_goals > 0) and (away_goals > 0)
        sel = selection.upper().strip()

        if sel in ("YES", "Y", "BTTS_YES"):
            return "WON" if btts_actual else "LOST"
        elif sel in ("NO", "N", "BTTS_NO"):
            return "WON" if not btts_actual else "LOST"
        return "LOST"

    @classmethod
    def settle_double_chance(cls, home_goals: int, away_goals: int, selection: str) -> str:
        """Settle Double Chance market ('1X', '12', 'X2')."""
        if home_goals > away_goals:
            actual = "1"
        elif home_goals == away_goals:
            actual = "X"
        else:
            actual = "2"

        sel = selection.upper().replace("/", "").replace(" ", "").strip()
        if sel == "1X":
            return "WON" if actual in ("1", "X") else "LOST"
        elif sel == "12":
            return "WON" if actual in ("1", "2") else "LOST"
        elif sel == "X2":
            return "WON" if actual in ("X", "2") else "LOST"
        return "LOST"

    @classmethod
    def settle_cards(cls, total_cards: int, selection: str, line: float) -> str:
        """Settle Total Cards market."""
        if total_cards == line:
            return "PUSH"
        sel = selection.upper().strip()
        is_over = total_cards > line
        if sel in ("OVER", ">"):
            return "WON" if is_over else "LOST"
        elif sel in ("UNDER", "<"):
            return "WON" if not is_over else "LOST"
        return "WON" if is_over else "LOST"

    @classmethod
    def settle_corners(cls, total_corners: int, selection: str, line: float) -> str:
        """Settle Total Corners market."""
        if total_corners == line:
            return "PUSH"
        sel = selection.upper().strip()
        is_over = total_corners > line
        if sel in ("OVER", ">"):
            return "WON" if is_over else "LOST"
        elif sel in ("UNDER", "<"):
            return "WON" if not is_over else "LOST"
        return "WON" if is_over else "LOST"

    @classmethod
    def settle(
        cls,
        prediction_id: str,
        match_id: str,
        market: str,
        selection: str,
        odds_at_prediction: float,
        actual_home_goals: int,
        actual_away_goals: int,
        actual_cards: Optional[int] = None,
        actual_corners: Optional[int] = None,
        line: Optional[float] = None,
        closing_odds: Optional[float] = None,
        calibrated_prob: Optional[float] = None,
        settled_at: Optional[datetime] = None,
        error_classification: Optional[str] = None,
    ) -> CanonicalSettlement:
        """Settle a candidate prediction against verified match results.

        Args:
            prediction_id: Canonical prediction UUID.
            match_id: Match UUID.
            market: 'TOTAL_GOALS_2_5', 'TOTAL_GOALS', 'MATCH_1X2', 'BTTS', 'DOUBLE_CHANCE', etc.
            selection: Market selection string.
            odds_at_prediction: Decimal odds at time of bet placement.
            actual_home_goals: Official home goals scored.
            actual_away_goals: Official away goals scored.
            actual_cards: Optional official card count.
            actual_corners: Optional official corner count.
            line: Line parameter (default 2.5 for goal totals).
            closing_odds: Closing 1xBet odds for CLV calculation.
            calibrated_prob: Calibrated model win probability.
            settled_at: Settlement timestamp (defaults to UTC now).
            error_classification: Error taxonomy category if applicable.

        Returns:
            CanonicalSettlement dataclass instance.
        """
        market_upper = market.upper().strip()

        # Determine outcome
        if market_upper in ("TOTAL_GOALS_2_5", "OVER_UNDER_2_5"):
            outcome = cls.settle_total_goals(actual_home_goals, actual_away_goals, selection, line=2.5)
            resolved_line = 2.5
        elif market_upper in ("TOTAL_GOALS", "OVER_UNDER"):
            eff_line = line if line is not None else 2.5
            outcome = cls.settle_total_goals(actual_home_goals, actual_away_goals, selection, line=eff_line)
            resolved_line = eff_line
        elif market_upper in ("MATCH_1X2", "1X2", "MATCH_RESULT"):
            outcome = cls.settle_1x2(actual_home_goals, actual_away_goals, selection)
            resolved_line = None
        elif market_upper in ("BTTS", "BOTH_TEAMS_TO_SCORE"):
            outcome = cls.settle_btts(actual_home_goals, actual_away_goals, selection)
            resolved_line = None
        elif market_upper in ("DOUBLE_CHANCE", "DC"):
            outcome = cls.settle_double_chance(actual_home_goals, actual_away_goals, selection)
            resolved_line = None
        elif market_upper in ("TOTAL_CARDS", "CARDS") and actual_cards is not None:
            eff_line = line if line is not None else 3.5
            outcome = cls.settle_cards(actual_cards, selection, line=eff_line)
            resolved_line = eff_line
        elif market_upper in ("TOTAL_CORNERS", "CORNERS") and actual_corners is not None:
            eff_line = line if line is not None else 9.5
            outcome = cls.settle_corners(actual_corners, selection, line=eff_line)
            resolved_line = eff_line
        else:
            # Fallback
            outcome = "LOST"
            resolved_line = line

        # Calculate profit / loss on 1.0 flat unit stake
        if outcome == "WON":
            profit_loss = round((odds_at_prediction - 1.0) * cls.FLAT_PAPER_STAKE, 4)
        elif outcome == "LOST":
            profit_loss = -cls.FLAT_PAPER_STAKE
        else:  # PUSH or VOID
            profit_loss = 0.0

        # Calculate Closing Line Value (CLV)
        # clv = (odds_bet / closing_odds) - 1.0
        if closing_odds is not None and closing_odds > 0.0:
            clv = round((odds_at_prediction / closing_odds) - 1.0, 6)
        else:
            clv = None

        # Calculate Brier score contribution: (p - y)^2
        brier_contrib = None
        if calibrated_prob is not None:
            if outcome == "WON":
                brier_contrib = round((calibrated_prob - 1.0) ** 2, 6)
            elif outcome == "LOST":
                brier_contrib = round((calibrated_prob - 0.0) ** 2, 6)
            else:
                brier_contrib = 0.0

        return CanonicalSettlement(
            prediction_id=prediction_id,
            match_id=match_id,
            market=market,
            selection=selection,
            line=resolved_line,
            odds_at_prediction=odds_at_prediction,
            actual_outcome=outcome,
            profit_loss=profit_loss,
            settled_at=settled_at or datetime.now(timezone.utc),
            closing_odds=closing_odds,
            clv=clv,
            actual_home_goals=actual_home_goals,
            actual_away_goals=actual_away_goals,
            actual_cards=actual_cards,
            actual_corners=actual_corners,
            brier_score_contribution=brier_contrib,
            error_classification=error_classification,
        )
