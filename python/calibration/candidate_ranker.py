from python.calibration.no_bet_gate import BetCandidate

class CandidateRanker:
    def rank(self, candidates: list[BetCandidate]) -> list[BetCandidate]:
        valid_candidates = [c for c in candidates if c.is_candidate]
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda c: self._compute_risk_adjusted_score(c),
            reverse=True
        )
        return sorted_candidates
    
    def _compute_risk_adjusted_score(self, candidate: BetCandidate) -> float:
        # V1 heuristic (transparent, labeled as requiring learning):
        # score = ev * (1 - uncertainty) * freshness_factor * calibration_weight
        
        # All factors should ideally be bounded [0,1], EV is raw
        ev = max(0.0, candidate.expected_value)
        certainty = max(0.0, 1.0 - candidate.uncertainty)
        
        # Freshness factor: degrades from 1.0 down to 0.5 based on how old odds are
        max_freshness = 1800  # 30 mins
        freshness_ratio = min(1.0, candidate.odds_freshness_seconds / max_freshness)
        freshness_factor = 1.0 - (0.5 * freshness_ratio)
        
        calibration_weight = 1.0  # assumed 1.0 for V1 if model_calibrated was True
        
        score = ev * certainty * freshness_factor * calibration_weight
        return score
