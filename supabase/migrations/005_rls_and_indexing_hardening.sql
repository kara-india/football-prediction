-- ============================================================
-- MIGRATION 005: RLS POLICY HARDENING & INDEX OPTIMIZATION
-- 1. Restricts all public/client write privileges to protect
--    prediction IP, paper bets, model configurations, and
--    historical training datasets from unauthorized tampering.
-- 2. Service role retains full bypass privileges for backend
--    Python workers and internal pipeline tasks.
-- 3. Adds high-performance B-tree indexes for all foreign keys
--    and temporal analytical query joins.
-- ============================================================

-- ------------------------------------------------------------
-- SECTION 1: HISTORICAL MATCHES RLS HARDENING
-- Revoke anonymous and client insert/update/delete on historical dataset
-- ------------------------------------------------------------
DROP POLICY IF EXISTS "anon_insert_historical_matches" ON public.historical_matches;
DROP POLICY IF EXISTS "anon_update_historical_matches" ON public.historical_matches;
DROP POLICY IF EXISTS "auth_all_historical_matches" ON public.historical_matches;

-- Ensure read-only access for both anon and authenticated users
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'historical_matches' AND policyname = 'anon_read_historical_matches'
    ) THEN
        CREATE POLICY "anon_read_historical_matches" 
            ON public.historical_matches FOR SELECT TO anon USING (true);
    END IF;
END $$;

DROP POLICY IF EXISTS "auth_read_historical_matches" ON public.historical_matches;
CREATE POLICY "auth_read_historical_matches" 
    ON public.historical_matches FOR SELECT TO authenticated USING (true);

-- ------------------------------------------------------------
-- SECTION 2: SENSITIVE TABLES RLS HARDENING
-- Replace permissive "Auth full access" (FOR ALL) policies with
-- read-only (FOR SELECT) for authenticated clients.
-- Service role key automatically bypasses RLS for write operations.
-- ------------------------------------------------------------

-- Model Predictions
DROP POLICY IF EXISTS "Auth full access model_predictions" ON public.model_predictions;
DROP POLICY IF EXISTS "auth_read_model_predictions" ON public.model_predictions;
DROP POLICY IF EXISTS "anon_read_model_predictions" ON public.model_predictions;
CREATE POLICY "anon_read_model_predictions" 
    ON public.model_predictions FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_model_predictions" 
    ON public.model_predictions FOR SELECT TO authenticated USING (true);

-- Prediction Results & Errors
DROP POLICY IF EXISTS "Auth full access prediction_results" ON public.prediction_results;
DROP POLICY IF EXISTS "auth_read_prediction_results" ON public.prediction_results;
CREATE POLICY "auth_read_prediction_results" 
    ON public.prediction_results FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access prediction_errors" ON public.prediction_errors;
DROP POLICY IF EXISTS "auth_read_prediction_errors" ON public.prediction_errors;
CREATE POLICY "auth_read_prediction_errors" 
    ON public.prediction_errors FOR SELECT TO authenticated USING (true);

-- Paper Bets & Settlements
DROP POLICY IF EXISTS "Auth full access paper_bets" ON public.paper_bets;
DROP POLICY IF EXISTS "auth_read_paper_bets" ON public.paper_bets;
DROP POLICY IF EXISTS "anon_read_paper_bets" ON public.paper_bets;
CREATE POLICY "anon_read_paper_bets" 
    ON public.paper_bets FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_paper_bets" 
    ON public.paper_bets FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access paper_bet_settlements" ON public.paper_bet_settlements;
DROP POLICY IF EXISTS "auth_read_paper_bet_settlements" ON public.paper_bet_settlements;
CREATE POLICY "auth_read_paper_bet_settlements" 
    ON public.paper_bet_settlements FOR SELECT TO authenticated USING (true);

-- Learning Runs, Metrics & Calibration Bins
DROP POLICY IF EXISTS "Auth full access learning_runs" ON public.learning_runs;
DROP POLICY IF EXISTS "auth_read_learning_runs" ON public.learning_runs;
CREATE POLICY "auth_read_learning_runs" 
    ON public.learning_runs FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access model_metrics" ON public.model_metrics;
DROP POLICY IF EXISTS "auth_read_model_metrics" ON public.model_metrics;
CREATE POLICY "auth_read_model_metrics" 
    ON public.model_metrics FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access calibration_bins" ON public.calibration_bins;
DROP POLICY IF EXISTS "auth_read_calibration_bins" ON public.calibration_bins;
CREATE POLICY "auth_read_calibration_bins" 
    ON public.calibration_bins FOR SELECT TO authenticated USING (true);

-- Model & Calibration Versions
DROP POLICY IF EXISTS "Auth full access model_versions" ON public.model_versions;
DROP POLICY IF EXISTS "auth_read_model_versions" ON public.model_versions;
CREATE POLICY "auth_read_model_versions" 
    ON public.model_versions FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access calibration_versions" ON public.calibration_versions;
DROP POLICY IF EXISTS "auth_read_calibration_versions" ON public.calibration_versions;
CREATE POLICY "auth_read_calibration_versions" 
    ON public.calibration_versions FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access prediction_models" ON public.prediction_models;
DROP POLICY IF EXISTS "auth_read_prediction_models" ON public.prediction_models;
CREATE POLICY "auth_read_prediction_models" 
    ON public.prediction_models FOR SELECT TO authenticated USING (true);

