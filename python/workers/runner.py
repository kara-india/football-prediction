"""
Unified Background Worker CLI Runner & Orchestrator
Dispatches scheduled jobs:
  - discovery: Runs CollectorWorker for fixture ingestion and INITIAL checkpoint
  - lineups: Runs LineupWatcherWorker for [T-75m, T-40m] team sheet verification
  - analysis: Runs AnalysisWorker multi-checkpoint pipeline
  - evaluator: Runs EvaluatorWorker for post-match settlement and error classification
  - learner: Runs LearnerWorker for online residuals, calibration tracking, and promotion gate
  - live: Runs LiveStateWorker for in-play simulation
  - all: Runs entire pipeline sequentially

Enforces:
  - Cross-platform process mutex (WorkerMutex) preventing concurrent duplicate executions
  - Atomic database logging to Supabase worker_runs
  - Graceful command-line handling and error telemetry
"""
import os
import sys
import json
import logging
import argparse
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from python.adapters.quota_manager import CentralQuotaManager
from python.workers.collector_worker import CollectorWorker
from python.workers.lineup_watcher import LineupWatcherWorker
from python.workers.analysis_worker import AnalysisWorker
from python.workers.evaluator_worker import EvaluatorWorker
from python.workers.learner_worker import LearnerWorker
from python.workers.live_state_worker import LiveStateWorker
from python.workers.retention_pruner import RetentionPruner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("WorkerRunner")


class WorkerLockedError(Exception):
    """Raised when an instance of the requested worker is already active."""
    pass


class WorkerMutex:
    """Cross-platform PID-verified file lock ensuring mutual exclusion."""

    def __init__(self, worker_name: str, lock_dir: Optional[str] = None):
        self.worker_name = worker_name
        self.lock_dir = lock_dir or tempfile.gettempdir()
        self.lock_file = os.path.join(self.lock_dir, f"football_worker_{worker_name}.lock")
        self._acquired = False

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        """Check if process ID is alive."""
        if pid <= 0:
            return False
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if h_proc:
                    kernel32.CloseHandle(h_proc)
                    return True
                return False
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def acquire(self) -> None:
        """Acquire the worker lock or raise WorkerLockedError if already active."""
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    content = f.read().strip()
                if content:
                    existing_pid = int(content.split(":")[0])
                    if self._is_pid_running(existing_pid):
                        raise WorkerLockedError(
                            f"Worker '{self.worker_name}' is already running with PID {existing_pid}."
                        )
            except (ValueError, IOError):
                pass

        # Write current PID and timestamp to lock file
        try:
            with open(self.lock_file, "w") as f:
                f.write(f"{os.getpid()}:{datetime.now(timezone.utc).isoformat()}")
            self._acquired = True
        except Exception as e:
            logger.warning(f"Could not create lock file {self.lock_file}: {e}")

    def release(self) -> None:
        """Release the worker lock."""
        if self._acquired and os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except Exception:
                pass
            self._acquired = False

    def __enter__(self) -> "WorkerMutex":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


