-- Defaults are already seeded in 001_initial_schema.sql but repeating for idempotency
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
('max_monte_carlo_error', '0.005', 'Max acceptable MC standard error')
ON CONFLICT (key) DO NOTHING;
