CREATE TABLE competitions (
    id SERIAL PRIMARY KEY,
    league_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    country TEXT,
    type TEXT CHECK (type IN ('league','cup','international')),
    season INTEGER,
    is_enabled BOOLEAN DEFAULT true,
    is_international BOOLEAN DEFAULT false,
    api_football_id INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    short_name TEXT,
    country TEXT,
    founded INTEGER,
    venue_name TEXT,
    venue_capacity INTEGER,
    logo_url TEXT,
    elo_rating DECIMAL(8,2) DEFAULT 1500.0,
    elo_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    firstname TEXT,
    lastname TEXT,
    nationality TEXT,
    date_of_birth DATE,
    position TEXT,
    height TEXT,
    weight TEXT,
    photo_url TEXT,
    current_team_id INTEGER REFERENCES teams(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE NOT NULL,
    competition_id INTEGER REFERENCES competitions(id),
    season INTEGER,
    round TEXT,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    kickoff_utc TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'NS',
    status_short TEXT,
    minute INTEGER,
    added_time INTEGER,
    score_home INTEGER,
    score_away INTEGER,
    halftime_home INTEGER,
    halftime_away INTEGER,
    fulltime_home INTEGER,
    fulltime_away INTEGER,
    venue TEXT,
    referee TEXT,
    lineup_confirmed BOOLEAN DEFAULT false,
    lineup_confirmed_at TIMESTAMPTZ,
    is_eligible BOOLEAN DEFAULT false,
    weather_temp DECIMAL(5,2),
    weather_description TEXT,
    weather_wind DECIMAL(5,2),
    weather_humidity INTEGER,
    last_api_sync TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    is_starter BOOLEAN NOT NULL,
    position TEXT,
    grid_position TEXT,
    jersey_number INTEGER,
    formation TEXT,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(match_id, team_id, player_id)
);

CREATE TABLE match_events (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    minute INTEGER,
    added_time INTEGER,
    event_type TEXT,
    event_detail TEXT,
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    assist_player_id INTEGER REFERENCES players(id),
    comments TEXT,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE team_snapshots (
    id BIGSERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    team_id INTEGER REFERENCES teams(id),
    snapshot_type TEXT,
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    elo_rating DECIMAL(8,2),
    attack_strength DECIMAL(8,4),
    defense_strength DECIMAL(8,4),
    home_advantage DECIMAL(8,4),
    form_ewma DECIMAL(8,4),
    xg_season DECIMAL(8,4),
    xga_season DECIMAL(8,4),
    goals_scored_season INTEGER,
    goals_conceded_season INTEGER,
    avg_goals_scored_5 DECIMAL(8,4),
    avg_goals_conceded_5 DECIMAL(8,4),
    shots_per_game DECIMAL(8,4),
    shots_on_target_per_game DECIMAL(8,4),
    possession_avg DECIMAL(8,4),
    corners_per_game DECIMAL(8,4),
    cards_per_game DECIMAL(8,4),
    fouls_per_game DECIMAL(8,4),
    rest_days INTEGER,
    features JSONB
);

CREATE TABLE player_snapshots (
    id BIGSERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    player_id INTEGER REFERENCES players(id),
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    is_starter BOOLEAN,
    expected_minutes DECIMAL(6,2),
    goals_season INTEGER,
    assists_season INTEGER,
    xg_season DECIMAL(8,4),
    xa_season DECIMAL(8,4),
    shots_per_90 DECIMAL(8,4),
    shots_on_target_per_90 DECIMAL(8,4),
    key_passes_per_90 DECIMAL(8,4),
    goals_per_90 DECIMAL(8,4),
    assists_per_90 DECIMAL(8,4),
    recent_form_score DECIMAL(8,4),
    minutes_ytd INTEGER,
    injury_status TEXT,
    features JSONB
);

CREATE TABLE odds_providers (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    provider_type TEXT,
    base_url TEXT,
    is_active BOOLEAN DEFAULT true,
    supports_live BOOLEAN DEFAULT false,
    supports_prematch BOOLEAN DEFAULT true,
    supports_1xbet BOOLEAN DEFAULT false,
    free_tier_available BOOLEAN DEFAULT true,
    daily_quota INTEGER,
    monthly_quota INTEGER,
    last_health_check TIMESTAMPTZ,
    last_success TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE provider_usage (
    id BIGSERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES odds_providers(id),
    date DATE NOT NULL,
    endpoint TEXT,
    requests_used INTEGER DEFAULT 0,
    requests_remaining INTEGER,
    quota_reset_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(provider_id, date, endpoint)
);

CREATE TABLE odds_snapshots (
    id BIGSERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    provider_id INTEGER REFERENCES odds_providers(id),
    bookmaker TEXT DEFAULT '1xbet',
    market_id TEXT NOT NULL,
    canonical_market TEXT NOT NULL,
    period TEXT DEFAULT 'full_match',
    selection TEXT NOT NULL,
    line DECIMAL(8,4),
    decimal_odds DECIMAL(10,4) NOT NULL,
    is_live BOOLEAN DEFAULT false,
    is_suspended BOOLEAN DEFAULT false,
    source_timestamp TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    is_latest BOOLEAN DEFAULT true
);

CREATE TABLE market_definitions (
    id SERIAL PRIMARY KEY,
    canonical_market TEXT UNIQUE NOT NULL,
    description TEXT,
    settlement_type TEXT,
    is_enabled BOOLEAN DEFAULT false,
    model_validated BOOLEAN DEFAULT false,
    settlement_rules JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE market_outcomes (
    id SERIAL PRIMARY KEY,
    market_definition_id INTEGER REFERENCES market_definitions(id),
    selection TEXT NOT NULL,
    description TEXT,
    outcome_order INTEGER,
    UNIQUE(market_definition_id, selection)
);

CREATE TABLE feature_snapshots (
    id BIGSERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    feature_version TEXT,
    minute INTEGER,
    score_home INTEGER DEFAULT 0,
    score_away INTEGER DEFAULT 0,
    is_live BOOLEAN DEFAULT false,
    lineup_confirmed BOOLEAN DEFAULT false,
    features JSONB NOT NULL,
    data_freshness_seconds INTEGER,
    odds_freshness_seconds INTEGER
);

CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    model_type TEXT,
    status TEXT DEFAULT 'challenger',
    promoted_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ,
    training_start DATE,
    training_end DATE,
    validation_start DATE,
    validation_end DATE,
    dataset_version TEXT,
    hyperparameters JSONB,
    features_used JSONB,
    sample_size INTEGER,
    brier_score DECIMAL(8,6),
    log_loss DECIMAL(8,6),
    ece DECIMAL(8,6),
    roi DECIMAL(8,4),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_name, version)
);

CREATE TABLE calibration_versions (
    id SERIAL PRIMARY KEY,
    model_version_id INTEGER REFERENCES model_versions(id),
    version TEXT NOT NULL,
    calibration_method TEXT,
    market TEXT,
    n_buckets INTEGER,
    parameters JSONB,
    ece DECIMAL(8,6),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prediction_models (
    id SERIAL PRIMARY KEY,
    model_version_id INTEGER REFERENCES model_versions(id),
    market TEXT NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE model_predictions (
    id BIGSERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    model_version_id INTEGER REFERENCES model_versions(id),
    calibration_version_id INTEGER REFERENCES calibration_versions(id),
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    line DECIMAL(8,4),
    predicted_at TIMESTAMPTZ DEFAULT NOW(),
    minute INTEGER,
    score_home INTEGER,
    score_away INTEGER,
    is_live BOOLEAN DEFAULT false,
    raw_probability DECIMAL(8,6) NOT NULL,
    market_probability DECIMAL(8,6),
    calibrated_probability DECIMAL(8,6) NOT NULL,
    probability_lower DECIMAL(8,6),
    probability_upper DECIMAL(8,6),
    decimal_odds DECIMAL(10,4),
    implied_probability DECIMAL(8,6),
    expected_value DECIMAL(8,6),
    simulation_count INTEGER,
    simulation_seed BIGINT,
    simulation_version TEXT,
    feature_snapshot_id BIGINT REFERENCES feature_snapshots(id),
    no_bet_reasons TEXT[],
    is_candidate BOOLEAN DEFAULT false,
    uncertainty DECIMAL(8,6),
    model_confidence DECIMAL(8,6),
    data_freshness_seconds INTEGER,
    odds_freshness_seconds INTEGER
);

CREATE TABLE prediction_results (
    id BIGSERIAL PRIMARY KEY,
    prediction_id BIGINT REFERENCES model_predictions(id),
    settled_at TIMESTAMPTZ DEFAULT NOW(),
    outcome BOOLEAN,
    actual_result TEXT,
    brier_contribution DECIMAL(8,6),
    log_loss_contribution DECIMAL(8,6),
    clv_odds DECIMAL(10,4),
    closing_line_probability DECIMAL(8,6),
    clv DECIMAL(8,6)
);

CREATE TABLE prediction_errors (
    id BIGSERIAL PRIMARY KEY,
    prediction_id BIGINT REFERENCES model_predictions(id),
    error_category TEXT NOT NULL CHECK (error_category in ('MODEL_OVERCONFIDENCE', 'MODEL_UNDERCONFIDENCE', 'BAD_SCORE_STATE', 'BAD_EVENT_RATE', 'BAD_PLAYER_PROJECTION', 'BAD_LINEUP_ADJUSTMENT', 'STALE_ODDS', 'ODDS_MOVEMENT', 'RED_CARD_EFFECT', 'SUBSTITUTION_EFFECT', 'DATA_MISSING', 'SOURCE_CONFLICT', 'RANDOM_VARIANCE', 'MODEL_SPECIFICATION', 'OTHER')),
    magnitude DECIMAL(8,6),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paper_bets (
    id BIGSERIAL PRIMARY KEY,
    prediction_id BIGINT REFERENCES model_predictions(id),
    match_id INTEGER REFERENCES matches(id),
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    line DECIMAL(8,4),
    decimal_odds DECIMAL(10,4) NOT NULL,
    stake_units DECIMAL(8,4) DEFAULT 1.0,
    calibrated_probability DECIMAL(8,6),
    probability_lower DECIMAL(8,6),
    probability_upper DECIMAL(8,6),
    expected_value DECIMAL(8,6),
    model_version TEXT,
    calibration_version TEXT,
    simulation_version TEXT,
    provider_version TEXT,
    placed_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'open' CHECK (status in ('open', 'settled', 'void'))
);

CREATE TABLE paper_bet_settlements (
    id BIGSERIAL PRIMARY KEY,
    paper_bet_id BIGINT REFERENCES paper_bets(id),
    settled_at TIMESTAMPTZ DEFAULT NOW(),
    outcome TEXT CHECK (outcome in ('win', 'loss', 'void', 'push')),
    profit_loss_units DECIMAL(8,4),
    closing_odds DECIMAL(10,4),
    clv DECIMAL(8,6),
    notes TEXT
);

CREATE TABLE learning_runs (
    id SERIAL PRIMARY KEY,
    run_type TEXT,
    model_name TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status TEXT,
    records_processed INTEGER,
    error_message TEXT,
    metrics JSONB
);

CREATE TABLE model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_version_id INTEGER REFERENCES model_versions(id),
    metric_date DATE,
    market TEXT,
    brier_score DECIMAL(8,6),
    log_loss DECIMAL(8,6),
    ece DECIMAL(8,6),
    win_rate DECIMAL(8,4),
    roi DECIMAL(8,4),
    sample_size INTEGER,
    UNIQUE(model_version_id, metric_date, market)
);

CREATE TABLE calibration_bins (
    id BIGSERIAL PRIMARY KEY,
    calibration_version_id INTEGER REFERENCES calibration_versions(id),
    bin_lower DECIMAL(8,6),
    bin_upper DECIMAL(8,6),
    predicted_prob DECIMAL(8,6),
    actual_freq DECIMAL(8,6),
    count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE worker_runs (
    id BIGSERIAL PRIMARY KEY,
    worker_type TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    matches_seen INTEGER DEFAULT 0,
    matches_analyzed INTEGER DEFAULT 0,
    api_requests INTEGER DEFAULT 0,
    quota_remaining INTEGER,
    predictions_generated INTEGER DEFAULT 0,
    no_bet_count INTEGER DEFAULT 0,
    errors TEXT[],
    status TEXT DEFAULT 'running' CHECK (status in ('running', 'success', 'failed', 'skipped'))
);

CREATE TABLE engine_settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO engine_settings (key, value, description) VALUES
('engine_enabled', 'false', 'Master engine on/off switch'),
('worker_enabled', 'false', 'Background worker on/off'),
('analysis_interval_minutes', '5', 'Worker analysis interval'),
('max_matches_per_cycle', '20', 'Max matches per worker cycle'),
('max_api_requests_per_cycle', '50', 'API request budget per cycle'),
('max_simulations', '10000', 'Default Monte Carlo simulations'),
('paper_betting_enabled', 'false', 'Enable paper bet recording'),
('learning_enabled', 'false', 'Enable online learning'),
('rl_enabled', 'false', 'Enable RL decision layer'),
('min_edge_threshold', '0.03', 'Minimum EV threshold for candidates'),
('max_monte_carlo_error', '0.005', 'Max acceptable MC standard error');

CREATE INDEX idx_matches_kickoff_status ON matches(kickoff_utc, status, is_eligible);
CREATE INDEX idx_matches_api_football_id ON matches(api_football_id);
CREATE INDEX idx_matches_comp_status ON matches(competition_id, status);
CREATE INDEX idx_lineups_match_starter ON lineups(match_id, is_starter);
CREATE INDEX idx_match_events_match_min ON match_events(match_id, minute);
CREATE INDEX idx_odds_snapshots_match_market ON odds_snapshots(match_id, canonical_market, is_latest, fetched_at);
CREATE INDEX idx_odds_snapshots_fetched ON odds_snapshots(fetched_at);
CREATE INDEX idx_model_pred_match_market ON model_predictions(match_id, market, predicted_at);
CREATE INDEX idx_model_pred_candidate ON model_predictions(is_candidate, predicted_at);
CREATE INDEX idx_paper_bets_status ON paper_bets(status, placed_at);
CREATE INDEX idx_feature_snapshots_match ON feature_snapshots(match_id, snapshot_at);
CREATE INDEX idx_team_snapshots_match_team ON team_snapshots(match_id, team_id);
CREATE INDEX idx_player_snapshots_match_player ON player_snapshots(match_id, player_id);
CREATE INDEX idx_worker_runs_type_started ON worker_runs(worker_type, started_at);

-- RLS Enablement
ALTER TABLE competitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE lineups ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE odds_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE provider_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE odds_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibration_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_errors ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_bets ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_bet_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibration_bins ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE engine_settings ENABLE ROW LEVEL SECURITY;

-- Anon SELECT access
CREATE POLICY "Anon can view competitions" ON competitions FOR SELECT TO anon USING (true);
CREATE POLICY "Anon can view teams" ON teams FOR SELECT TO anon USING (true);
CREATE POLICY "Anon can view players" ON players FOR SELECT TO anon USING (true);
CREATE POLICY "Anon can view matches" ON matches FOR SELECT TO anon USING (true);
CREATE POLICY "Anon can view market_definitions" ON market_definitions FOR SELECT TO anon USING (true);
CREATE POLICY "Anon can view engine_settings" ON engine_settings FOR SELECT TO anon USING (true);

-- Authenticated full access (simplified per requirements)
CREATE POLICY "Auth full access competitions" ON competitions FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access teams" ON teams FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access players" ON players FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access matches" ON matches FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access lineups" ON lineups FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access match_events" ON match_events FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access team_snapshots" ON team_snapshots FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access player_snapshots" ON player_snapshots FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access odds_providers" ON odds_providers FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access provider_usage" ON provider_usage FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access odds_snapshots" ON odds_snapshots FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access market_definitions" ON market_definitions FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access market_outcomes" ON market_outcomes FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access feature_snapshots" ON feature_snapshots FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access model_versions" ON model_versions FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access calibration_versions" ON calibration_versions FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access prediction_models" ON prediction_models FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access model_predictions" ON model_predictions FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access prediction_results" ON prediction_results FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access prediction_errors" ON prediction_errors FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access paper_bets" ON paper_bets FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access paper_bet_settlements" ON paper_bet_settlements FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access learning_runs" ON learning_runs FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access model_metrics" ON model_metrics FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access calibration_bins" ON calibration_bins FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access worker_runs" ON worker_runs FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access engine_settings" ON engine_settings FOR ALL TO authenticated USING (true);

-- Ensure service_role can access everything naturally due to postgres superuser, but explicitly it bypasses RLS.
