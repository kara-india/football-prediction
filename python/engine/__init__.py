"""
Prediction Engine Package
Competition gating, runtime lineup validation, analytical edge calculation,
authoritative 10-point NO-BET gate, market settlement, and error evaluation.
"""
from .competition_gate import CompetitionGatekeeper
from .edge_calculator import EdgeCalculator, CandidateSelection
from .nobet_gate import NoBetGate, NoBetGateResult
from .settlement import SettlementEngine
from .error_evaluator import ErrorEvaluator, ErrorCategory, CanonicalForecastError

__all__ = [
    "CompetitionGatekeeper",
    "EdgeCalculator",
    "CandidateSelection",
    "NoBetGate",
    "NoBetGateResult",
    "SettlementEngine",
    "ErrorEvaluator",
    "ErrorCategory",
    "CanonicalForecastError",
]
