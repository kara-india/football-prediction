"""
Reinforcement Learning & Contextual Bandit Policy Module.
"""

from typing import Any

__all__ = [
    "Action",
    "V1_ACTIONS",
    "RLState",
    "RewardCalculator",
    "MultiObjectiveRewardCalculator",
    "LinUCBAgent",
    "ThompsonSamplingAgent",
    "RLDecisionLayer",
    "CounterfactualLogger",
    "CandidateDecisionOpportunity",
    "OffPolicyEvaluator",
    "OPEResult",
    "PromotionEvaluationResult",
    "Experience",
    "ExperienceReplay",
]


def __getattr__(name: str) -> Any:
    """Lazy-load module attributes to prevent circular imports and runpy warnings."""
    if name in ("Action", "V1_ACTIONS"):
        from . import action_space
        val = getattr(action_space, name)
        globals()[name] = val
        return val
    if name == "RLState":
        from . import state_representation
        val = getattr(state_representation, name)
        globals()[name] = val
        return val
    if name in ("RewardCalculator", "MultiObjectiveRewardCalculator"):
        from . import reward
        val = getattr(reward, name)
        globals()[name] = val
        return val
    if name in ("LinUCBAgent", "ThompsonSamplingAgent", "RLDecisionLayer"):
        from . import bandit_policy
        val = getattr(bandit_policy, name)
        globals()[name] = val
        return val
    if name in ("CounterfactualLogger", "CandidateDecisionOpportunity"):
        from . import counterfactual_logger
        val = getattr(counterfactual_logger, name)
        globals()[name] = val
        return val
    if name in ("OffPolicyEvaluator", "OPEResult", "PromotionEvaluationResult"):
        from . import off_policy_evaluator
        val = getattr(off_policy_evaluator, name)
        globals()[name] = val
        return val
    if name in ("Experience", "ExperienceReplay"):
        from . import experience_replay
        val = getattr(experience_replay, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return __all__
