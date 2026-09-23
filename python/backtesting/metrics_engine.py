"""
Empirical Backtest Metrics & Lineup Information Value (LIV) Engine
Authentic computation of Brier Score, Log-Loss, Expected Calibration Error (ECE),
flat staking ROI, Closing Line Value (CLV), Maximum Drawdown, and Lineup Information Value (LIV).
Zero fake or hardcoded metrics permitted.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd


@dataclass
class BacktestMetricsSummary:
    """Out-of-sample empirical performance metrics."""
    brier_score: float
    log_loss: float
    ece: float
    roi: float
    mean_clv: float
    max_drawdown_units: float
    max_drawdown_pct: float
    sample_size: int
    win_rate: float
    total_profit: float
    total_staked: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LIVSegmentSummary:
    """LIV metrics for a specific segment (competition, market, or favorite status)."""
    segment_name: str
    sample_size: int
    liv_brier: float
    liv_log_loss: float
    mean_abs_prob_delta: float
    market_alignment_corr: float
    brier_pre: float
    brier_post: float


@dataclass
class LIVReport:
    """Comprehensive Lineup Information Value evaluation report."""
    sample_size: int
    liv_brier: float
    liv_log_loss: float
    mean_prob_delta: float
    mean_abs_prob_delta: float
    max_abs_prob_delta: float
    std_prob_delta: float
    market_alignment_corr: float
    brier_pre: float
    brier_post: float
    log_loss_pre: float
    log_loss_post: float
    by_competition: Dict[str, LIVSegmentSummary] = field(default_factory=dict)
    by_market: Dict[str, LIVSegmentSummary] = field(default_factory=dict)
    by_favorite_status: Dict[str, LIVSegmentSummary] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsEngine:
    """Empirical mathematical metrics calculator for sports prediction evaluation."""

    @staticmethod
    def brier_score(
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
    ) -> float:
        """
        Compute empirical Brier score:
        - Binary: (1/N) * sum((p_i - y_i)^2)
        - Multi-class: (1/N) * sum_i sum_k (p_ik - y_ik)^2
        """
        y_t = np.asarray(y_true, dtype=float)
        y_p = np.asarray(y_prob, dtype=float)

        if y_t.shape != y_p.shape:
            # Check if y_t is 1D class indices and y_p is 2D one-hot probabilities
            if y_t.ndim == 1 and y_p.ndim == 2:
                n_classes = y_p.shape[1]
                y_t_onehot = np.zeros_like(y_p)
                for idx, val in enumerate(y_t.astype(int)):
                    if 0 <= val < n_classes:
                        y_t_onehot[idx, val] = 1.0
                y_t = y_t_onehot
            else:
                y_t = y_t.ravel()
                y_p = y_p.ravel()

        if len(y_t) == 0:
            return 0.0

        diff = y_p - y_t
        if diff.ndim == 1:
            return float(np.mean(diff ** 2))
        else:
            # Multi-class sum over classes per observation, then mean over observations
            return float(np.mean(np.sum(diff ** 2, axis=1)))

    @staticmethod
    def log_loss(
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        eps: float = 1e-15,
    ) -> float:
        """
        Compute Logarithmic Loss (Cross-Entropy) with epsilon clamping:
        - Binary: -1/N * sum[y * ln(p) + (1-y) * ln(1-p)]
        - Multi-class: -1/N * sum_i sum_k y_ik * ln(p_ik)
        """
        y_t = np.asarray(y_true, dtype=float)
        y_p = np.asarray(y_prob, dtype=float)

        if y_t.shape != y_p.shape:
            if y_t.ndim == 1 and y_p.ndim == 2:
                n_classes = y_p.shape[1]
                y_t_onehot = np.zeros_like(y_p)
                for idx, val in enumerate(y_t.astype(int)):
                    if 0 <= val < n_classes:
                        y_t_onehot[idx, val] = 1.0
                y_t = y_t_onehot
            else:
                y_t = y_t.ravel()
                y_p = y_p.ravel()

        if len(y_t) == 0:
            return 0.0

        y_p_clipped = np.clip(y_p, eps, 1.0 - eps)

        if y_t.ndim == 1:
            loss = -(y_t * np.log(y_p_clipped) + (1.0 - y_t) * np.log(1.0 - y_p_clipped))
            return float(np.mean(loss))
        else:
            # Multi-class: normalize probabilities across rows just in case
            row_sums = y_p_clipped.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1.0
            p_norm = y_p_clipped / row_sums
            loss = -np.sum(y_t * np.log(p_norm), axis=1)
            return float(np.mean(loss))

    @staticmethod
    def expected_calibration_error(
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        n_bins: int = 10,
        strategy: str = "uniform",
    ) -> float:
        """
        Compute Expected Calibration Error (ECE) across 10 equal-width or equal-frequency bins.
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

    @staticmethod
    def flat_staking_roi(
        profit_loss: Union[List[float], np.ndarray],
        stakes: Optional[Union[List[float], np.ndarray]] = None,
    ) -> float:
        """
        Compute Flat 1.0 unit staking ROI: Net Profit / Total Stakes.
        """
        pnl = np.asarray(profit_loss, dtype=float)
        if len(pnl) == 0:
            return 0.0

        if stakes is not None:
            stk = np.asarray(stakes, dtype=float)
            total_staked = float(np.sum(stk))
        else:
            total_staked = float(len(pnl))  # Flat 1.0 unit stake per bet

        if total_staked <= 0.0:
            return 0.0

        return float(np.sum(pnl) / total_staked)

    @staticmethod
    def closing_line_value(
        odds_at_prediction: Union[float, List[float], np.ndarray],
        closing_odds: Union[float, List[float], np.ndarray],
    ) -> float:
        """
        Compute Closing Line Value (CLV):
        CLV = o_pred / o_close - 1.0
        Returns mean CLV across valid samples.
        """
        o_pred = np.asarray(odds_at_prediction, dtype=float).ravel()
        o_close = np.asarray(closing_odds, dtype=float).ravel()

        valid_mask = (o_pred > 1.0) & (o_close > 1.0)
        if not np.any(valid_mask):
            return 0.0

        clv_values = (o_pred[valid_mask] / o_close[valid_mask]) - 1.0
        return float(np.mean(clv_values))

    @staticmethod
    def maximum_drawdown(
        profit_loss: Union[List[float], np.ndarray],
        initial_bankroll: float = 100.0,
    ) -> Dict[str, float]:
        """
        Compute Maximum Drawdown in units and as a percentage of peak bankroll.
        """
        pnl = np.asarray(profit_loss, dtype=float).ravel()
        if len(pnl) == 0:
            return {"max_drawdown_units": 0.0, "max_drawdown_pct": 0.0}

        cum_pnl = np.cumsum(pnl)
        # Bankroll path starting at initial_bankroll
        bankroll = initial_bankroll + cum_pnl
        running_peak = np.maximum.accumulate(np.insert(bankroll, 0, initial_bankroll))[1:]

        drawdowns_units = running_peak - bankroll
        max_dd_units = float(np.max(drawdowns_units)) if len(drawdowns_units) > 0 else 0.0

        # Drawdown percentage relative to peak bankroll at that point
        drawdowns_pct = drawdowns_units / np.maximum(running_peak, 1e-4)
        max_dd_pct = float(np.max(drawdowns_pct)) if len(drawdowns_pct) > 0 else 0.0

        return {
            "max_drawdown_units": round(max_dd_units, 4),
            "max_drawdown_pct": round(max_dd_pct, 4),
        }

    @classmethod
    def compute_all_metrics(
        cls,
        y_true: Union[np.ndarray, List[float], List[int]],
        y_prob: Union[np.ndarray, List[float]],
        pnl: Union[np.ndarray, List[float]],
        odds_pred: Optional[Union[np.ndarray, List[float]]] = None,
        odds_close: Optional[Union[np.ndarray, List[float]]] = None,
        initial_bankroll: float = 100.0,
    ) -> BacktestMetricsSummary:
        """
        Compute the complete set of out-of-sample performance metrics.
        """
        y_t = np.asarray(y_true, dtype=float)
        y_p = np.asarray(y_prob, dtype=float)
        p_l = np.asarray(pnl, dtype=float)
        N = len(y_t)

        bs = cls.brier_score(y_t, y_p)
        ll = cls.log_loss(y_t, y_p)
        ece = cls.expected_calibration_error(y_t, y_p, n_bins=10)
        roi = cls.flat_staking_roi(p_l)

        clv = 0.0
        if odds_pred is not None and odds_close is not None:
            clv = cls.closing_line_value(odds_pred, odds_close)

        dd = cls.maximum_drawdown(p_l, initial_bankroll=initial_bankroll)

        win_count = np.sum(p_l > 0)
        win_rate = float(win_count / N) if N > 0 else 0.0
        total_profit = float(np.sum(p_l)) if N > 0 else 0.0
        total_staked = float(N)

        return BacktestMetricsSummary(
            brier_score=round(bs, 6),
            log_loss=round(ll, 6),
            ece=round(ece, 6),
            roi=round(roi, 6),
            mean_clv=round(clv, 6),
            max_drawdown_units=dd["max_drawdown_units"],
            max_drawdown_pct=dd["max_drawdown_pct"],
            sample_size=N,
            win_rate=round(win_rate, 4),
            total_profit=round(total_profit, 4),
            total_staked=round(total_staked, 4),
        )


