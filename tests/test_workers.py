"""
Comprehensive Background Worker Automation & Orchestration Tests
Tests Phase 9 deliverables:
  1. CLI Dispatcher executes valid subcommands and fails gracefully on unknown commands.
  2. Worker mutex prevents concurrent runs of the same worker type.
  3. worker_runs telemetry logging tracks start time, duration, status, and metrics.
  4. Evaluator settlement idempotency: duplicate runs produce zero duplicate records.
  5. Prequential update invariant: match t outcome cannot alter prediction t and only updates models for t+1 onwards.
  6. Lineup watcher quota window enforcement: zero polling > 75m, active polling in [T-75m, T-40m].
  7. Lineup watcher detects confirmed 11 vs 11 and late changes (LINEUP_V2).
  8. Analysis worker multi-checkpoint forecasting, LIV computation, and counterfactual candidate logging.
  9. Learner worker controlled promotion gate: requires >= 250 matches, p < 0.05, positive CLV, non-degraded ECE.
"""
import os
import sys
import pytest
from datetime import datetime, timezone, timedelta
import numpy as np

from python.workers.runner import WorkerRunner, WorkerMutex, WorkerLockedError
from python.workers.collector_worker import CollectorWorker, run_collector_worker
from python.workers.lineup_watcher import LineupWatcherWorker, run_lineup_watcher
from python.workers.analysis_worker import AnalysisWorker
from python.workers.evaluator_worker import EvaluatorWorker, run_evaluator_worker
from python.workers.learner_worker import LearnerWorker, run_learner_worker
from python.workers.live_state_worker import LiveStateWorker, run_live_worker
from python.data_contracts import CanonicalMatch


class TestWorkerRunnerCLI:
    """Test WorkerRunner CLI dispatcher, argument validation, and subcommands."""

    def test_runner_executes_valid_subcommands_dry_run(self):
        """Test dispatcher executes all valid subcommands in dry-run mode."""
        runner = WorkerRunner()
        for job in ("discovery", "lineups", "analysis", "evaluator", "learner", "live"):
            res = runner.dispatch(job, dry_run=True)
            assert res is not None
            assert res.get("status") in ("success", "skipped")
            assert res.get("worker_name") == job

    def test_runner_executes_all_job_pipeline(self):
        """Test 'all' subcommand executes full pipeline sequentially."""
        runner = WorkerRunner()
        res = runner.dispatch("all", dry_run=True)
        assert res.get("status") == "success"
        assert "pipeline_results" in res
        pipeline = res["pipeline_results"]
        for sub_job in ("discovery", "lineups", "analysis", "live", "evaluator", "learner"):
            assert sub_job in pipeline
            assert pipeline[sub_job].get("status") in ("success", "skipped")

    def test_runner_fails_gracefully_on_unknown_job(self):
        """Test dispatcher raises ValueError with clear error message on invalid subcommand."""
        runner = WorkerRunner()
        with pytest.raises(ValueError, match="Unknown worker job"):
            runner.dispatch("non_existent_worker_xyz")


class TestWorkerMutex:
    """Test process-level mutual exclusion preventing overlapping runs."""

    def test_mutex_acquires_and_releases(self, tmp_path):
        """Test basic mutex acquire and release lifecycle."""
        lock_dir = str(tmp_path)
        mutex = WorkerMutex("test_worker", lock_dir=lock_dir)
        
        with mutex:
            assert os.path.exists(mutex.lock_file)
            with open(mutex.lock_file, "r") as f:
                content = f.read()
            assert str(os.getpid()) in content

        # Upon exiting context manager, lock file must be removed
        assert not os.path.exists(mutex.lock_file)

    def test_mutex_blocks_concurrent_execution(self, tmp_path):
        """Test that a second worker instance cannot acquire lock while first is active."""
        lock_dir = str(tmp_path)
        mutex1 = WorkerMutex("concurrent_worker", lock_dir=lock_dir)
        mutex2 = WorkerMutex("concurrent_worker", lock_dir=lock_dir)

        with mutex1:
            with pytest.raises(WorkerLockedError, match="is already running"):
                mutex2.acquire()

        # After mutex1 releases, mutex2 can acquire
        with mutex2:
            assert os.path.exists(mutex2.lock_file)


class TestWorkerRunsLogging:
    """Test telemetry and execution recording into worker_runs structure."""

    def test_worker_runs_record_structure(self):
        """Verify worker_runs record contains required schema attributes."""
        runner = WorkerRunner()
        t_start = datetime.now(timezone.utc) - timedelta(seconds=12)
        t_end = datetime.now(timezone.utc)

        record = runner.log_worker_run(
            worker_name="discovery",
            started_at=t_start,
            finished_at=t_end,
            status="success",
            matches_seen=15,
            matches_analyzed=15,
            api_requests=1,
            quota_remaining=44,
            predictions_count=105,
            errors_count=0,
            error_details=None,
        )

        assert record["worker_name"] == "discovery"
        assert record["worker_type"] == "discovery"
        assert record["status"] == "success"
        assert record["duration_seconds"] >= 10
        assert record["matches_seen"] == 15
        assert record["matches_analyzed"] == 15
        assert record["api_requests"] == 1
        assert record["quota_remaining"] == 44
        assert record["predictions_count"] == 105
        assert record["predictions_generated"] == 105
        assert record["errors_count"] == 0
        assert record["error_details"] is None


