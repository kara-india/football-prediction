"""
Counterfactual Decision Logger for Contextual Bandit and Reinforcement Learning.
Enforces full candidate decision opportunity logging across all eligible matches
(including ABSTAIN and rejected candidates) to prevent selection bias in downstream
continual learning and offline policy evaluation (OPE).
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class CandidateDecisionOpportunity:
    """Immutable record of an individual candidate decision opportunity."""
    candidate_id: str
    fixture_id: Union[int, str]
    match_timestamp: str

    # Context state
    market: str
    competition: str
    team_form: float
    scoreline: str
    odds: float
    uncertainty: float
    starter_ratings: float
    context_vector: List[float]

    # Model probabilities & confidence
    raw_probability: float
    calibrated_probability: float
    probability_interval: Tuple[float, float]  # (lower, upper)

    # Market metrics
    decimal_odds: float
    fair_probability: float
    expected_value: float
    value_edge: float

    # Gate evaluation
    gate_action: str  # "BET" | "NO_BET"
    gate_reasons: List[str]
    data_quality_tier: str = "TIER_1"
    lineup_verified: bool = True

    # Policy action & propensity
    available_actions: List[str] = field(default_factory=lambda: ["ABSTAIN", "BET"])
    chosen_action: str = "ABSTAIN"
    action_index: int = 0
    action_propensity: float = 1.0
    action_propensities: Dict[str, float] = field(default_factory=dict)

    # Post-settlement fields
    settled: bool = False
    actual_outcome: Optional[str] = None  # "win", "loss", "void"
    realized_return: Optional[float] = None
    closing_odds: Optional[float] = None
    clv: Optional[float] = None
    counterfactual_return: Optional[float] = None
    settled_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert opportunity to dictionary."""
        d = asdict(self)
        # Ensure tuple is converted for serialization
        d["probability_interval"] = list(self.probability_interval)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateDecisionOpportunity":
        """Reconstruct opportunity from dictionary."""
        d = dict(data)
        if isinstance(d.get("probability_interval"), list):
            d["probability_interval"] = tuple(d["probability_interval"])
        return cls(**d)


