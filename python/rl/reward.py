class RewardCalculator:
    # Base reward: paper bet realized return
    # Penalties (configurable):
    BASE_OVERCONFIDENCE_PENALTY = -0.5  # calibrated_prob >> actual outcome
    BASE_STALE_DATA_PENALTY = -0.2     # acted on stale data
    BASE_DRAWDOWN_PENALTY = -0.3       # contributed to significant drawdown
    BASE_POOR_CALIBRATION_PENALTY = -0.1  # model poorly calibrated
    
    def calculate_reward(self,
                          action: str,
                          outcome: str,  # 'win', 'loss', 'void'
                          decimal_odds: float,
                          stake_units: float,
                          calibrated_prob: float,
                          data_freshness_seconds: int,
                          current_drawdown: float,
                          brier_contribution: float) -> float:
        if action == 'ABSTAIN':
            return 0.0
        
        if action == 'BET':
            reward = 0.0
            if outcome == 'win':
                reward = (decimal_odds - 1) * stake_units
            elif outcome == 'loss':
                reward = -stake_units
            
            # Penalties
            actual_outcome = 1.0 if outcome == 'win' else 0.0 if outcome == 'loss' else 0.5
            reward += self.apply_overconfidence_penalty(calibrated_prob, actual_outcome)
            reward += self.apply_drawdown_penalty(current_drawdown)
            
            if data_freshness_seconds > 300: # 5 minutes
                reward += self.BASE_STALE_DATA_PENALTY
                
            return reward
            
        return 0.0
    
    def apply_overconfidence_penalty(self, calibrated_prob: float, 
                                      actual_outcome: float) -> float:
        if calibrated_prob > 0.8 and actual_outcome == 0.0:
            return self.BASE_OVERCONFIDENCE_PENALTY * (calibrated_prob - 0.8) * 5.0
        return 0.0
    
    def apply_drawdown_penalty(self, current_drawdown: float,
                                threshold: float = 0.10) -> float:
        if current_drawdown > threshold:
            return self.BASE_DRAWDOWN_PENALTY
        return 0.0
