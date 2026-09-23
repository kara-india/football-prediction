import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


@dataclass
class MultiDimensionalForm:
    """Multi-channel dynamic team performance metrics."""
    attacking_form: float
    defensive_form: float
    territorial_form: float
    disciplinary_form: float
    composite_index: float
    matches_counted: int
    half_life_matches: float


class FormCalculator:
    """
    Multi-dimensional dynamic form calculator replacing single-fixed-alpha EWMA.
    Separates performance into distinct analytical dimensions:
    - Attacking: goals scored, shots on target, xG created
    - Defensive: goals conceded, shots on target conceded, xG conceded
    - Territorial / Set-piece: corners won vs conceded
    - Disciplinary: yellow/red cards, fouls committed
    """

    DEFAULT_HALF_LIFE_MATCHES: float = 5.0
    DEFAULT_HALF_LIFE_DAYS: float = 35.0

    def __init__(self, alpha: Optional[float] = None, half_life_matches: float = 5.0):
        self.half_life_matches = half_life_matches
        if alpha is not None:
            self.alpha = float(alpha)
        else:
            # alpha corresponding to half_life_matches: (1 - alpha)^half_life = 0.5 => alpha = 1 - 0.5^(1/half_life)
            self.alpha = 1.0 - math.pow(0.5, 1.0 / max(half_life_matches, 1e-4))

    def calculate_ewma_form(
        self,
        results: List[Dict[str, Any]],
        metric: str,
        half_life_matches: Optional[float] = None,
    ) -> float:
        """
        Calculate EWMA form for a single metric with configurable half-life decay.
        Maintains backwards compatibility with results list containing 'date' and metric key.
        """
        if not results:
            return 0.0

        alpha = (
            1.0 - math.pow(0.5, 1.0 / max(half_life_matches, 1e-4))
            if half_life_matches is not None
            else self.alpha
        )

        # Sort descending by date
        sorted_results = sorted(
            results,
            key=lambda x: str(x.get("date", "")),
            reverse=True,
        )

        ewma = 0.0
        weight_sum = 0.0
        current_weight = 1.0

        for r in sorted_results:
            val = float(r.get(metric, 0.0))
            mult = float(r.get("weight", 1.0))
            w = current_weight * mult
            ewma += val * w
            weight_sum += w
            current_weight *= (1.0 - alpha)

        return float(ewma / max(weight_sum, 1e-9))

    def calculate_time_decay_form(
        self,
        results: List[Dict[str, Any]],
        metric: str,
        reference_date: Optional[Union[date, datetime]] = None,
        half_life_days: float = 35.0,
    ) -> float:
        """Compute calendar-time exponential decay form w = 2^(-delta_days / half_life_days)."""
        if not results:
            return 0.0

        if reference_date is None:
            max_dt = max(
                pd.to_datetime(r["date"]) for r in results if r.get("date") is not None
            )
            reference_date = max_dt

        ref_ts = pd.to_datetime(reference_date).timestamp()
        ewma = 0.0
        weight_sum = 0.0

        for r in results:
            if not r.get("date"):
                continue
            r_ts = pd.to_datetime(r["date"]).timestamp()
            delta_days = max(0.0, (ref_ts - r_ts) / 86400.0)
            weight = math.pow(0.5, delta_days / max(half_life_days, 1e-4))
            val = float(r.get(metric, 0.0))
            ewma += val * weight
            weight_sum += weight

        return float(ewma / max(weight_sum, 1e-9))

    def calculate_multidimensional_form(
        self,
        results: List[Dict[str, Any]],
        half_life_matches: Optional[float] = None,
    ) -> MultiDimensionalForm:
        """
        Compute multi-dimensional performance decomposition across 4 channels.
        Higher is better for attacking/territorial; lower is better for defensive/disciplinary.
        """
        hl = half_life_matches or self.half_life_matches

        # 1. Attacking form: combination of goals_scored (60%) and shots_on_target (40%)
        goals_scored_form = self.calculate_ewma_form(results, "goals_scored", hl)
        sot_form = self.calculate_ewma_form(results, "shots_on_target", hl)
        attacking_form = (
            goals_scored_form * 0.6 + (sot_form / 4.5) * 0.4
            if sot_form > 0
            else goals_scored_form
        )

        # 2. Defensive form: combination of goals_conceded (60%) and shots_on_target_conceded (40%)
        goals_conceded_form = self.calculate_ewma_form(results, "goals_conceded", hl)
        sot_conceded_form = self.calculate_ewma_form(results, "shots_on_target_conceded", hl)
        defensive_form = (
            goals_conceded_form * 0.6 + (sot_conceded_form / 4.5) * 0.4
            if sot_conceded_form > 0
            else goals_conceded_form
        )

        # 3. Territorial / Set-piece form: net corners ratio
        corners_won = self.calculate_ewma_form(results, "corners_won", hl)
        corners_conceded = self.calculate_ewma_form(results, "corners_conceded", hl)
        total_corners = corners_won + corners_conceded
        territorial_form = (
            corners_won / total_corners if total_corners > 0 else 0.50
        )

        # 4. Disciplinary form: cards and fouls (lower is cleaner)
        yellow_cards = self.calculate_ewma_form(results, "yellow_cards", hl)
        red_cards = self.calculate_ewma_form(results, "red_cards", hl)
        fouls = self.calculate_ewma_form(results, "fouls", hl)
        disciplinary_form = yellow_cards * 1.0 + red_cards * 3.0 + (fouls / 10.0) * 0.5

        # 5. Composite index: attack + territorial - defense (scaled around 1.0)
        composite_index = max(
            0.0,
            1.0 + (attacking_form - defensive_form) * 0.35 + (territorial_form - 0.50) * 0.30,
        )

        return MultiDimensionalForm(
            attacking_form=float(round(attacking_form, 4)),
            defensive_form=float(round(defensive_form, 4)),
            territorial_form=float(round(territorial_form, 4)),
            disciplinary_form=float(round(disciplinary_form, 4)),
            composite_index=float(round(composite_index, 4)),
            matches_counted=len(results),
            half_life_matches=hl,
        )

    def calculate_team_attack_strength(
        self, team_matches: pd.DataFrame, league_avg_goals: float
    ) -> float:
        """Ratio of team average goals scored to league average."""
        if len(team_matches) == 0:
            return 1.0
        avg = float(team_matches["goals_scored"].mean())
        return float(avg / max(league_avg_goals, 1e-9))

    def calculate_team_defense_strength(
        self, team_matches: pd.DataFrame, league_avg_goals: float
    ) -> float:
        """Ratio of team average goals conceded to league average (lower is stronger)."""
        if len(team_matches) == 0:
            return 1.0
        avg = float(team_matches["goals_conceded"].mean())
        return float(avg / max(league_avg_goals, 1e-9))

    def get_rest_days(
        self,
        last_match_date: Union[date, datetime, str],
        current_date: Union[date, datetime, str],
    ) -> int:
        """Calculate calendar rest days between matches."""
        dt1 = pd.to_datetime(last_match_date).date()
        dt2 = pd.to_datetime(current_date).date()
        return max(0, (dt2 - dt1).days)
