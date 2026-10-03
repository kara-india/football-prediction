-- supabase/migrations/011_lineup_snapshots.sql
-- Durable lineup snapshot storage for prequential integrity

CREATE TABLE IF NOT EXISTS lineup_snapshots (
    id BIGSERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,           -- API-Football fixture ID
    snapshot_version INTEGER NOT NULL DEFAULT 1,  -- 1 = LINEUP_CONFIRMED, 2+ = LINEUP_V2
    lineup_fingerprint TEXT NOT NULL,      -- SHA-256 hex of sorted starter player IDs
    stage TEXT NOT NULL CHECK (stage IN ('LINEUP_CONFIRMED', 'LINEUP_V2', 'LINEUP_V3')),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    home_team_id INTEGER,
    away_team_id INTEGER,
    home_formation TEXT,
    away_formation TEXT,
    home_starters JSONB NOT NULL DEFAULT '[]',  -- [{player_id, name, position, number}]
    away_starters JSONB NOT NULL DEFAULT '[]',
    home_bench JSONB DEFAULT '[]',
    away_bench JSONB DEFAULT '[]',
    is_immutable BOOLEAN NOT NULL DEFAULT FALSE,  -- set TRUE after match kicks off
    raw_provider_payload JSONB,           -- provider response for audit
    provider_name TEXT NOT NULL DEFAULT 'api_football',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Prevent duplicate snapshots for same fixture+version
    UNIQUE(fixture_id, snapshot_version)
);

CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_fixture ON lineup_snapshots(fixture_id);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_detected ON lineup_snapshots(detected_at);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_fingerprint ON lineup_snapshots(lineup_fingerprint);

-- RLS: service role can write; anon can read confirmed lineups
ALTER TABLE lineup_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY lineup_snapshots_service_write ON lineup_snapshots
    FOR ALL TO service_role USING (true);
CREATE POLICY lineup_snapshots_anon_read ON lineup_snapshots
    FOR SELECT TO anon USING (is_immutable = TRUE);

COMMENT ON TABLE lineup_snapshots IS 'Immutable lineup snapshot ledger. Each confirmed starting XI creates one row. Late changes create new versioned rows. Never overwritten.';
