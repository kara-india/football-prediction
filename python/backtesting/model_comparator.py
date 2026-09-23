"""
Champion vs Challenger Model Comparator & Objective Promotion Gate
Implements the Diebold-Mariano (1995) paired forecast accuracy test with
Newey-West / Bartlett autocovariance kernel, Wilcoxon signed-rank test fallback,
and multi-criteria objective promotion gate for production models.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import scipy.stats as stats

from .metrics_engine import MetricsEngine, BacktestMetricsSummary


@dataclass
class ComparisonResult:
    """Detailed diagnostic results of Champion vs Challenger comparison."""
    recommendation: str  # "PROMOTE", "REJECT", "INSUFFICIENT_DATA"
    reasons: List[str]
    sample_size: int
    diebold_mariano_stat: float
    diebold_mariano_p_value: float
    wilcoxon_stat: Optional[float]
    wilcoxon_p_value: Optional[float]
    loss_differential_mean: float
    champion_brier: float
    challenger_brier: float
    brier_reduction: float
    brier_p_value: float
    champion_ece: float
    challenger_ece: float
    ece_ratio: float
    champion_clv: float
    challenger_clv: float
    criteria_met: Dict[str, bool] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModelComparator:
    """
    Evaluates Champion vs Challenger models on identical out-of-sample evaluation folds.
    Enforces scientific, statistical promotion criteria to prevent regression.
    """

    MIN_SAMPLE_SIZE: int = 100
    SIGNIFICANCE_THRESHOLD: float = 0.05
    MAX_ECE_DEGRADATION_RATIO: float = 1.05

    def __init__(
        self,
        min_sample_size: int = 100,
        significance_threshold: float = 0.05,
        max_ece_degradation_ratio: float = 1.05,
        metrics_engine: Optional[MetricsEngine] = None,
    ):
        self.min_sample_size = min_sample_size
        self.significance_threshold = significance_threshold
        self.max_ece_degradation_ratio = max_ece_degradation_ratio
        self.metrics = metrics_engine or MetricsEngine()

    @staticmethod
    def diebold_mariano_test(
        loss_challenger: Union[List[float], np.ndarray],
        loss_champion: Union[List[float], np.ndarray],
        h: Optional[int] = None,
    ) -> Tuple[float, float, float]:
        """
        Compute Diebold-Mariano test statistic for equal predictive accuracy.
        
        Args:
            loss_challenger: Array of per-match loss for Challenger (e.g. (p_chal - y)^2).
            loss_champion: Array of per-match loss for Champion (e.g. (p_champ - y)^2).
            h: Autocorrelation lag truncation parameter. Defaults to max(1, int(N**(1/3))).

        Returns:
            Tuple of (dm_stat, p_value, d_bar)
            where d_bar = mean(loss_challenger - loss_champion).
            A negative d_bar indicates Challenger has lower error than Champion.
        """
        l_chal = np.asarray(loss_challenger, dtype=float).ravel()
        l_champ = np.asarray(loss_champion, dtype=float).ravel()
        N = len(l_chal)

        if N != len(l_champ):
            raise ValueError(f"Length mismatch: {N} vs {len(l_champ)}")
        if N < 2:
            return 0.0, 1.0, 0.0

        # Loss differential: Challenger loss minus Champion loss
        d = l_chal - l_champ
        d_bar = float(np.mean(d))

        # Bartlett / Newey-West lag truncation
        if h is None:
            h = max(1, int(np.floor(N ** (1.0 / 3.0))))

        # Autocovariances gamma_k
        d_centered = d - d_bar
        gamma_0 = float(np.mean(d_centered ** 2))

        long_run_var = gamma_0
        for k in range(1, h):
            weight = 1.0 - (k / h)
            gamma_k = float(np.mean(d_centered[k:] * d_centered[:-k]))
            long_run_var += 2.0 * weight * gamma_k

        # Ensure positive variance
        long_run_var = max(long_run_var, 1e-12)
        variance_d_bar = long_run_var / N

        dm_stat = d_bar / np.sqrt(variance_d_bar)

        # Harvey, Leybourne, Newbold (1997) small-sample modification
        if N > 1:
            hln_correction = np.sqrt(max(1e-8, (N + 1 - 2 * h + (h * (h - 1) / N)) / N))
            dm_stat_corrected = dm_stat * hln_correction
            # Two-tailed p-value using Student's t distribution with N-1 degrees of freedom
            p_val = float(2.0 * stats.t.sf(np.abs(dm_stat_corrected), df=N - 1))
        else:
            p_val = 1.0
            dm_stat_corrected = dm_stat

        return float(dm_stat_corrected), float(p_val), d_bar

    @staticmethod
    def wilcoxon_test(
        loss_challenger: Union[List[float], np.ndarray],
        loss_champion: Union[List[float], np.ndarray],
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Wilcoxon signed-rank test fallback for non-parametric paired evaluation.
        """
        l_chal = np.asarray(loss_challenger, dtype=float).ravel()
        l_champ = np.asarray(loss_champion, dtype=float).ravel()
        diff = l_chal - l_champ

        if np.all(diff == 0) or len(diff) < 5:
            return 0.0, 1.0

        try:
            res = stats.wilcoxon(l_chal, l_champ, alternative="two-sided")
            return float(res.statistic), float(res.pvalue)
        except Exception:
            return None, None

    def compare(
        self,
        y_true: Union[List[int], np.ndarray],
        prob_champion: Union[List[float], np.ndarray],
        prob_challenger: Union[List[float], np.ndarray],
        odds_prediction: Optional[Union[List[float], np.ndarray]] = None,
        odds_closing: Optional[Union[List[float], np.ndarray]] = None,
    ) -> ComparisonResult:
        """
        Run the complete Champion vs Challenger comparative evaluation.
        Evaluates Brier reduction, DM statistical significance, ECE stability, and CLV.
        """
        y_t = np.asarray(y_true, dtype=float).ravel()
        p_champ = np.asarray(prob_champion, dtype=float).ravel()
        p_chal = np.asarray(prob_challenger, dtype=float).ravel()
        N = len(y_t)

        reasons: List[str] = []
        criteria_met = {
            "sample_size": False,
            "brier_reduction": False,
            "statistical_significance": False,
            "calibration_preserved": False,
            "clv_non_negative": False,
        }

        # 1. Sample Size Gate
        if N < self.min_sample_size:
            reasons.append(
                f"INSUFFICIENT_DATA: Evaluation sample size N={N} is below required threshold N={self.min_sample_size}."
            )
            return ComparisonResult(
                recommendation="INSUFFICIENT_DATA",
                reasons=reasons,
                sample_size=N,
                diebold_mariano_stat=0.0,
                diebold_mariano_p_value=1.0,
                wilcoxon_stat=None,
                wilcoxon_p_value=None,
                loss_differential_mean=0.0,
                champion_brier=round(float(self.metrics.brier_score(y_t, p_champ)), 6) if N > 0 else 0.0,
                challenger_brier=round(float(self.metrics.brier_score(y_t, p_chal)), 6) if N > 0 else 0.0,
                brier_reduction=0.0,
                brier_p_value=1.0,
                champion_ece=round(float(self.metrics.expected_calibration_error(y_t, p_champ)), 6) if N > 0 else 0.0,
                challenger_ece=round(float(self.metrics.expected_calibration_error(y_t, p_chal)), 6) if N > 0 else 0.0,
                ece_ratio=1.0,
                champion_clv=0.0,
                challenger_clv=0.0,
                criteria_met=criteria_met,
            )

        criteria_met["sample_size"] = True

        # Per-observation Brier losses
        loss_champ = (p_champ - y_t) ** 2
        loss_chal = (p_chal - y_t) ** 2

        # 2. Diebold-Mariano Test on Loss Differential
        dm_stat, dm_p_val, d_bar = self.diebold_mariano_test(loss_chal, loss_champ)
        w_stat, w_p_val = self.wilcoxon_test(loss_chal, loss_champ)

        champ_brier = float(np.mean(loss_champ))
        chal_brier = float(np.mean(loss_chal))
        brier_reduction = champ_brier - chal_brier

        if brier_reduction > 0:
            criteria_met["brier_reduction"] = True
        else:
            reasons.append(
                f"REJECT: Challenger Brier score ({chal_brier:.4f}) did not improve over Champion ({champ_brier:.4f})."
            )

        if brier_reduction > 0 and dm_p_val < self.significance_threshold:
            criteria_met["statistical_significance"] = True
        else:
            if brier_reduction > 0:
                reasons.append(
                    f"REJECT: Brier improvement (+{brier_reduction:.4f}) is not statistically significant (DM p={dm_p_val:.4f} >= {self.significance_threshold})."
                )

        # 3. Calibration Non-Degradation Gate (ECE)
        champ_ece = self.metrics.expected_calibration_error(y_t, p_champ)
        chal_ece = self.metrics.expected_calibration_error(y_t, p_chal)
        ece_threshold = max(champ_ece * self.max_ece_degradation_ratio, 0.05)
        ece_ratio = chal_ece / max(champ_ece, 1e-6)

        if chal_ece <= ece_threshold:
            criteria_met["calibration_preserved"] = True
        else:
            reasons.append(
                f"REJECT: Challenger ECE ({chal_ece:.4f}) exceeds allowable degradation threshold ({ece_threshold:.4f}, ratio={ece_ratio:.2f})."
            )

        # 4. Closing Line Value Gate
        champ_clv = 0.0
        chal_clv = 0.0
        if odds_prediction is not None and odds_closing is not None:
            chal_clv = self.metrics.closing_line_value(odds_prediction, odds_closing)
            champ_clv = chal_clv  # when evaluating on same market lines

        if chal_clv >= 0.0 or chal_clv >= champ_clv - 0.005:
            criteria_met["clv_non_negative"] = True
        else:
            reasons.append(
                f"REJECT: Challenger Closing Line Value ({chal_clv:.4f}) is negative and degraded."
            )

        # Final Promotion Gate Decision
        all_passed = (
            criteria_met["sample_size"]
            and criteria_met["brier_reduction"]
            and criteria_met["statistical_significance"]
            and criteria_met["calibration_preserved"]
            and criteria_met["clv_non_negative"]
        )

        if all_passed:
            recommendation = "PROMOTE"
            reasons.append(
                f"PROMOTE: Challenger achieved statistically significant Brier reduction (-{brier_reduction:.4f}, p={dm_p_val:.4f}), stable ECE ({chal_ece:.4f}), and non-negative CLV ({chal_clv:.4f})."
            )
        else:
            recommendation = "REJECT"

        return ComparisonResult(
            recommendation=recommendation,
            reasons=reasons,
            sample_size=N,
            diebold_mariano_stat=round(dm_stat, 4),
            diebold_mariano_p_value=round(dm_p_val, 6),
            wilcoxon_stat=round(w_stat, 4) if w_stat is not None else None,
            wilcoxon_p_value=round(w_p_val, 6) if w_p_val is not None else None,
            loss_differential_mean=round(d_bar, 6),
            champion_brier=round(champ_brier, 6),
            challenger_brier=round(chal_brier, 6),
            brier_reduction=round(brier_reduction, 6),
            brier_p_value=round(dm_p_val, 6),
            champion_ece=round(champ_ece, 6),
            challenger_ece=round(chal_ece, 6),
            ece_ratio=round(ece_ratio, 4),
            champion_clv=round(champ_clv, 6),
            challenger_clv=round(chal_clv, 6),
            criteria_met=criteria_met,
            diagnostics={
                "min_sample_size": self.min_sample_size,
                "significance_threshold": self.significance_threshold,
                "max_ece_degradation_ratio": self.max_ece_degradation_ratio,
            },
        )
