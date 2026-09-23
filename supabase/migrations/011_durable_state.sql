-- Phase 14: Durable lineup, decision-opportunity, and learning state persistence.
-- Non-destructive: creates new tables only and exposes them to service workers.

CREATE TABLE IF NOT EXISTS public.lineup_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id INTEGER NOT NULL REFERENCES public.matches(id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK (version >= 1),
    lineup_hash TEXT NOT NULL,
    source_timestamp TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    home_formation TEXT,
    away_formation TEXT,
    home_starters JSONB NOT NULL,
    away_starters JSONB NOT NULL,
    is_official BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (match_id, lineup_hash),
    UNIQUE (match_id, version)
);

CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_match_version
    ON public.lineup_snapshots(match_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_detected_at
    ON public.lineup_snapshots(detected_at DESC);

CREATE TABLE IF NOT EXISTS public.decision_opportunities (
    opportunity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id TEXT NOT NULL UNIQUE,
    match_id INTEGER REFERENCES public.matches(id) ON DELETE SET NULL,
    prediction_id BIGINT REFERENCES public.model_predictions(id) ON DELETE SET NULL,
    checkpoint_stage TEXT NOT NULL,
    opportunity_at TIMESTAMPTZ NOT NULL,
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    line NUMERIC,
    decimal_odds NUMERIC,
    fair_probability NUMERIC,
    expected_value NUMERIC,
    value_edge NUMERIC,
    raw_probability NUMERIC,
    calibrated_probability NUMERIC,
    probability_lower NUMERIC,
    probability_upper NUMERIC,
    data_quality_tier TEXT,
    lineup_verified BOOLEAN,
    uncertainty NUMERIC,
    gate_action TEXT NOT NULL,
    gate_reasons TEXT[] NOT NULL DEFAULT '{}',
    available_actions TEXT[] NOT NULL DEFAULT '{}',
    chosen_action TEXT NOT NULL,
    action_propensity NUMERIC,
    action_propensities JSONB,
    context_vector JSONB,
    behavior_policy_version TEXT,
    model_version_id INTEGER REFERENCES public.model_versions(id) ON DELETE SET NULL,
    calibration_version_id INTEGER REFERENCES public.calibration_versions(id) ON DELETE SET NULL,
    feature_snapshot_id BIGINT REFERENCES public.feature_snapshots(id) ON DELETE SET NULL,
    outcome TEXT,
    realized_return NUMERIC,
    counterfactual_return NUMERIC,
    closing_odds NUMERIC,
    clv NUMERIC,
    settled_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_decision_opportunities_match_time
    ON public.decision_opportunities(match_id, opportunity_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_opportunities_market_time
    ON public.decision_opportunities(market, opportunity_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_opportunities_settlement
    ON public.decision_opportunities(settled_at);
CREATE INDEX IF NOT EXISTS idx_decision_opportunities_action
    ON public.decision_opportunities(chosen_action, opportunity_at DESC);

CREATE TABLE IF NOT EXISTS public.learning_state (
    state_key TEXT PRIMARY KEY,
    model_family TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'global',
    state JSONB NOT NULL,
    version BIGINT NOT NULL DEFAULT 1,
    last_observation_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_family, scope)
);

CREATE INDEX IF NOT EXISTS idx_learning_state_family_scope
    ON public.learning_state(model_family, scope);

ALTER TABLE public.lineup_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.decision_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_state ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.lineup_snapshots FROM anon, authenticated;
REVOKE ALL ON public.decision_opportunities FROM anon, authenticated;
REVOKE ALL ON public.learning_state FROM anon, authenticated;

GRANT ALL ON public.lineup_snapshots TO service_role;
GRANT ALL ON public.decision_opportunities TO service_role;
GRANT ALL ON public.learning_state TO service_role;
