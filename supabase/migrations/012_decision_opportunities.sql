-- supabase/migrations/012_decision_opportunities.sql
-- Persists every prediction/decision opportunity for unbiased learning

CREATE TABLE IF NOT EXISTS decision_opportunities (
    id BIGSERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    prediction_stage TEXT NOT NULL CHECK (prediction_stage IN ('INITIAL', 'LINEUP_CONFIRMED', 'LINEUP_V2', 'FINAL_PREMATCH', 'LIVE')),
    market TEXT NOT NULL,                  -- 'home_win', 'draw', 'away_win', 'over_25', etc.
    selection TEXT NOT NULL,               -- '1', 'X', '2', 'over', 'under', etc.

    -- Model outputs
    raw_probability DOUBLE PRECISION NOT NULL CHECK (raw_probability BETWEEN 0 AND 1),
    calibrated_probability DOUBLE PRECISION CHECK (calibrated_probability BETWEEN 0 AND 1),
    model_version TEXT NOT NULL,
    feature_snapshot_id TEXT,              -- hash of feature vector used
    simulation_count INTEGER,
    simulation_std_error DOUBLE PRECISION,

    -- Market data at prediction time
    provider_odds DOUBLE PRECISION,        -- decimal odds if available, NULL if not
    implied_probability DOUBLE PRECISION,  -- 1/odds, NULL if no odds
    devigged_probability DOUBLE PRECISION,
    overround DOUBLE PRECISION,
    odds_freshness_seconds INTEGER,

    -- Gate outcomes
    expected_value DOUBLE PRECISION,
    no_bet_reasons TEXT[] DEFAULT ARRAY[]::TEXT[],
    gate_decision TEXT NOT NULL CHECK (gate_decision IN ('BET_CANDIDATE', 'NO_BET', 'ABSTAIN')),

    -- Behavior policy (for offline evaluation)
    behavior_policy_name TEXT NOT NULL DEFAULT 'static_no_bet_gate',
    behavior_policy_action TEXT,           -- action taken by production policy
    behavior_propensity DOUBLE PRECISION,  -- P(action | context) for IPS

    -- Outcome (filled post-match)
    actual_outcome INTEGER,                -- 1 if selection won, 0 if lost, NULL until settled
    settled_at TIMESTAMPTZ,
    settlement_source TEXT,               -- 'api_football_result'

    -- Timing
    prediction_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    kickoff_at TIMESTAMPTZ,
    information_cutoff_at TIMESTAMPTZ,    -- point-in-time cutoff for features

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dop_fixture ON decision_opportunities(fixture_id);
CREATE INDEX IF NOT EXISTS idx_dop_stage ON decision_opportunities(prediction_stage);
CREATE INDEX IF NOT EXISTS idx_dop_unsettled ON decision_opportunities(fixture_id) WHERE actual_outcome IS NULL;
CREATE INDEX IF NOT EXISTS idx_dop_market ON decision_opportunities(market, selection);
CREATE INDEX IF NOT EXISTS idx_dop_model_version ON decision_opportunities(model_version);

ALTER TABLE decision_opportunities ENABLE ROW LEVEL SECURITY;
CREATE POLICY dop_service_all ON decision_opportunities FOR ALL TO service_role USING (true);
CREATE POLICY dop_anon_read ON decision_opportunities FOR SELECT TO anon USING (settled_at IS NOT NULL);

COMMENT ON TABLE decision_opportunities IS 'Every prediction opportunity persisted regardless of gate outcome. Essential for unbiased learning — selection bias avoided by logging NO_BET decisions too.';
