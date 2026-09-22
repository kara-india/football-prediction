INSERT INTO market_definitions (canonical_market, is_enabled) VALUES 
('1x2', true),
('double_chance', true),
('over_under_15', true),
('over_under_25', true),
('over_under_35', true),
('over_under_45', true),
('btts', true),
('next_goal', true),
('total_cards', true),
('team_cards', true),
('anytime_goalscorer', true),
('player_assist', true)
ON CONFLICT (canonical_market) DO NOTHING;
