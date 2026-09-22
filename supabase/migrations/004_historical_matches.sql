-- ============================================================
-- MIGRATION 004: HISTORICAL MATCHES TABLE (PAST 5 YEARS)
-- Holds football-data.co.uk historical match statistics, shots,
-- cards, and closing market odds for offline model training.
-- ============================================================

CREATE TABLE IF NOT EXISTS historical_matches (
    id BIGSERIAL PRIMARY KEY,
    league_code TEXT NOT NULL,
    league_name TEXT,
    season TEXT NOT NULL,
    match_date DATE NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    fthg INTEGER,
    ftag INTEGER,
    ftr TEXT,
    hthg INTEGER,
    htag INTEGER,
    hs INTEGER,
    as_shots INTEGER,
    hst INTEGER,
    ast INTEGER,
    hf INTEGER,
    af INTEGER,
    hc INTEGER,
    ac INTEGER,
    hy INTEGER,
    ay INTEGER,
    hr INTEGER,
    ar INTEGER,
    b365_h DECIMAL(8,4),
    b365_d DECIMAL(8,4),
    b365_a DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(league_code, season, match_date, home_team, away_team)
);

CREATE INDEX IF NOT EXISTS idx_hist_matches_league_date ON historical_matches(league_code, match_date);
CREATE INDEX IF NOT EXISTS idx_hist_matches_teams ON historical_matches(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_hist_matches_season ON historical_matches(season);

-- Enable RLS & allow public read/write for ingestion
ALTER TABLE historical_matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read_historical_matches" ON historical_matches FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert_historical_matches" ON historical_matches FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_update_historical_matches" ON historical_matches FOR UPDATE TO anon USING (true);
CREATE POLICY "auth_all_historical_matches" ON historical_matches FOR ALL TO authenticated USING (true);
