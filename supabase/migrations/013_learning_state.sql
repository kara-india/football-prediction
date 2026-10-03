-- supabase/migrations/013_learning_state.sql
-- Transactional learning state for online learners

CREATE TABLE IF NOT EXISTS learning_state (
    id BIGSERIAL PRIMARY KEY,
    learner_name TEXT NOT NULL,           -- 'elo_online', 'dixon_coles_challenger', 'calibrator_isotonic'
    learner_version TEXT NOT NULL DEFAULT '1.0',
    state_json JSONB NOT NULL DEFAULT '{}',   -- serialized learner state
    training_sample_count INTEGER NOT NULL DEFAULT 0,
    last_trained_at TIMESTAMPTZ,
    last_fixture_id INTEGER,               -- last fixture that triggered update
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'superseded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(learner_name, learner_version, status)
);

CREATE INDEX IF NOT EXISTS idx_learning_state_name ON learning_state(learner_name, status);

ALTER TABLE learning_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY ls_service_all ON learning_state FOR ALL TO service_role USING (true);
CREATE POLICY ls_anon_read ON learning_state FOR SELECT TO anon USING (status = 'active');

COMMENT ON TABLE learning_state IS 'Durable learner state. Workers read/write transactionally. Restart-safe. Old states archived, not deleted.';