-- Feature & Entity Snapshots
DROP POLICY IF EXISTS "Auth full access feature_snapshots" ON public.feature_snapshots;
DROP POLICY IF EXISTS "auth_read_feature_snapshots" ON public.feature_snapshots;
CREATE POLICY "auth_read_feature_snapshots" 
    ON public.feature_snapshots FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access team_snapshots" ON public.team_snapshots;
DROP POLICY IF EXISTS "auth_read_team_snapshots" ON public.team_snapshots;
CREATE POLICY "auth_read_team_snapshots" 
    ON public.team_snapshots FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access player_snapshots" ON public.player_snapshots;
DROP POLICY IF EXISTS "auth_read_player_snapshots" ON public.player_snapshots;
CREATE POLICY "auth_read_player_snapshots" 
    ON public.player_snapshots FOR SELECT TO authenticated USING (true);

-- Operational Tracking: Worker Runs & Provider Usage
DROP POLICY IF EXISTS "Auth full access worker_runs" ON public.worker_runs;
DROP POLICY IF EXISTS "auth_read_worker_runs" ON public.worker_runs;
CREATE POLICY "auth_read_worker_runs" 
    ON public.worker_runs FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access provider_usage" ON public.provider_usage;
DROP POLICY IF EXISTS "auth_read_provider_usage" ON public.provider_usage;
CREATE POLICY "auth_read_provider_usage" 
    ON public.provider_usage FOR SELECT TO authenticated USING (true);

-- Engine Settings
DROP POLICY IF EXISTS "Auth full access engine_settings" ON public.engine_settings;
DROP POLICY IF EXISTS "auth_read_engine_settings" ON public.engine_settings;
CREATE POLICY "auth_read_engine_settings" 
    ON public.engine_settings FOR SELECT TO authenticated USING (true);

-- Fixtures & Core Domain Data (Read-only for authenticated & anon)
DROP POLICY IF EXISTS "Auth full access competitions" ON public.competitions;
CREATE POLICY "auth_read_competitions" ON public.competitions FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access teams" ON public.teams;
CREATE POLICY "auth_read_teams" ON public.teams FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access players" ON public.players;
CREATE POLICY "auth_read_players" ON public.players FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access matches" ON public.matches;
CREATE POLICY "auth_read_matches" ON public.matches FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access lineups" ON public.lineups;
DROP POLICY IF EXISTS "anon_read_lineups" ON public.lineups;
CREATE POLICY "anon_read_lineups" ON public.lineups FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_lineups" ON public.lineups FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access match_events" ON public.match_events;
DROP POLICY IF EXISTS "anon_read_match_events" ON public.match_events;
CREATE POLICY "anon_read_match_events" ON public.match_events FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_match_events" ON public.match_events FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access odds_snapshots" ON public.odds_snapshots;
DROP POLICY IF EXISTS "anon_read_odds_snapshots" ON public.odds_snapshots;
CREATE POLICY "anon_read_odds_snapshots" ON public.odds_snapshots FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_odds_snapshots" ON public.odds_snapshots FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access odds_providers" ON public.odds_providers;
DROP POLICY IF EXISTS "anon_read_odds_providers" ON public.odds_providers;
CREATE POLICY "anon_read_odds_providers" ON public.odds_providers FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_odds_providers" ON public.odds_providers FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access market_definitions" ON public.market_definitions;
CREATE POLICY "auth_read_market_definitions" ON public.market_definitions FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Auth full access market_outcomes" ON public.market_outcomes;
DROP POLICY IF EXISTS "anon_read_market_outcomes" ON public.market_outcomes;
CREATE POLICY "anon_read_market_outcomes" ON public.market_outcomes FOR SELECT TO anon USING (true);
CREATE POLICY "auth_read_market_outcomes" ON public.market_outcomes FOR SELECT TO authenticated USING (true);

-- ------------------------------------------------------------
-- SECTION 3: FOREIGN KEY & TEMPORAL QUERY INDEXING
-- Optimize join performance and analytical scans
-- ------------------------------------------------------------

-- Matches Foreign Keys and Kickoff Filter
CREATE INDEX IF NOT EXISTS idx_matches_competition_id ON public.matches(competition_id);
CREATE INDEX IF NOT EXISTS idx_matches_home_team_id ON public.matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team_id ON public.matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_kickoff_utc ON public.matches(kickoff_utc);

-- Lineups & Events
CREATE INDEX IF NOT EXISTS idx_lineups_match_id ON public.lineups(match_id);
CREATE INDEX IF NOT EXISTS idx_lineups_player_id ON public.lineups(player_id);
CREATE INDEX IF NOT EXISTS idx_match_events_match_id ON public.match_events(match_id);

-- Odds Snapshots by Match, Market, and Timestamp
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_match_mkt_source 
    ON public.odds_snapshots(match_id, canonical_market, source_timestamp);

-- Model Predictions by Match and Market
CREATE INDEX IF NOT EXISTS idx_model_predictions_match_market 
    ON public.model_predictions(match_id, market);

-- Paper Bets by Prediction and Status
CREATE INDEX IF NOT EXISTS idx_paper_bets_prediction_status 
    ON public.paper_bets(prediction_id, status);

-- Historical Matches Fast Filtering
CREATE INDEX IF NOT EXISTS idx_historical_matches_date_league 
    ON public.historical_matches(match_date DESC, league_code);

-- ------------------------------------------------------------
-- SECTION 4: RECORD MIGRATION COMPLETION
-- ------------------------------------------------------------
INSERT INTO public.schema_migrations (version, description, applied_at)
VALUES ('005', 'RLS policy hardening and foreign key indexing optimization', NOW())
ON CONFLICT (version) DO NOTHING;
