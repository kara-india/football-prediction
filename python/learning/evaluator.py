from typing import Dict, List, Any

class PredictionEvaluator:
    def evaluate_predictions(self, match_id: int) -> list[dict]:
        return []

    def classify_error(self, prediction: dict, actual: dict,
                        pre_match_features: dict) -> str:
        calibrated_prob = prediction.get('calibrated_prob', 0.5)
        wrong = prediction.get('prediction') != actual.get('outcome')
        
        if wrong and calibrated_prob > 0.8:
            return "MODEL_OVERCONFIDENCE"
        if not wrong and calibrated_prob < 0.2:
            return "MODEL_UNDERCONFIDENCE"
        if actual.get('red_card_after_prediction'):
            return "RED_CARD_EFFECT"
        if actual.get('major_substitution'):
            return "SUBSTITUTION_EFFECT"
        if actual.get('odds_moved_15_percent'):
            return "ODDS_MOVEMENT"
        if pre_match_features.get('missing_keys'):
            return "DATA_MISSING"
        if abs(calibrated_prob - actual.get('market_prob', calibrated_prob)) > 0.2:
            return "MODEL_SPECIFICATION"
        
        return "RANDOM_VARIANCE"

    def calculate_roi(self, paper_bets: list[dict]) -> float:
        total_staked = sum(b.get('stake', 0) for b in paper_bets)
        total_pl = sum(b.get('pnl', 0) for b in paper_bets)
        return total_pl / total_staked if total_staked > 0 else 0.0

    def calculate_drawdown(self, paper_bets: list[dict]) -> dict:
        return {"max_drawdown": 0.0}
