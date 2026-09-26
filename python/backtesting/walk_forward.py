"""
Walk-Forward Validation & Replay Backtester Engine
Performs authentic out-of-sample temporal cross-validation with zero lookahead.
Folds enforce strict non-overlapping Train [T0, T1] -> Calibrate [T1, T2] -> Test [T2, T3] boundaries.
Computes real empirical metrics (Brier, Log-Loss, ECE, ROI, CLV, Max Drawdown).
Zero hardcoded or mock metrics permitted.
"""
import argparse
import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Callable, Optional, Union
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from python.calibration.calibrator import ProbabilityCalibrator
from python.engine.settlement import SettlementEngine
from python.backtesting.metrics_engine import MetricsEngine, BacktestMetricsSummary
from python.backtesting.model_comparator import ModelComparator, ComparisonResult

logger = logging.getLogger(__name__)


def _to_date(val: Any) -> date:
    """Normalize timestamp or string into a date object."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        val_clean = val.strip().replace("Z", "").split("T")[0]
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val_clean, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Cannot parse date from: {val}")


class WalkForwardValidator:
    """
    Temporal Walk-Forward Validator executing sliding or expanding holdout evaluations.
    """

    def __init__(
        self,
        initial_train_months: int = 24,
        calibration_months: int = 3,
        test_months: int = 1,
        step_months: int = 1,
        mode: str = "sliding",  # "sliding" or "expanding"
        calibration_method: str = "isotonic",
        validation_months: Optional[int] = None,  # backwards compatibility alias
    ):
        self.initial_train_months = initial_train_months
        self.step_months = step_months
        self.mode = mode.lower()
        self.calibration_method = calibration_method.lower()

        if validation_months is not None:
            # Backwards compatibility: when validation_months is explicitly supplied,
            # calibration is bypassed unless calibration_months is specified separately
            self.test_months = validation_months
            self.calibration_months = 0
            self.validation_months = validation_months
        else:
            self.calibration_months = calibration_months
            self.test_months = test_months
            self.validation_months = test_months

        self.metrics_engine = MetricsEngine()
        self.comparator = ModelComparator()

    def generate_folds(
        self,
        all_matches: Union[pd.DataFrame, List[Any]],
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Generate temporal evaluation folds strictly respecting temporal boundaries.
        Each fold defines:
        - Train: [train_start, train_end)
        - Calibrate: [cal_start, cal_end) (if calibration_months > 0)
        - Test: [test_start, test_end)
        """
        s_date = _to_date(start_date)
        e_date = _to_date(end_date)
        folds = []

        k = 0
        while True:
            # Calculate train window
            if self.mode == "expanding":
                train_start = s_date
                train_end = s_date + relativedelta(months=self.initial_train_months + k * self.step_months)
            else:  # sliding
                train_start = s_date + relativedelta(months=k * self.step_months)
                train_end = train_start + relativedelta(months=self.initial_train_months)

            # Calculate calibration window
            if self.calibration_months > 0:
                cal_start = train_end
                cal_end = cal_start + relativedelta(months=self.calibration_months)
                test_start = cal_end
            else:
                cal_start = train_end
                cal_end = train_end
                test_start = train_end

            # Calculate out-of-sample evaluation window
            test_end = test_start + relativedelta(months=self.test_months)

            # Invariant: evaluation window must not exceed dataset end date
            if test_end > e_date:
                break

            fold_info = {
                "fold_index": k,
                "train_start": train_start,
                "train_end": train_end,
                "cal_start": cal_start,
                "cal_end": cal_end,
                "test_start": test_start,
                "test_end": test_end,
                # Aliases for backwards compatibility with existing tests
                "val_start": test_start,
                "val_end": test_end,
            }
            folds.append(fold_info)
            k += 1

        return folds

    def validate_model(
        self,
        model_factory: Callable[[], Any],
        features: pd.DataFrame,
        outcomes: Optional[Union[pd.Series, np.ndarray, List[Any]]] = None,
        folds: Optional[List[Dict[str, Any]]] = None,
        date_col: str = "date",
        target_col: str = "outcome",
        odds_col: Optional[str] = "odds",
        closing_odds_col: Optional[str] = "closing_odds",
        market: str = "1X2",
    ) -> Dict[str, Any]:
        """
        Execute full walk-forward validation across all folds.
        Fits model on train, calibrates on validation, evaluates out-of-sample on test.
        Computes genuine empirical metrics with zero mocked or static values.
        """
        df = features.copy()
        if outcomes is not None:
            df[target_col] = np.asarray(outcomes)

        # Ensure date column exists and is normalized
        if date_col not in df.columns:
            for alt in ("match_date", "kickoff_utc", "datetime", "Date"):
                if alt in df.columns:
                    date_col = alt
                    break

        if date_col in df.columns:
            df["_parsed_date"] = df[date_col].apply(_to_date)
        else:
            raise ValueError(f"Features dataframe missing date column: '{date_col}'")

        # Sort chronologically to preserve prequential order
        df = df.sort_values(by="_parsed_date").reset_index(drop=True)

        if folds is None:
            min_date = df["_parsed_date"].min()
            max_date = df["_parsed_date"].max()
            folds = self.generate_folds(df, min_date, max_date)

        if not folds:
            return {
                "mean_brier": 0.0,
                "std_brier": 0.0,
                "mean_log_loss": 0.0,
                "std_log_loss": 0.0,
                "mean_ece": 0.0,
                "overall_roi": 0.0,
                "mean_clv": 0.0,
                "max_drawdown_units": 0.0,
                "max_drawdown_pct": 0.0,
                "total_predictions": 0,
                "folds": [],
            }

        fold_summaries = []
        all_y_true = []
        all_y_prob = []
        all_pnl = []
        all_clv = []

        for fold in folds:
            t_start, t_end = fold["train_start"], fold["train_end"]
            c_start, c_end = fold["cal_start"], fold["cal_end"]
            eval_start, eval_end = fold["test_start"], fold["test_end"]

            # Filter data partitions
            train_mask = (df["_parsed_date"] >= t_start) & (df["_parsed_date"] < t_end)
            cal_mask = (df["_parsed_date"] >= c_start) & (df["_parsed_date"] < c_end)
            test_mask = (df["_parsed_date"] >= eval_start) & (df["_parsed_date"] < eval_end)

            train_df = df[train_mask]
            cal_df = df[cal_mask]
            test_df = df[test_mask]

            if len(train_df) == 0 or len(test_df) == 0:
                continue

            # 1. Instantiate and fit model on Train partition
            model = model_factory()
            self._fit_model(model, train_df, target_col)

            # 2. Probability Calibration on Calibration partition (if available)
            calibrator = None
            if self.calibration_months > 0 and len(cal_df) >= 5:
                cal_y = cal_df[target_col].values
                if len(np.unique(cal_y)) >= 2:
                    raw_cal_probs = self._predict_model(model, cal_df)
                    calibrator = ProbabilityCalibrator(method=self.calibration_method)
                    try:
                        calibrator.fit(cal_y, raw_cal_probs)
                    except Exception as e:
                        logger.warning(f"Calibration fit failed on fold {fold.get('fold_index')}: {e}")
                        calibrator = None

            # 3. Out-of-sample prediction on Test partition
            raw_test_probs = self._predict_model(model, test_df)
            if calibrator is not None:
                cal_test_probs = np.asarray(calibrator.calibrate(raw_test_probs), dtype=float)
            else:
                cal_test_probs = np.clip(np.asarray(raw_test_probs, dtype=float), 0.001, 0.999)

            y_test = test_df[target_col].values

            # Betting/CLV metrics require observed odds. Never substitute a
            # synthetic price (for example 2.0) when odds are missing.
            odds_available = bool(odds_col and odds_col in test_df.columns)
            if odds_available:
                odds_series = pd.to_numeric(test_df[odds_col], errors="coerce")
                valid_odds_mask = odds_series.notna() & (odds_series > 1.0)
                odds_test = odds_series.to_numpy(dtype=float)
            else:
                valid_odds_mask = np.zeros(len(test_df), dtype=bool)
                odds_test = np.full(len(y_test), np.nan)

            if closing_odds_col and closing_odds_col in test_df.columns:
                close_series = pd.to_numeric(test_df[closing_odds_col], errors="coerce")
                close_odds_test = close_series.to_numpy(dtype=float)
            else:
                close_odds_test = np.full(len(y_test), np.nan)

            pnl_fold = []
            valid_close_pred = []
            valid_close_odds = []
            for idx, (y_val, prob, o_val) in enumerate(zip(y_test, cal_test_probs, odds_test)):
                if not valid_odds_mask[idx]:
                    continue
                ev = (prob * o_val) - 1.0
                if ev > 0.0:
                    won = (y_val == 1) or (y_val is True)
                    pnl_fold.append((o_val - 1.0) if won else -1.0)
                    if np.isfinite(close_odds_test[idx]) and close_odds_test[idx] > 1.0:
                        valid_close_pred.append(o_val)
                        valid_close_odds.append(close_odds_test[idx])

            # Compute empirical metrics on this test fold
            bs = self.metrics_engine.brier_score(y_test, cal_test_probs)
            ll = self.metrics_engine.log_loss(y_test, cal_test_probs)
            ece = self.metrics_engine.expected_calibration_error(y_test, cal_test_probs)
            roi = self.metrics_engine.flat_staking_roi(pnl_fold) if pnl_fold else None
            clv = (
                self.metrics_engine.closing_line_value(
                    np.asarray(valid_close_pred, dtype=float),
                    np.asarray(valid_close_odds, dtype=float),
                )
                if valid_close_pred
                else None
            )
            dd = self.metrics_engine.maximum_drawdown(pnl_fold)

            fold_record = {
                "fold_index": fold.get("fold_index", len(fold_summaries)),
                "train_samples": len(train_df),
                "test_samples": len(test_df),
                "brier": round(bs, 6),
                "brier_score": round(bs, 6),
                "log_loss": round(ll, 6),
                "ece": round(ece, 6),
                "roi": round(roi, 6) if roi is not None else None,
                "clv": round(clv, 6) if clv is not None else None,
                "max_drawdown_units": dd["max_drawdown_units"],
                "pnl": round(float(np.sum(pnl_fold)), 4),
            }
            fold_summaries.append(fold_record)

            all_y_true.extend(y_test)
            all_y_prob.extend(cal_test_probs)
            all_pnl.extend(pnl_fold)
            if clv is not None:
                all_clv.append(clv)

        if not fold_summaries:
            return {
                "mean_brier": 0.0,
                "std_brier": 0.0,
                "mean_log_loss": 0.0,
                "std_log_loss": 0.0,
                "mean_ece": 0.0,
                "overall_roi": 0.0,
                "mean_clv": 0.0,
                "max_drawdown_units": 0.0,
                "max_drawdown_pct": 0.0,
                "total_predictions": 0,
                "folds": folds,
            }

        # Overall pooled metrics
        arr_y_true = np.asarray(all_y_true)
        arr_y_prob = np.asarray(all_y_prob)
        arr_pnl = np.asarray(all_pnl)

        briers = [f["brier"] for f in fold_summaries]
        log_losses = [f["log_loss"] for f in fold_summaries]
        eces = [f["ece"] for f in fold_summaries]

        overall_dd = self.metrics_engine.maximum_drawdown(arr_pnl)

        return {
            "mean_brier": round(float(np.mean(briers)), 6),
            "std_brier": round(float(np.std(briers)), 6),
            "mean_log_loss": round(float(np.mean(log_losses)), 6),
            "std_log_loss": round(float(np.std(log_losses)), 6),
            "mean_ece": round(float(np.mean(eces)), 6),
            "overall_roi": round(float(self.metrics_engine.flat_staking_roi(arr_pnl)), 6) if len(arr_pnl) > 0 else None,
            "mean_clv": round(float(np.mean(all_clv)), 6) if all_clv else None,
            "max_drawdown_units": overall_dd["max_drawdown_units"],
            "max_drawdown_pct": overall_dd["max_drawdown_pct"],
            "total_predictions": len(arr_y_true),
            "folds": fold_summaries,
            "_raw_predictions": {
                "y_true": arr_y_true.tolist(),
                "y_prob": arr_y_prob.tolist(),
            },
        }

    def _fit_model(self, model: Any, train_df: pd.DataFrame, target_col: str) -> None:
        """Internal adapter to fit different model types."""
        # 1. Standard scikit-learn classifier
        if hasattr(model, "fit"):
            feature_cols = [c for c in train_df.columns if c not in (target_col, "_parsed_date", "date", "match_date", "id", "match_id")]
            X = train_df[feature_cols].select_dtypes(include=[np.number]).fillna(0.0)
            y = train_df[target_col].values
            if len(feature_cols) > 0 and len(X.columns) > 0:
                try:
                    model.fit(X, y)
                    return
                except TypeError:
                    pass

        # 2. Dixon-Coles model
        if hasattr(model, "fit_historical"):
            matches = train_df.to_dict(orient="records")
            model.fit_historical(matches)
            return

        # 3. EloSystem
        if hasattr(model, "bulk_update_from_history"):
            matches = train_df.to_dict(orient="records")
            model.bulk_update_from_history(matches)
            return

    def _predict_model(self, model: Any, test_df: pd.DataFrame) -> np.ndarray:
        """Internal adapter to generate win probabilities for test samples."""
        N = len(test_df)
        if hasattr(model, "predict_proba"):
            feature_cols = [c for c in test_df.columns if c not in ("outcome", "target", "_parsed_date", "date", "match_date", "id", "match_id")]
            X = test_df[feature_cols].select_dtypes(include=[np.number]).fillna(0.0)
            if len(X.columns) > 0:
                probs = model.predict_proba(X)
                if probs.ndim == 2:
                    return probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
                return probs

        if hasattr(model, "predict_1x2"):
            # Predict match 1X2 using Dixon-Coles or Elo
            probs = []
            for _, row in test_df.iterrows():
                h_id = row.get("home_team_id") or row.get("home_id") or row.get("home_team", 0)
                a_id = row.get("away_team_id") or row.get("away_id") or row.get("away_team", 1)
                p_h, p_d, p_a = model.predict_1x2(h_id, a_id)
                probs.append(p_h)
            return np.array(probs, dtype=float)

        if callable(model):
            return np.asarray(model(test_df), dtype=float)

        # Baseline fallback
        return np.full(N, 0.5)

    def compare_models(
        self,
        champion_metrics: Dict[str, Any],
        challenger_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Objective Champion vs Challenger comparison using Diebold-Mariano test.
        """
        champ_preds = champion_metrics.get("_raw_predictions", {})
        chal_preds = challenger_metrics.get("_raw_predictions", {})

        if "y_true" in champ_preds and "y_prob" in champ_preds and "y_prob" in chal_preds:
            y_t = np.asarray(champ_preds["y_true"])
            p_champ = np.asarray(champ_preds["y_prob"])
            p_chal = np.asarray(chal_preds["y_prob"])

            cmp_result = self.comparator.compare(y_t, p_champ, p_chal)
            winner = "challenger" if cmp_result.recommendation == "PROMOTE" else "champion"
            return {
                "winner": winner,
                "recommendation": cmp_result.recommendation,
                "p_value": cmp_result.diebold_mariano_p_value,
                "dm_stat": cmp_result.diebold_mariano_stat,
                "brier_reduction": cmp_result.brier_reduction,
                "details": cmp_result.to_dict(),
            }

        # Without paired out-of-sample predictions, a model comparison cannot
        # calculate a valid statistical test. Never fabricate a p-value or winner.
        sample_size = int(challenger_metrics.get("total_predictions", 0))
        return {
            "winner": None,
            "recommendation": "INSUFFICIENT_DATA",
            "p_value": None,
            "details": {
                "sample_size": sample_size,
                "reason": "Paired raw out-of-sample predictions are required for objective model comparison.",
            },
        }


def run_full_backtest(
    data_path: str,
    leagues: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run a real walk-forward benchmark from an external historical dataset.

    Synthetic outcomes are intentionally forbidden here. Tests may construct
    in-memory fixtures, but the production CLI requires a supplied dataset.
    """
    if not data_path:
        raise ValueError("A real historical dataset path is required; synthetic fallback is disabled.")

    path = str(data_path)
    if path.lower().endswith((".parquet", ".pq")):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    if leagues and "league" in df.columns:
        df = df[df["league"].isin(leagues)].copy()

    if df.empty:
        return {
            "status": "insufficient_data",
            "reason": "Historical dataset contains no usable rows after filtering.",
            "total_predictions": 0,
        }

    validator = WalkForwardValidator(
        initial_train_months=24,
        calibration_months=3,
        test_months=1,
        step_months=1,
        calibration_method="isotonic",
    )

    from sklearn.linear_model import LogisticRegression

    results = validator.validate_model(
        model_factory=lambda: LogisticRegression(C=0.1, max_iter=1000),
        features=df,
        target_col="outcome",
        date_col="date" if "date" in df.columns else "kickoff_utc",
    )
    results["status"] = "success"
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Walk-Forward Historical Replay Backtester")
    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to real historical CSV/Parquet data; synthetic fallback is disabled.",
    )
    parser.add_argument(
        "--leagues",
        type=str,
        default="",
        help="Optional comma-separated league filter.",
    )
    args = parser.parse_args()

    target_leagues = [lg.strip() for lg in args.leagues.split(",") if lg.strip()]
    result = run_full_backtest(args.data_path, target_leagues or None)
    print(result)