class WorkerRunner:
    """Unified orchestrator running background jobs with process locking and DB logging."""

    VALID_JOBS = ("discovery", "lineups", "analysis", "evaluator", "learner", "live", "prune", "all")

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        quota_manager: Optional[CentralQuotaManager] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://qqcxjjkgvqknesrtnwal.supabase.co")
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )
        self.quota_manager = quota_manager or CentralQuotaManager()
        self._last_run_record: Optional[Dict[str, Any]] = None

    def log_worker_run(
        self,
        worker_name: str,
        started_at: datetime,
        finished_at: datetime,
        status: str,
        matches_seen: int = 0,
        matches_analyzed: int = 0,
        api_requests: int = 0,
        quota_remaining: int = 45,
        predictions_count: int = 0,
        errors_count: int = 0,
        error_details: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record worker run execution metadata to Supabase worker_runs."""
        duration_seconds = max(0, int((finished_at - started_at).total_seconds()))

        record = {
            "worker_name": worker_name,
            "worker_type": worker_name,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "completed_at": finished_at.isoformat(),
            "duration_seconds": duration_seconds,
            "status": status,
            "matches_seen": matches_seen,
            "matches_analyzed": matches_analyzed,
            "api_requests": api_requests,
            "quota_remaining": quota_remaining,
            "predictions_count": predictions_count,
            "predictions_generated": predictions_count,
            "errors_count": errors_count,
            "error_details": error_details,
            "errors": [error_details] if error_details else [],
        }

        self._last_run_record = record

        if self.supabase_url and self.supabase_key:
            try:
                import urllib.request
                url = f"{self.supabase_url}/rest/v1/worker_runs"
                payload = json.dumps([record]).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Recorded worker run telemetry for '{worker_name}' to Supabase.")
            except Exception as e:
                logger.warning(f"Could not persist worker_runs record to Supabase: {e}")

        return record

    def dispatch(self, job_name: str, dry_run: bool = False) -> Dict[str, Any]:
        """Dispatch requested worker job under mutex lock and DB logging."""
        norm_job = job_name.lower().strip()
        if norm_job not in self.VALID_JOBS:
            raise ValueError(f"Unknown worker job: '{job_name}'. Valid jobs are: {self.VALID_JOBS}")

        # Execute full sequence if job is 'all'
        if norm_job == "all":
            logger.info("Executing full sequential background worker pipeline...")
            seq_results = {}
            for sub_job in ("discovery", "lineups", "analysis", "live", "evaluator", "learner"):
                seq_results[sub_job] = self.dispatch(sub_job, dry_run=dry_run)
            return {"status": "success", "pipeline_results": seq_results}

        started_at = datetime.now(timezone.utc)
        status = "running"
        matches_seen = 0
        matches_analyzed = 0
        api_requests = 0
        predictions_count = 0
        errors_count = 0
        error_details = None

        logger.info(f"Acquiring mutex lock for worker '{norm_job}'...")
        with WorkerMutex(norm_job):
            try:
                if norm_job == "discovery":
                    worker = CollectorWorker(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                        quota_manager=self.quota_manager,
                    )
                    res = worker.run(dry_run=dry_run)
                    matches_seen = res.get("matches_seen", 0)
                    matches_analyzed = res.get("matches_inserted", 0)
                    predictions_count = res.get("predictions_count", 0)
                    api_requests = res.get("quota_used", 0)
                    status = res.get("status", "success")

                elif norm_job == "lineups":
                    worker = LineupWatcherWorker(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                        quota_manager=self.quota_manager,
                    )
                    res = worker.run(dry_run=dry_run)
                    matches_seen = res.get("matches_seen", 0)
                    matches_analyzed = res.get("matches_in_window", 0)
                    predictions_count = res.get("predictions_count", 0)
                    api_requests = res.get("api_requests", 0)
                    status = res.get("status", "success")

                elif norm_job == "analysis":
                    worker = AnalysisWorker(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                    )
                    res = worker.run(stage="INITIAL", dry_run=dry_run)
                    matches_analyzed = res.get("matches_analyzed", 0)
                    matches_seen = matches_analyzed
                    predictions_count = res.get("predictions_count", 0)
                    status = res.get("status", "success")

                elif norm_job == "evaluator":
                    worker = EvaluatorWorker(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                    )
                    res = worker.run(dry_run=dry_run)
                    matches_analyzed = res.get("matches_evaluated", 0)
                    matches_seen = matches_analyzed
                    predictions_count = res.get("predictions_settled", 0)
                    errors_count = res.get("errors_classified", 0)
                    status = res.get("status", "success")

                elif norm_job == "learner":
                    worker = LearnerWorker(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                    )
                    res = worker.run(dry_run=dry_run)
                    matches_analyzed = res.get("samples_processed", 0)
                    matches_seen = matches_analyzed
                    status = res.get("status", "success")

                elif norm_job == "live":
                    worker = LiveStateWorker(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                    )
                    res = worker.run(dry_run=dry_run)
                    matches_analyzed = res.get("matches_processed", 0)
                    matches_seen = matches_analyzed
                    predictions_count = res.get("snapshots_generated", 0)
                    status = res.get("status", "success")

                elif norm_job == "prune":
                    worker = RetentionPruner(
                        supabase_url=self.supabase_url,
                        supabase_key=self.supabase_key,
                    )
                    res = worker.run(dry_run=dry_run)
                    matches_analyzed = res.get("total_pruned", 0)
                    matches_seen = matches_analyzed
                    status = res.get("status", "success")

            except Exception as e:
                logger.error(f"Worker '{norm_job}' encountered unhandled exception: {e}")
                status = "failed"
                errors_count += 1
                error_details = str(e)
                raise

            finally:
                finished_at = datetime.now(timezone.utc)
                status_dict = self.quota_manager.get_status() if hasattr(self.quota_manager, "get_status") else {}
                quota_remaining = status_dict.get("remaining_worker", 45)
                self.log_worker_run(
                    worker_name=norm_job,
                    started_at=started_at,
                    finished_at=finished_at,
                    status=status,
                    matches_seen=matches_seen,
                    matches_analyzed=matches_analyzed,
                    api_requests=api_requests,
                    quota_remaining=quota_remaining,
                    predictions_count=predictions_count,
                    errors_count=errors_count,
                    error_details=error_details,
                )

        return self._last_run_record or {}


def build_cli_parser() -> argparse.ArgumentParser:
    """Build unified argument parser."""
    parser = argparse.ArgumentParser(
        description="Football Prediction Intelligence Platform — Unified Worker CLI Orchestrator"
    )
    parser.add_argument(
        "job",
        choices=WorkerRunner.VALID_JOBS,
        help="Worker job name to execute: discovery, lineups, analysis, evaluator, learner, live, prune, all",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Execute in simulation mode without consuming external quota or writing to DB",
    )
    return parser


def main():
    """Main CLI entrypoint."""
    parser = build_cli_parser()
    args = parser.parse_args()

    runner = WorkerRunner()
    try:
        result = runner.dispatch(args.job, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("status") in ("success", "skipped") else 1)
    except WorkerLockedError as wle:
        logger.warning(f"Execution halted: {wle}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Fatal error running job '{args.job}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