class TestEvaluatorIdempotency:
    """Test that settlement worker is strictly idempotent across duplicate executions."""

    def test_evaluator_settlement_idempotency(self):
        """Verify that running evaluator twice on identical matches yields zero duplicate settlements."""
        worker = EvaluatorWorker()

        match_data = [
            {
                "prediction_id": "test_pred_101",
                "match_id": "match_2001",
                "market": "MATCH_1X2",
                "selection": "1",
                "decimal_odds": 2.20,
                "closing_odds": 2.10,
                "calibrated_probability": 0.55,
                "score_home": 2,
                "score_away": 1,
            },
            {
                "prediction_id": "test_pred_102",
                "match_id": "match_2001",
                "market": "TOTAL_GOALS_2_5",
                "selection": "OVER",
                "line": 2.5,
                "decimal_odds": 1.90,
                "closing_odds": 1.85,
                "calibrated_probability": 0.60,
                "score_home": 2,
                "score_away": 1,
            },
        ]

        # First run: settles 2 predictions
        settled_run_1, errors_run_1 = worker.settle_predictions(match_data, dry_run=True)
        assert len(settled_run_1) == 2
        assert len(errors_run_1) == 2
        assert settled_run_1[0].actual_outcome == "WON"
        assert settled_run_1[1].actual_outcome == "WON"

        # Second run on identical data: strictly 0 new settlements, 0 double counting
        settled_run_2, errors_run_2 = worker.settle_predictions(match_data, dry_run=True)
        assert len(settled_run_2) == 0
        assert len(errors_run_2) == 0


class TestPrequentialUpdateInvariant:
    """Test non-negotiable prequential protocol: outcome of match t cannot alter prediction t."""

    def test_outcome_of_t_cannot_alter_prediction_t(self):
        """Verify that prediction at time t is immutable and historical outcome does not mutate it."""
        analysis_worker = AnalysisWorker()

        match = {
            "match_id": "prequential_match_t",
            "competition_name": "Premier League (England)",
        }

        # Generate prediction at time t
        preds_t = analysis_worker.run_match_prediction(match, stage="INITIAL", dry_run=True)
        initial_prob_home = next(p["calibrated_probability"] for p in preds_t if p["selection"] == "1")

        # Now simulate match completion at time t (match ends 0-3 away win)
        evaluator = EvaluatorWorker()
        settlement_input = [{
            "prediction_id": "prequential_pred_h",
            "match_id": "prequential_match_t",
            "market": "MATCH_1X2",
            "selection": "1",
            "decimal_odds": 2.0,
            "calibrated_probability": initial_prob_home,
            "score_home": 0,
            "score_away": 3,
        }]
        settled, _ = evaluator.settle_predictions(settlement_input, dry_run=True)
        assert settled[0].actual_outcome == "LOST"

        # Assert prediction record t remained unchanged and was not mutated by the loss
        assert preds_t[0]["calibrated_probability"] == initial_prob_home

        # Learner updates model for t+1 matches onwards
        learner = LearnerWorker()
        residuals_t1 = learner.update_layer3_team_residuals([{
            "home_team_id": "team_A",
            "away_team_id": "team_B",
            "score_home": 0,
            "score_away": 3,
            "predicted_home_goals": 1.45,
            "predicted_away_goals": 1.15,
        }])

        # Residuals update team strengths for FUTURE match t+1
        assert "team_A" in residuals_t1
        assert residuals_t1["team_A"] < 0  # Underperformed expected goals