class LineupInformationValueEngine:
    """
    Evaluates the empirical information value added by confirmed starting lineups.
    Computes Brier/LogLoss deltas, probability revisions, market alignment correlation,
    and multi-dimensional segmentation.
    """

    def __init__(self, metrics_engine: Optional[MetricsEngine] = None):
        self.metrics = metrics_engine or MetricsEngine()

    def evaluate_liv(
        self,
        records: List[Dict[str, Any]],
    ) -> LIVReport:
        """
        Compute Lineup Information Value (LIV) from a list of paired evaluation records.
        Each record must contain:
        - 'outcome': int/float (ground truth)
        - 'p_pre': float (initial pre-lineup probability)
        - 'p_post': float (confirmed lineup probability)
        - 'odds_pre': Optional[float] (early market odds)
        - 'odds_post': Optional[float] (market odds after lineup release)
        - 'competition': Optional[str]
        - 'market': Optional[str]
        """
        if not records:
            return LIVReport(
                sample_size=0,
                liv_brier=0.0,
                liv_log_loss=0.0,
                mean_prob_delta=0.0,
                mean_abs_prob_delta=0.0,
                max_abs_prob_delta=0.0,
                std_prob_delta=0.0,
                market_alignment_corr=0.0,
                brier_pre=0.0,
                brier_post=0.0,
                log_loss_pre=0.0,
                log_loss_post=0.0,
            )

        df = pd.DataFrame(records)
        y_true = df["outcome"].values
        p_pre = df["p_pre"].values
        p_post = df["p_post"].values

        brier_pre = self.metrics.brier_score(y_true, p_pre)
        brier_post = self.metrics.brier_score(y_true, p_post)
        liv_brier = brier_pre - brier_post  # positive = lineup improves accuracy

        ll_pre = self.metrics.log_loss(y_true, p_pre)
        ll_post = self.metrics.log_loss(y_true, p_post)
        liv_ll = ll_pre - ll_post

        prob_delta = p_post - p_pre
        abs_delta = np.abs(prob_delta)

        # Market alignment correlation
        market_corr = 0.0
        if "odds_pre" in df.columns and "odds_post" in df.columns:
            valid_odds = df["odds_pre"].notna() & df["odds_post"].notna() & (df["odds_pre"] > 1.0) & (df["odds_post"] > 1.0)
            if np.sum(valid_odds) >= 5:
                m_sub = df[valid_odds]
                market_prob_pre = 1.0 / m_sub["odds_pre"].values
                market_prob_post = 1.0 / m_sub["odds_post"].values
                market_delta = market_prob_post - market_prob_pre
                model_delta = m_sub["p_post"].values - m_sub["p_pre"].values

                # Pearson correlation between model delta and market delta
                std_model = np.std(model_delta)
                std_market = np.std(market_delta)
                if std_model > 1e-8 and std_market > 1e-8:
                    corr_matrix = np.corrcoef(model_delta, market_delta)
                    market_corr = float(corr_matrix[0, 1])

        # Segmentation by competition
        comp_summaries = {}
        if "competition" in df.columns:
            for comp, group in df.groupby("competition"):
                if len(group) >= 1:
                    comp_summaries[str(comp)] = self._compute_segment_summary(str(comp), group)

        # Segmentation by market
        market_summaries = {}
        if "market" in df.columns:
            for mkt, group in df.groupby("market"):
                if len(group) >= 1:
                    market_summaries[str(mkt)] = self._compute_segment_summary(str(mkt), group)

        # Segmentation by favorite status (p_pre >= 0.5 vs < 0.5)
        fav_summaries = {}
        fav_mask = df["p_pre"] >= 0.5
        if np.sum(fav_mask) >= 1:
            fav_summaries["FAVORITE"] = self._compute_segment_summary("FAVORITE", df[fav_mask])
        if np.sum(~fav_mask) >= 1:
            fav_summaries["UNDERDOG"] = self._compute_segment_summary("UNDERDOG", df[~fav_mask])

        return LIVReport(
            sample_size=len(df),
            liv_brier=round(float(liv_brier), 6),
            liv_log_loss=round(float(liv_ll), 6),
            mean_prob_delta=round(float(np.mean(prob_delta)), 6),
            mean_abs_prob_delta=round(float(np.mean(abs_delta)), 6),
            max_abs_prob_delta=round(float(np.max(abs_delta)), 6),
            std_prob_delta=round(float(np.std(prob_delta)), 6),
            market_alignment_corr=round(market_corr, 4),
            brier_pre=round(float(brier_pre), 6),
            brier_post=round(float(brier_post), 6),
            log_loss_pre=round(float(ll_pre), 6),
            log_loss_post=round(float(ll_post), 6),
            by_competition=comp_summaries,
            by_market=market_summaries,
            by_favorite_status=fav_summaries,
        )

    def _compute_segment_summary(self, name: str, group: pd.DataFrame) -> LIVSegmentSummary:
        y = group["outcome"].values
        p_pre = group["p_pre"].values
        p_post = group["p_post"].values

        b_pre = self.metrics.brier_score(y, p_pre)
        b_post = self.metrics.brier_score(y, p_post)
        ll_pre = self.metrics.log_loss(y, p_pre)
        ll_post = self.metrics.log_loss(y, p_post)

        mean_abs_d = float(np.mean(np.abs(p_post - p_pre)))

        corr = 0.0
        if "odds_pre" in group.columns and "odds_post" in group.columns:
            valid = (group["odds_pre"] > 1.0) & (group["odds_post"] > 1.0)
            if np.sum(valid) >= 4:
                m_pre = 1.0 / group.loc[valid, "odds_pre"].values
                m_post = 1.0 / group.loc[valid, "odds_post"].values
                m_delta = m_post - m_pre
                mod_delta = p_post[valid] - p_pre[valid]
                if np.std(m_delta) > 1e-8 and np.std(mod_delta) > 1e-8:
                    corr = float(np.corrcoef(mod_delta, m_delta)[0, 1])

        return LIVSegmentSummary(
            segment_name=name,
            sample_size=len(group),
            liv_brier=round(float(b_pre - b_post), 6),
            liv_log_loss=round(float(ll_pre - ll_post), 6),
            mean_abs_prob_delta=round(mean_abs_d, 6),
            market_alignment_corr=round(corr, 4),
            brier_pre=round(float(b_pre), 6),
            brier_post=round(float(b_post), 6),
        )
