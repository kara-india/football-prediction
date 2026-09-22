import numpy as np
from typing import Dict
from .action_space import Action, V1_ACTIONS
from .state_representation import RLState
from .reward import RewardCalculator

class LinUCBAgent:
    # Linear Upper Confidence Bound bandit
    # Suitable for V1 with limited data
    # NOT a deep RL agent - too much data required for that
    
    def __init__(self, n_actions: int = 2, n_features: int = 20, alpha: float = 1.0):
        # alpha: exploration parameter
        self.n_actions = n_actions
        self.n_features = n_features
        self.alpha = alpha
        self.A = {a: np.eye(n_features) for a in range(n_actions)}  # covariance
        self.b = {a: np.zeros(n_features) for a in range(n_actions)}  # reward
    
    def select_action(self, context: np.ndarray) -> int:
        # UCB action selection
        p_t = np.zeros(self.n_actions)
        for a in range(self.n_actions):
            A_inv = np.linalg.inv(self.A[a])
            theta_a = A_inv @ self.b[a]
            p_t[a] = theta_a.T @ context + self.alpha * np.sqrt(context.T @ A_inv @ context)
        
        # Break ties with ABSTAIN
        max_p = np.max(p_t)
        best_actions = np.where(p_t == max_p)[0]
        if 0 in best_actions:
            return 0
        return int(best_actions[0])
    
    def update(self, action: int, context: np.ndarray, reward: float) -> None:
        # Update A and b for the chosen action
        self.A[action] += np.outer(context, context)
        self.b[action] += reward * context
    
    def serialize(self) -> dict:
        return {
            'A': {a: self.A[a].tolist() for a in range(self.n_actions)},
            'b': {a: self.b[a].tolist() for a in range(self.n_actions)},
            'n_actions': self.n_actions,
            'n_features': self.n_features,
            'alpha': self.alpha
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LinUCBAgent':
        agent = cls(n_actions=data['n_actions'], n_features=data['n_features'], alpha=data['alpha'])
        agent.A = {int(a): np.array(mat) for a, mat in data['A'].items()}
        agent.b = {int(a): np.array(vec) for a, vec in data['b'].items()}
        return agent

class RLDecisionLayer:
    # Wraps the contextual bandit
    # Only active when rl_enabled = True in engine_settings
    # When disabled: pass through to NO-BET gate result
    
    def __init__(self, agent: LinUCBAgent, reward_calc: RewardCalculator,
                 min_observations: int = 500):  # Need 500 settled bets before RL matters
        self.agent = agent
        self.reward_calc = reward_calc
        self.is_enabled = False  # MUST read from engine_settings
        self.min_observations = min_observations
    
    def decide(self, candidate, match_state, n_settled_bets: int) -> str:
        if not self.is_enabled:
            # Pass through NO-BET gate result
            return getattr(candidate, 'decision', 'NO_BET')
        
        if n_settled_bets < self.min_observations:
            # Not enough data for RL to be meaningful
            return getattr(candidate, 'decision', 'NO_BET')
        
        # Get RL state
        state = RLState.from_candidate(candidate, match_state)
        context = state.to_array()
        
        # Get bandit recommendation
        action_idx = self.agent.select_action(context)
        rl_action = V1_ACTIONS[action_idx]
        
        original_decision = getattr(candidate, 'decision', 'NO_BET')
        
        # RL can only ABSTAIN when NO-BET gate already says BET_CANDIDATE
        # RL cannot OVERRIDE a NO_BET into a BET
        if original_decision == 'NO_BET':
            return 'NO_BET'  # RL cannot force a bet
        
        return 'BET_CANDIDATE' if rl_action == Action.BET else 'ABSTAIN'
    
    def record_outcome(self, prediction_id: str, action: str,
                       context: np.ndarray, reward: float) -> None:
        # Update bandit after outcome known
        action_idx = V1_ACTIONS.index(action)
        self.agent.update(action_idx, context, reward)