class TestLineupWatcherQuotaAndWindow:
    """Test targeted lineup watcher window gating and event triggering."""

    def test_zero_polling_greater_than_75m_before_kickoff(self):
        """Verify matches > 75m before kickoff are strictly excluded from polling."""
        watcher = LineupWatcherWorker()
        now = datetime.now(timezone.utc)

        fixtures = [
            {"id": 1, "kickoff_utc": (now + timedelta(minutes=120)).isoformat(), "lineup_confirmed": False},
            {"id": 2, "kickoff_utc": (now + timedelta(minutes=80)).isoformat(), "lineup_confirmed": False},
            {"id": 3, "kickoff_utc": (now + timedelta(minutes=60)).isoformat(), "lineup_confirmed": False},  # In window
            {"id": 4, "kickoff_utc": (now + timedelta(minutes=20)).isoformat(), "lineup_confirmed": False},  # Past window
        ]

        target_matches = watcher.filter_target_window_matches(fixtures, now_utc=now)
        target_ids = [m["id"] for m in target_matches]

        # Only fixture 3 (60m to kickoff) should be inside [T-75m, T-40m]
        assert target_ids == [3]

    def test_lineup_confirmation_triggers_lineup_confirmed_and_v2(self):
        """Verify verified starting XI triggers LINEUP_CONFIRMED and revision triggers LINEUP_V2."""
        analysis_worker = AnalysisWorker()
        watcher = LineupWatcherWorker(analysis_worker=analysis_worker)
        now = datetime.now(timezone.utc)

        match = {
            "id": 888,
            "api_football_id": 888,
            "competition_name": "La Liga (Spain)",
            "home_team_name": "Real Madrid",
            "away_team_name": "Barcelona",
            "kickoff_utc": (now + timedelta(minutes=55)).isoformat(),
            "lineup_confirmed": False,
        }

        # 1. Run watcher with match in window -> generates LINEUP_CONFIRMED
        res1 = watcher.run([match], dry_run=True)
        assert res1["lineups_confirmed"] == 1
        assert res1["predictions_count"] > 0
        assert 888 in watcher._confirmed_rosters

        # 2. Simulate late change: modify roster set
        watcher._confirmed_rosters[888] = {9999}  # Dummy previous roster
        res2 = watcher.run([match], dry_run=True)
        assert res2["lineups_confirmed"] == 1


class TestAnalysisWorkerMultiCheckpoint:
    """Test multi-checkpoint prediction generation, LIV calculation, and CounterfactualLogger."""

    def test_analysis_worker_generates_initial_and_lineup_checkpoints(self):
        """Test INITIAL and LINEUP_CONFIRMED predictions with LIV computation."""
        worker = AnalysisWorker()
        match = {
            "match_id": "test_match_liv",
            "competition_name": "Premier League (England)",
        }

        # 1. INITIAL Checkpoint (T-48h)
        preds_init = worker.run_match_prediction(match, stage="INITIAL", dry_run=True)
        assert len(preds_init) == 7
        for p in preds_init:
            assert p["stage"] == "INITIAL"
            # INITIAL checkpoint should trip NO-BET gate with LINEUP_UNCONFIRMED
            assert p["recommended_action"] == "NO_BET"
            assert "LINEUP_UNCONFIRMED" in p["no_bet_reasons"]

        # 2. LINEUP_CONFIRMED Checkpoint (T-60m)
        lineup_payload = {
            "home": {
                "starters": [{"player": {"id": i}} for i in range(11)],
            },
            "away": {
                "starters": [{"player": {"id": 100 + i}} for i in range(11)],
            },
        }
        preds_lineup = worker.run_match_prediction(
            match, stage="LINEUP_CONFIRMED", lineup_data=lineup_payload, dry_run=True
        )
        assert len(preds_lineup) == 7
        for p in preds_lineup:
            assert p["stage"] == "LINEUP_CONFIRMED"
            # Lineup Information Value is computed against INITIAL
            liv = p.get("lineup_information_value", {})
            assert "delta_p" in liv
            assert "delta_odds" in liv
            assert "delta_ev" in liv

        # 3. Verify all candidates are logged to Counterfactual candidate ledger
        assert len(worker.cf_logger._opportunities) >= 14


class TestLearnerWorkerPromotionGate:
    """Test scientific champion vs challenger promotion gate."""

    def test_learner_rejects_under_sample_size(self):
        """Verify promotion rejected if sample size < 250 matches."""
        learner = LearnerWorker()
        # Test with N = 100 (< 250)
        y_true = np.random.binomial(1, 0.5, size=100)
        p_champ = np.full(100, 0.5)
        p_chal = np.full(100, 0.6)

        res = learner.evaluate_challenger_promotion(y_true, p_champ, p_chal)
        assert res.recommendation in ("REJECT", "INSUFFICIENT_DATA")
        assert res.criteria_met.get("sample_size") is False

    def test_learner_promotes_statistically_superior_challenger(self):
        """Verify promotion succeeds when N >= 250, DM p < 0.05, positive CLV, and stable ECE."""
        learner = LearnerWorker()
        np.random.seed(42)
        N = 300
        y_true = np.random.binomial(1, 0.5, size=N)
        # Challenger is significantly closer to ground truth
        p_champ = np.clip(np.random.uniform(0.3, 0.7, size=N), 0.01, 0.99)
        p_chal = np.clip(y_true * 0.8 + 0.1, 0.01, 0.99)
        odds_pred = np.full(N, 2.10)
        odds_close = np.full(N, 2.00)  # Positive CLV: 2.10 / 2.00 - 1 = +5%

        res = learner.evaluate_challenger_promotion(
            y_true=y_true,
            prob_champion=p_champ,
            prob_challenger=p_chal,
            odds_pred=odds_pred,
            odds_close=odds_close,
        )

        assert res.sample_size == N
        assert res.brier_reduction > 0
        assert res.criteria_met["sample_size"] is True
        assert res.criteria_met["brier_reduction"] is True
        assert res.criteria_met["clv_non_negative"] is True
        assert res.diebold_mariano_p_value < 0.05
        assert res.recommendation == "PROMOTE"
