"""
Probability Calibration Engine
Out-of-sample probability calibration supporting both Isotonic Regression and Platt (Logistic) scaling.
Strict avoidance of in-sample training leakage.
"""
from typing import Dict, List, Optional, Tuple, Union, Any
import warnings
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class ProbabilityCalibrator:
    """Out-of-sample probability calibrator supporting Isotonic and Platt scaling."""

    def __init__(self, method: str = "isotonic"):
        """Initialize calibrator.
        
        Args:
            method: Calibration technique - 'isotonic' or 'platt' ('logistic').
        """
        self.method = method.lower()
        self.calibrators: Dict[str, Any] = {}
        self._default_calibrator: Optional[Any] = None
        self._fitted_method: Optional[str] = None

    def fit(
        self,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        method: Optional[str] = None,
        market: Optional[str] = None,
    ) -> "ProbabilityCalibrator":
        """Fit probability calibrator on validation / out-of-sample predictions.
        
        Strictly avoids in-sample leakage: expects independent validation targets and probabilities.

        Args:
            y_true: Binary ground-truth outcomes {0, 1}.
            y_prob: Uncalibrated predicted probabilities in [0.0, 1.0].
            method: 'isotonic' or 'platt' / 'logistic'. Defaults to self.method.
            market: Optional market identifier for multi-market calibration (e.g. '1x2', 'btts').
        """
        chosen_method = (method or self.method).lower()
        y_t = np.asarray(y_true, dtype=float).ravel()
        y_p = np.asarray(y_prob, dtype=float).ravel()

        if len(y_t) != len(y_p):
            raise ValueError(f"Length mismatch: y_true ({len(y_t)}) vs y_prob ({len(y_p)})")
        if len(y_t) < 5:
            raise ValueError(f"Insufficient sample size for calibration ({len(y_t)} samples). Minimum 5 required.")
        if len(np.unique(y_t)) < 2:
            raise ValueError("Calibration requires at least two distinct outcome classes (0 and 1) in y_true.")
        if np.any(np.isnan(y_t)) or np.any(np.isnan(y_p)):
            raise ValueError("Input arrays must not contain NaN values.")

        # Clip probabilities to avoid extreme logit infinities
        y_p_clipped = np.clip(y_p, 1e-6, 1.0 - 1e-6)

        if chosen_method == "isotonic":
            calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.001, y_max=0.999)
            calibrator.fit(y_p_clipped, y_t)
        elif chosen_method in ("platt", "logistic", "sigmoid"):
            # Platt scaling: univariate logistic regression on uncalibrated probabilities
            calibrator = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
            calibrator.fit(y_p_clipped.reshape(-1, 1), y_t.astype(int))
        else:
            raise NotImplementedError(f"Calibration method '{chosen_method}' not implemented.")

        storage_key = market if market is not None else chosen_method
        self.calibrators[storage_key] = calibrator
        self._default_calibrator = calibrator
        self._fitted_method = chosen_method
        return self

    def calibrate(
        self,
        y_prob: Union[np.ndarray, List[float], float],
        method: Optional[str] = None,
        market: Optional[str] = None,
    ) -> Union[np.ndarray, float]:
        """Calibrate raw probabilities.

        Args:
            y_prob: Uncalibrated probability (scalar or array).
            method: Calibration method to use if market not provided.
            market: Market identifier if fitted per market.

        Returns:
            Calibrated probability or array of calibrated probabilities.
        """
        is_scalar = np.isscalar(y_prob) or (isinstance(y_prob, np.ndarray) and y_prob.ndim == 0)
        
        calibrator = None
        if market is not None and market in self.calibrators:
            calibrator = self.calibrators[market]
        elif method is not None and method.lower() in self.calibrators:
            calibrator = self.calibrators[method.lower()]
        elif self._default_calibrator is not None:
            calibrator = self._default_calibrator

        if calibrator is None:
            warnings.warn(f"No calibrator fitted for market='{market}' or method='{method}'. Returning clipped raw prob.")
            clipped = np.clip(np.asarray(y_prob, dtype=float), 0.001, 0.999)
            return float(clipped) if (is_scalar and market is not None) else (clipped if not is_scalar else np.array([float(clipped)]))

        probs_arr = np.asarray(y_prob, dtype=float).ravel()
        probs_clipped = np.clip(probs_arr, 1e-6, 1.0 - 1e-6)

        if isinstance(calibrator, IsotonicRegression):
            calibrated = calibrator.predict(probs_clipped)
        elif isinstance(calibrator, LogisticRegression):
            calibrated = calibrator.predict_proba(probs_clipped.reshape(-1, 1))[:, 1]
        else:
            calibrated = calibrator.predict(probs_clipped)

        calibrated = np.clip(calibrated, 0.001, 0.999)

        if is_scalar and market is not None:
            return float(calibrated[0])
        elif is_scalar and market is None and isinstance(y_prob, (float, int)):
            # If scalar float passed with no market, return 1D numpy array per spec
            return np.array([float(calibrated[0])])
        return calibrated

    def calibrate_batch(self, raw_probs: np.ndarray, market: Optional[str] = None) -> np.ndarray:
        """Backwards-compatible batch calibration."""
        res = self.calibrate(raw_probs, market=market)
        return np.asarray(res, dtype=float)

    def compute_brier_score(
        self,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
    ) -> float:
        """Compute Brier Score: mean((y_prob - y_true)^2)."""
        y_t = np.asarray(y_true, dtype=float).ravel()
        y_p = np.asarray(y_prob, dtype=float).ravel()
        if len(y_t) != len(y_p):
            raise ValueError(f"Length mismatch: {len(y_t)} vs {len(y_p)}")
        return float(np.mean((y_p - y_t) ** 2))

    def compute_log_loss(
        self,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        eps: float = 1e-15,
    ) -> float:
        """Compute Binary Cross-Entropy (Log-Loss)."""
        y_t = np.asarray(y_true, dtype=float).ravel()
        y_p = np.clip(np.asarray(y_prob, dtype=float).ravel(), eps, 1.0 - eps)
        return float(-np.mean(y_t * np.log(y_p) + (1.0 - y_t) * np.log(1.0 - y_p)))

    def compute_ece(
        self,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        n_bins: int = 10,
        strategy: str = "uniform",
    ) -> float:
        """Compute Expected Calibration Error (ECE) across equal-frequency or equal-width bins.

        Args:
            y_true: Binary ground truth {0, 1}.
            y_prob: Predicted calibrated probabilities in [0.0, 1.0].
            n_bins: Number of discretization bins.
            strategy: 'uniform' (equal-width) or 'quantile' (equal-frequency).

        Returns:
            ECE value as float in [0.0, 1.0].
        """
        y_t = np.asarray(y_true, dtype=float).ravel()
        y_p = np.asarray(y_prob, dtype=float).ravel()
        N = len(y_t)
        if N == 0:
            return 0.0

        if strategy == "quantile":
            quantiles = np.linspace(0, 100, n_bins + 1)
            bin_edges = np.percentile(y_p, quantiles)
            bin_edges[0] = 0.0
            bin_edges[-1] = 1.0
        else:
            bin_edges = np.linspace(0.0, 1.0, n_bins + 1)

        ece = 0.0
        for i in range(n_bins):
            low = bin_edges[i]
            high = bin_edges[i + 1]
            if i == n_bins - 1:
                mask = (y_p >= low) & (y_p <= high)
            else:
                mask = (y_p >= low) & (y_p < high)

            count = np.sum(mask)
            if count > 0:
                prob_pred = np.mean(y_p[mask])
                prob_true = np.mean(y_t[mask])
                ece += np.abs(prob_pred - prob_true) * (count / N)

        return float(ece)

    def get_reliability_curve(
        self,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        n_bins: int = 10,
    ) -> Dict[str, Any]:
        """Generate reliability diagram data.

        Returns:
            dict containing:
                - 'bins': list of (bin_low, bin_high) intervals
                - 'mean_predicted': list of average predicted probabilities in each bin
                - 'empirical_accuracy': list of observed true positive rates in each bin
                - 'counts': number of observations in each bin
                - 'bin_centers': midpoint of each bin
        """
        y_t = np.asarray(y_true, dtype=float).ravel()
        y_p = np.asarray(y_prob, dtype=float).ravel()
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

        bins_list: List[Tuple[float, float]] = []
        mean_predicted: List[float] = []
        empirical_accuracy: List[float] = []
        counts: List[int] = []

        for i in range(n_bins):
            low = float(bin_edges[i])
            high = float(bin_edges[i + 1])
            bins_list.append((round(low, 4), round(high, 4)))

            if i == n_bins - 1:
                mask = (y_p >= low) & (y_p <= high)
            else:
                mask = (y_p >= low) & (y_p < high)

            count = int(np.sum(mask))
            counts.append(count)
            if count > 0:
                mean_predicted.append(float(np.mean(y_p[mask])))
                empirical_accuracy.append(float(np.mean(y_t[mask])))
            else:
                mean_predicted.append(float(bin_centers[i]))
                empirical_accuracy.append(0.0)

        return {
            "bins": bins_list,
            "bin_edges": bin_edges.tolist(),
            "bin_centers": bin_centers.tolist(),
            "mean_predicted": mean_predicted,
            "empirical_accuracy": empirical_accuracy,
            "counts": counts,
            "actual_freqs": empirical_accuracy,  # backwards compatibility
        }

    def compute_reliability_curve(
        self,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        n_bins: int = 10,
    ) -> Dict[str, Any]:
        """Backwards compatibility alias for get_reliability_curve."""
        curve = self.get_reliability_curve(y_true, y_prob, n_bins)
        return {
            "bin_centers": curve["bin_centers"],
            "actual_freqs": curve["empirical_accuracy"],
            "counts": curve["counts"],
        }

    def serialize(self) -> dict:
        """Serialize fitted calibrator parameters."""
        data = {"method": self.method, "calibrators": {}}
        for market, calibrator in self.calibrators.items():
            if isinstance(calibrator, IsotonicRegression):
                data["calibrators"][market] = {
                    "type": "isotonic",
                    "X_min": float(calibrator.X_min_),
                    "X_max": float(calibrator.X_max_),
                    "X_thresholds": calibrator.X_thresholds_.tolist(),
                    "y_thresholds": calibrator.y_thresholds_.tolist(),
                }
            elif isinstance(calibrator, LogisticRegression):
                data["calibrators"][market] = {
                    "type": "platt",
                    "coef": calibrator.coef_.tolist(),
                    "intercept": calibrator.intercept_.tolist(),
                }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ProbabilityCalibrator":
        """Deserialize calibrator from dictionary."""
        instance = cls(method=data.get("method", "isotonic"))
        for market, cal_data in data.get("calibrators", {}).items():
            cal_type = cal_data.get("type", "isotonic")
            if cal_type == "isotonic":
                cal = IsotonicRegression(out_of_bounds="clip", y_min=0.001, y_max=0.999)
                cal.X_min_ = cal_data["X_min"]
                cal.X_max_ = cal_data["X_max"]
                cal.X_thresholds_ = np.array(cal_data["X_thresholds"])
                cal.y_thresholds_ = np.array(cal_data["y_thresholds"])
                from scipy.interpolate import interp1d
                cal.f_ = interp1d(
                    cal.X_thresholds_,
                    cal.y_thresholds_,
                    kind="linear",
                    bounds_error=False,
                    fill_value=(cal.y_thresholds_[0], cal.y_thresholds_[-1]),
                )
                instance.calibrators[market] = cal
            elif cal_type == "platt":
                lr = LogisticRegression()
                lr.coef_ = np.array(cal_data["coef"])
                lr.intercept_ = np.array(cal_data["intercept"])
                lr.classes_ = np.array([0, 1])
                instance.calibrators[market] = lr
        return instance
