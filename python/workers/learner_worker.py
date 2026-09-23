"""
Continual Online Learner & Controlled Promotion Worker
Monitors post-match evaluation results and updates continual learning layers:
  - Layer 3: Online residual updates (recent team-strength adjustments with L2 shrinkage)
  - Layer 2: Calibration monitoring (Brier score, ECE, Log-Loss, and reliability tracking)
  - Layer 1: Evaluates Challenger models vs Champion via ModelComparator (Diebold-Mariano test)
  - Controlled Promotion Gate: Strictly requires >= 250 matches, p < 0.05 Brier improvement,
    positive CLV, and non-degraded calibration (ECE ratio <= 1.05) before recommending promotion.
"""
import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np

from python.backtesting.model_comparator import ModelComparator, ComparisonResult
from python.backtesting.metrics_engine import MetricsEngine
from python.learning.online_learner import OnlineLearner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LearnerWorker")


class LearnerWorker:
    """Continual online learner executing Layer 2/3 drift adaptation and Champion/Challenger promotion gate."""

    PROMOTION_MIN_MATCHES: int = 250
    SIGNIFICANCE_THRESHOLD: float = 0.05
    MAX_ECE_DEGRADATION_RATIO: float = 1.05
    L2_SHRINKAGE: float = 5.0

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        comparator: Optional[ModelComparator] = None,
        metrics_engine: Optional[MetricsEngine] = None,
        online_learner: Optional[OnlineLearner] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://qqcxjjkgvqknesrtnwal.supabase.co")
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )
        self.metrics_engine = metrics_engine or MetricsEngine()
        self.online_learner = online_learner or OnlineLearner()
        self.comparator = comparator or ModelComparator(
            min_sample_size=self.PROMOTION_MIN_MATCHES,
            significance_threshold=self.SIGNIFICANCE_THRESHOLD,
            max_ece_degradation_ratio=self.MAX_ECE_DEGRADATION_RATIO,
            metrics_engine=self.metrics_engine,
        )

        # In-memory canonical dataset & team residuals
        self._canonical_learning_dataset: List[Dict[str, Any]] = []
        self._team_residuals: Dict[str, float] = {}

    def is_learning_enabled(self) -> bool:
        """Check engine_settings for learning_enabled switch."""
        if not self.supabase_url or not self.supabase_key:
            return True

        try:
            url = f"{self.supabase_url}/rest/v1/engine_settings?key=eq.learning_enabled&select=value"
            req = urllib.request.Request(
                url,
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    rows = json.loads(resp.read().decode("utf-8"))
                    if rows and rows[0].get("value") in ("false", "0", "False"):
                        return False
        except Exception:
            pass

        return True

    def update_layer3_team_residuals(
        self,
        match_settlements: List[Dict[str, Any]],
        l2_lambda: float = L2_SHRINKAGE,
    ) -> Dict[str, float]:
        """Update Layer 3 online residuals with L2 / Ridge shrinkage toward baseline.
        
        Formula: delta_theta = sum(residuals) / (count + l2_lambda)
        """
        team_diffs: Dict[str, List[float]] = {}

        for s in match_settlements:
            team_h = str(s.get("home_team_id", s.get("home_team", "H")))
            team_a = str(s.get("away_team_id", s.get("away_team", "A")))
            h_score = s.get("score_home", s.get("actual_home_goals", 0))
            a_score = s.get("score_away", s.get("actual_away_goals", 0))
            pred_h = s.get("predicted_home_goals", 1.45)
            pred_a = s.get("predicted_away_goals", 1.15)

            r_h = float(h_score - pred_h)
            r_a = float(a_score - pred_a)

            team_diffs.setdefault(team_h, []).append(r_h)
            team_diffs.setdefault(team_a, []).append(r_a)

        # Apply L2 shrinkage
        updated_residuals = {}
        for team, residuals in team_diffs.items():
            count = len(residuals)
            shrunk_adjustment = float(sum(residuals) / (count + l2_lambda))
            current = self._team_residuals.get(team, 0.0)
            updated_residuals[team] = round(0.85 * current + 0.15 * shrunk_adjustment, 5)

        self._team_residuals.update(updated_residuals)
        return updated_residuals

    def monitor_layer2_calibration(
        self,
        y_true: np.ndarray,
        probs: np.ndarray,
    ) -> Dict[str, float]:
        """Compute rolling calibration metrics: Brier, ECE, Log-Loss."""
        if len(y_true) == 0:
            return {"brier_score": 0.0, "ece": 0.0, "log_loss": 0.0}

        brier = float(np.mean((probs - y_true) ** 2))
        eps = 1e-15
        p_clipped = np.clip(probs, eps, 1.0 - eps)
        log_loss = float(-np.mean(y_true * np.log(p_clipped) + (1.0 - y_true) * np.log(1.0 - p_clipped)))
        
        # 10-bin Expected Calibration Error (ECE)
        bins = np.linspace(0.0, 1.0, 11)
        ece = 0.0
        n = len(y_true)
        for i in range(10):
            idx = (probs >= bins[i]) & (probs < bins[i + 1]) if i < 9 else (probs >= bins[i]) & (probs <= bins[i + 1])
            if np.sum(idx) > 0:
                bin_acc = np.mean(y_true[idx])
                bin_conf = np.mean(probs[idx])
                ece += (np.sum(idx) / n) * np.abs(bin_acc - bin_conf)

        return {
            "brier_score": round(brier, 6),
            "ece": round(float(ece), 6),
            "log_loss": round(log_loss, 6),
        }

    def evaluate_challenger_promotion(
        self,
        y_true: Union[List[int], np.ndarray],
        prob_champion: Union[List[float], np.ndarray],
        prob_challenger: Union[List[float], np.ndarray],
        odds_pred: Optional[Union[List[float], np.ndarray]] = None,
        odds_close: Optional[Union[List[float], np.ndarray]] = None,
    ) -> ComparisonResult:
        """Run controlled Champion vs Challenger promotion evaluation via ModelComparator."""
        return self.comparator.compare(
            y_true=y_true,
            prob_champion=prob_champion,
            prob_challenger=prob_challenger,
            odds_prediction=odds_pred,
            odds_closing=odds_close,
        )

    def run(
        self,
        batch_settlements: Optional[List[Dict[str, Any]]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute continual learner worker cycle."""
        logger.info(f"Starting LearnerWorker execution (dry_run={dry_run})...")

        if not self.is_learning_enabled():
            logger.info("learning_enabled is false in engine_settings. Exiting cleanly.")
            return {
                "status": "skipped",
                "reason": "learning_disabled",
                "samples_processed": 0,
            }

        dataset = batch_settlements or []

        # If no batch provided and in dry_run mode, synthesize training batch
        if not dataset and dry_run:
            np.random.seed(42)
            n_samples = 300
            y_synth = np.random.binomial(1, 0.50, size=n_samples)
            p_champ = np.clip(y_synth * 0.40 + np.random.uniform(0.1, 0.4, size=n_samples), 0.05, 0.95)
            p_chal = np.clip(y_synth * 0.50 + np.random.uniform(0.1, 0.3, size=n_samples), 0.05, 0.95)
            odds_pred = np.full(n_samples, 2.05)
            odds_close = np.full(n_samples, 2.00)

            dataset = [
                {
                    "prediction_id": f"synth_{i}",
                    "y_true": int(y_synth[i]),
                    "prob_champion": float(p_champ[i]),
                    "prob_challenger": float(p_chal[i]),
                    "odds_pred": float(odds_pred[i]),
                    "odds_close": float(odds_close[i]),
                    "home_team_id": (i % 10) + 1,
                    "away_team_id": ((i + 3) % 10) + 1,
                    "score_home": 2 if y_synth[i] == 1 else 0,
                    "score_away": 1 if y_synth[i] == 0 else 0,
                }
                for i in range(n_samples)
            ]

        if not dataset:
            logger.info("No settled predictions available for continual learning.")
            return {
                "status": "success",
                "samples_processed": 0,
                "promotion_recommendation": "NO_DATA",
            }

        # 1. Append to canonical learning dataset
        self._canonical_learning_dataset.extend(dataset)

        # 2. Update Layer 3 online residuals
        updated_residuals = self.update_layer3_team_residuals(dataset)

        # 3. Update Layer 2 calibration monitoring
        y_arr = np.array([d.get("y_true", 1 if d.get("actual_outcome") == "WON" else 0) for d in dataset])
        p_champ_arr = np.array([d.get("prob_champion", d.get("calibrated_probability", 0.5)) for d in dataset])
        p_chal_arr = np.array([d.get("prob_challenger", d.get("calibrated_probability", 0.5)) for d in dataset])
        odds_p_arr = np.array([d.get("odds_pred", d.get("decimal_odds", 2.0)) for d in dataset])
        odds_c_arr = np.array([d.get("odds_close", d.get("closing_odds", 2.0)) for d in dataset])

        cal_metrics = self.monitor_layer2_calibration(y_arr, p_champ_arr)

        # 4. Evaluate Champion vs Challenger promotion gate
        comparison = self.evaluate_challenger_promotion(
            y_true=y_arr,
            prob_champion=p_champ_arr,
            prob_challenger=p_chal_arr,
            odds_pred=odds_p_arr,
            odds_close=odds_c_arr,
        )

        logger.info(
            f"LearnerWorker completed: {len(dataset)} samples processed. "
            f"Promotion Recommendation: {comparison.recommendation} (DM p={comparison.diebold_mariano_p_value:.4f})."
        )

        return {
            "status": "success",
            "samples_processed": len(dataset),
            "layer3_teams_updated": len(updated_residuals),
            "calibration_metrics": cal_metrics,
            "promotion_recommendation": comparison.recommendation,
            "reasons": comparison.reasons,
            "diebold_mariano_p_value": comparison.diebold_mariano_p_value,
            "criteria_met": comparison.criteria_met,
            "errors": [],
        }


def run_learner_worker(dry_run: bool = False) -> Dict[str, Any]:
    """CLI / runner entrypoint for learner worker."""
    worker = LearnerWorker()
    return worker.run(dry_run=dry_run)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    res = run_learner_worker(dry_run=is_dry)
    logger.info(f"Learner worker completed: {res}")
    sys.exit(0)
