-- Migration 008: RL Policy Runs Table for Contextual Bandit & OPE Tracking
-- Phase 12 - Reinforcement Learning & Contextual Bandit Policy

CREATE TABLE IF NOT EXISTS rl_policy_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_version TEXT NOT NULL,
    training_samples INTEGER NOT NULL,
    mean_reward DOUBLE PRECISION NOT NULL,
    ips_score DOUBLE PRECISION NOT NULL,
    dr_score DOUBLE PRECISION NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rl_policy_runs_created_at ON rl_policy_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rl_policy_runs_policy_version ON rl_policy_runs(policy_version);