class CounterfactualLogger:
    """In-memory and persistent logger for all candidate opportunities and settlements."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self._opportunities: Dict[str, CandidateDecisionOpportunity] = {}

    def log_candidate(self, opportunity: CandidateDecisionOpportunity) -> str:
        """Log a candidate opportunity in process memory.

        Persistence is handled by the durable worker repository layer. Keeping this
        method side-effect free preserves the in-memory logger as a deterministic
        test/dry-run component.
        """
        self._opportunities[opportunity.candidate_id] = opportunity
        return opportunity.candidate_id

    def record_opportunity(
        self,
        fixture_id: Union[int, str],
        match_timestamp: Union[str, datetime],
        market: str,
        competition: str,
        decimal_odds: float,
        fair_probability: float,
        expected_value: float,
        value_edge: float,
        raw_probability: float,
        calibrated_probability: float,
        probability_interval: Tuple[float, float],
        gate_action: str,
        gate_reasons: List[str],
        chosen_action: str,
        action_propensity: float,
        context_vector: Optional[Union[np.ndarray, List[float]]] = None,
        candidate_id: Optional[str] = None,
        team_form: float = 0.0,
        scoreline: str = "0-0",
        uncertainty: float = 0.05,
        starter_ratings: float = 1.0,
        data_quality_tier: str = "TIER_1",
        lineup_verified: bool = True,
        available_actions: Optional[List[str]] = None,
        action_propensities: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CandidateDecisionOpportunity:
        """Convenience method to construct, validate, and log a candidate opportunity."""
        cid = candidate_id or str(uuid.uuid4())
        ts_str = (
            match_timestamp.isoformat()
            if isinstance(match_timestamp, datetime)
            else str(match_timestamp)
        )

        actions = available_actions or ["ABSTAIN", "BET"]
        action_idx = actions.index(chosen_action) if chosen_action in actions else 0

        if context_vector is None:
            # Build default 10-dimensional feature context if none provided
            vec = [
                float(decimal_odds),
                float(fair_probability),
                float(expected_value),
                float(value_edge),
                float(calibrated_probability),
                float(probability_interval[1] - probability_interval[0]),
                float(uncertainty),
                float(team_form),
                float(starter_ratings),
                1.0 if lineup_verified else 0.0,
            ]
        elif isinstance(context_vector, np.ndarray):
            vec = context_vector.astype(float).tolist()
        else:
            vec = [float(v) for v in context_vector]

        prop_dict = action_propensities or {
            chosen_action: float(action_propensity),
            "ABSTAIN" if chosen_action == "BET" else "BET": 1.0 - float(action_propensity),
        }

        opp = CandidateDecisionOpportunity(
            candidate_id=cid,
            fixture_id=fixture_id,
            match_timestamp=ts_str,
            market=market,
            competition=competition,
            team_form=float(team_form),
            scoreline=scoreline,
            odds=float(decimal_odds),
            uncertainty=float(uncertainty),
            starter_ratings=float(starter_ratings),
            context_vector=vec,
            raw_probability=float(raw_probability),
            calibrated_probability=float(calibrated_probability),
            probability_interval=(float(probability_interval[0]), float(probability_interval[1])),
            decimal_odds=float(decimal_odds),
            fair_probability=float(fair_probability),
            expected_value=float(expected_value),
            value_edge=float(value_edge),
            gate_action=gate_action,
            gate_reasons=list(gate_reasons),
            data_quality_tier=data_quality_tier,
            lineup_verified=lineup_verified,
            available_actions=actions,
            chosen_action=chosen_action,
            action_index=action_idx,
            action_propensity=float(action_propensity),
            action_propensities=prop_dict,
            metadata=metadata or {},
        )

        self.log_candidate(opp)
        return opp

    def log_settlement(
        self,
        candidate_id: str,
        actual_outcome: str,
        closing_odds: Optional[float] = None,
        realized_return: Optional[float] = None,
        clv: Optional[float] = None,
        counterfactual_return: Optional[float] = None,
        settled_at: Optional[str] = None,
    ) -> Optional[CandidateDecisionOpportunity]:
        """Settle a logged opportunity by candidate_id.
        
        Calculates realized and counterfactual returns automatically if not explicitly provided.
        - If action was ABSTAIN: realized_return = 0.0.
          Counterfactual return (if we had bet 1 unit): (odds - 1.0) if win, -1.0 if loss, 0.0 if void.
        - If action was BET: realized_return = (odds - 1.0) if win, -1.0 if loss, 0.0 if void.
          Counterfactual return (if we had abstained): 0.0.
        """
        opp = self._opportunities.get(candidate_id)
        if opp is None:
            return None

        outcome_norm = actual_outcome.lower().strip()
        odds = opp.decimal_odds

        # Closing Line Value (CLV) calculation: (taken_odds / closing_odds) - 1.0
        calculated_clv = clv
        if calculated_clv is None and closing_odds is not None and closing_odds > 0:
            calculated_clv = (odds / closing_odds) - 1.0

        # Realized return calculation
        if realized_return is not None:
            r_return = float(realized_return)
        else:
            if opp.chosen_action == "ABSTAIN":
                r_return = 0.0
            elif opp.chosen_action == "BET":
                if outcome_norm in ("win", "won", "1"):
                    r_return = odds - 1.0
                elif outcome_norm in ("loss", "lost", "0"):
                    r_return = -1.0
                else:  # void, push
                    r_return = 0.0
            else:
                r_return = 0.0

        # Counterfactual return calculation (what would the OTHER action have yielded?)
        if counterfactual_return is not None:
            cf_return = float(counterfactual_return)
        else:
            if opp.chosen_action == "ABSTAIN":
                # Counterfactual action is BET
                if outcome_norm in ("win", "won", "1"):
                    cf_return = odds - 1.0
                elif outcome_norm in ("loss", "lost", "0"):
                    cf_return = -1.0
                else:
                    cf_return = 0.0
            else:
                # Counterfactual action is ABSTAIN
                cf_return = 0.0

        opp.settled = True
        opp.actual_outcome = outcome_norm
        opp.realized_return = r_return
        opp.closing_odds = closing_odds
        opp.clv = calculated_clv
        opp.counterfactual_return = cf_return
        opp.settled_at = settled_at or datetime.now(timezone.utc).isoformat()

        return opp

    def get_candidate(self, candidate_id: str) -> Optional[CandidateDecisionOpportunity]:
        """Retrieve candidate opportunity by candidate_id."""
        return self._opportunities.get(candidate_id)

    def get_all_candidates(self) -> List[CandidateDecisionOpportunity]:
        """Retrieve all recorded candidate opportunities."""
        return list(self._opportunities.values())

    def get_settled_candidates(self) -> List[CandidateDecisionOpportunity]:
        """Retrieve all settled candidate opportunities."""
        return [o for o in self._opportunities.values() if o.settled]

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serialize all opportunities to a list of dicts."""
        return [opp.to_dict() for opp in self._opportunities.values()]

    def to_json(self, filepath: Optional[str] = None, indent: int = 2) -> str:
        """Serialize opportunities to JSON string and optionally save to file."""
        data = self.to_dict()
        json_str = json.dumps(data, indent=indent)
        target = filepath or self.storage_path
        if target:
            with open(target, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str

    @classmethod
    def from_json(cls, json_str_or_filepath: str) -> "CounterfactualLogger":
        """Load logger from JSON string or file path."""
        try:
            with open(json_str_or_filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger = cls(storage_path=json_str_or_filepath)
        except (OSError, ValueError):
            data = json.loads(json_str_or_filepath)
            logger = cls()

        for item in data:
            opp = CandidateDecisionOpportunity.from_dict(item)
            logger.log_candidate(opp)

        return logger

    def to_dataframe(self) -> pd.DataFrame:
        """Export all logged opportunities to a pandas DataFrame."""
        records = []
        for opp in self._opportunities.values():
            rec = {
                "candidate_id": opp.candidate_id,
                "fixture_id": opp.fixture_id,
                "match_timestamp": opp.match_timestamp,
                "market": opp.market,
                "competition": opp.competition,
                "team_form": opp.team_form,
                "scoreline": opp.scoreline,
                "odds": opp.odds,
                "uncertainty": opp.uncertainty,
                "starter_ratings": opp.starter_ratings,
                "raw_probability": opp.raw_probability,
                "calibrated_probability": opp.calibrated_probability,
                "ci_lower": opp.probability_interval[0],
                "ci_upper": opp.probability_interval[1],
                "ci_width": opp.probability_interval[1] - opp.probability_interval[0],
                "decimal_odds": opp.decimal_odds,
                "fair_probability": opp.fair_probability,
                "expected_value": opp.expected_value,
                "value_edge": opp.value_edge,
                "gate_action": opp.gate_action,
                "gate_reasons": ",".join(opp.gate_reasons),
                "data_quality_tier": opp.data_quality_tier,
                "lineup_verified": opp.lineup_verified,
                "chosen_action": opp.chosen_action,
                "action_index": opp.action_index,
                "action_propensity": opp.action_propensity,
                "settled": opp.settled,
                "actual_outcome": opp.actual_outcome,
                "realized_return": opp.realized_return,
                "closing_odds": opp.closing_odds,
                "clv": opp.clv,
                "counterfactual_return": opp.counterfactual_return,
                "settled_at": opp.settled_at,
            }
            # Expand context vector elements as feature_0, feature_1, etc.
            for i, val in enumerate(opp.context_vector):
                rec[f"feature_{i}"] = val

            records.append(rec)

        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)

    def clear(self) -> None:
        """Clear all logged opportunities."""
        self._opportunities.clear()

    def __len__(self) -> int:
        return len(self._opportunities)

    def __iter__(self):
        return iter(self._opportunities.values())
