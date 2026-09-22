export interface Match {
  id: string;
  competition_id: string;
  home_team_id: string;
  away_team_id: string;
  kickoff_time: string;
  status: string;
  minute?: number;
  home_score?: number;
  away_score?: number;
}

export interface Team {
  id: string;
  name: string;
}

export interface Competition {
  id: string;
  name: string;
}

export interface Player {
  id: string;
  name: string;
}

export interface LiveState {
  possession_home: number;
  possession_away: number;
  shots_home: number;
  shots_away: number;
  shots_on_target_home: number;
  shots_on_target_away: number;
  xg_home: number;
  xg_away: number;
  corners_home: number;
  corners_away: number;
  cards_home: number;
  cards_away: number;
  fouls_home: number;
  fouls_away: number;
}

export interface Lineup {
  match_id: string;
  team_id: string;
  confirmed: boolean;
}

export interface OddsMarket {
  id: string;
  name: string;
}

export interface OddsSnapshot {
  market_id: string;
  selection: string;
  price: number;
  timestamp: string;
}

export interface ModelPrediction {
  id: string;
  match_id: string;
  market_id: string;
  selection: string;
  probability: number;
  model_version: string;
  created_at: string;
}

export interface BetCandidate {
  prediction_id: string;
  ev: number;
  kelly_fraction: number;
  decision: 'HIGH CONFIDENCE CANDIDATE' | 'NO BET';
  no_bet_reason?: string;
}

export interface PredictionResult {
  id: string;
}

export interface PaperBet {
  id: string;
}

export interface ProviderHealth {
  id: string;
  name: string;
  authenticated: boolean;
  reachable: boolean;
  live_support: boolean;
  prematch_support: boolean;
  xbet_confirmed: boolean;
  request_limit: number;
  requests_remaining: number;
  last_success?: string;
  last_error?: string;
  supported_markets: string[];
}

export interface EngineSettings {
  enabled: boolean;
}

export interface WorkerRun {
  id: string;
}

export interface ModelVersion {
  version: string;
  description: string;
}
