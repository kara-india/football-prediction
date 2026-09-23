-- Migration 009: Worker Runs Enhancements
-- Aligns worker_runs table with Phase 9 background worker specification

ALTER TABLE worker_runs
    ADD COLUMN IF NOT EXISTS worker_name TEXT,
    ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS predictions_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS errors_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS error_details TEXT;

CREATE INDEX IF NOT EXISTS idx_worker_runs_name_started ON worker_runs(worker_name, started_at DESC);
