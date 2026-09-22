import numpy as np
import warnings

class ProbabilityCalibrator:
    def __init__(self, method: str = 'isotonic'):
        # method: 'isotonic', 'platt', 'beta'
        self.method = method
        self.calibrators = {}  # market -> fitted calibrator
    
    def fit(self, y_true: np.ndarray, y_pred: np.ndarray, market: str) -> None:
        if self.method == 'isotonic':
            from sklearn.isotonic import IsotonicRegression
            calibrator = IsotonicRegression(out_of_bounds='clip')
            calibrator.fit(y_pred, y_true)
            self.calibrators[market] = calibrator
        else:
            raise NotImplementedError(f"Method {self.method} not implemented yet.")
    
    def calibrate(self, raw_probability: float, market: str) -> float:
        if market not in self.calibrators:
            warnings.warn(f"No calibrator fitted for market {market}")
            return max(0.001, min(0.999, raw_probability))
        
        calibrated = self.calibrators[market].predict([raw_probability])[0]
        return float(np.clip(calibrated, 0.001, 0.999))
    
    def calibrate_batch(self, raw_probs: np.ndarray, market: str) -> np.ndarray:
        if market not in self.calibrators:
            warnings.warn(f"No calibrator fitted for market {market}")
            return np.clip(raw_probs, 0.001, 0.999)
            
        calibrated = self.calibrators[market].predict(raw_probs)
        return np.clip(calibrated, 0.001, 0.999)
    
    def compute_brier_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean((y_pred - y_true)**2))
    
    def compute_log_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        eps = 1e-15
        y_pred = np.clip(y_pred, eps, 1 - eps)
        return float(-np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)))
    
    def compute_ece(self, y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> float:
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i+1])
            if i == n_bins - 1:
                mask = mask | (y_pred == 1.0)
            if np.any(mask):
                prob_pred = np.mean(y_pred[mask])
                prob_true = np.mean(y_true[mask])
                ece += np.abs(prob_pred - prob_true) * np.sum(mask) / len(y_true)
        return float(ece)
    
    def compute_reliability_curve(self, y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> dict:
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        actual_freqs = []
        counts = []
        for i in range(n_bins):
            mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i+1])
            if i == n_bins - 1:
                mask = mask | (y_pred == 1.0)
            if np.any(mask):
                actual_freqs.append(float(np.mean(y_true[mask])))
            else:
                actual_freqs.append(np.nan)
            counts.append(int(np.sum(mask)))
        return {
            'bin_centers': bin_centers.tolist(),
            'actual_freqs': actual_freqs,
            'counts': counts
        }
    
    def serialize(self) -> dict:
        data = {'method': self.method, 'calibrators': {}}
        if self.method == 'isotonic':
            for market, calibrator in self.calibrators.items():
                data['calibrators'][market] = {
                    'X_min': float(calibrator.X_min_),
                    'X_max': float(calibrator.X_max_),
                    'X_thresholds': calibrator.X_thresholds_.tolist(),
                    'y_thresholds': calibrator.y_thresholds_.tolist(),
                }
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProbabilityCalibrator':
        instance = cls(method=data.get('method', 'isotonic'))
        if instance.method == 'isotonic':
            from sklearn.isotonic import IsotonicRegression
            for market, cal_data in data.get('calibrators', {}).items():
                cal = IsotonicRegression(out_of_bounds='clip')
                cal.X_min_ = cal_data['X_min']
                cal.X_max_ = cal_data['X_max']
                cal.X_thresholds_ = np.array(cal_data['X_thresholds'])
                cal.y_thresholds_ = np.array(cal_data['y_thresholds'])
                cal.f_ = lambda x: np.interp(x, cal.X_thresholds_, cal.y_thresholds_)
                # Need to mock predict properly for sklearn isotonic if reconstructed this way, 
                # but for simplicity we will just rely on interp in our own predict wrapper or fit manually.
                # Since sklearn's isotonic relies on `f_`, we construct it:
                from scipy.interpolate import interp1d
                cal.f_ = interp1d(cal.X_thresholds_, cal.y_thresholds_, kind='linear', 
                                  bounds_error=False, fill_value=(cal.y_thresholds_[0], cal.y_thresholds_[-1]))
                instance.calibrators[market] = cal
        return instance
