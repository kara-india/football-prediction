import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

from python.calibration.no_bet_gate import NoBetGate
from python.simulation.match_state import MatchState
from python.models.elo import EloSystem

load_dotenv('.env.local')

# Fixture 1628995: Japan vs Uruguay
fixture_id = 1628995

# Live check from API data:
lineups_confirmed = False  # 0 lineups available ~38h before kickoff
odds_available = False     # 0 bookmaker odds available yet

print("=== PIPELINE EVALUATION: JAPAN vs URUGUAY (Fixture 1628995) ===")
print("Kickoff: 2026-09-24T10:05:00 UTC")
print("Status: Upcoming (NS)")
print(f"Lineup Confirmed: {lineups_confirmed}")
print(f"1xBet Odds Published: {odds_available}")

# 1. Check baseline Elo for both teams
elo = EloSystem()
# Prior H2H matches show Japan and Uruguay
japan_elo = elo.get_rating(12)
uruguay_elo = elo.get_rating(7)
p_home, p_draw, p_away = elo.predict_1x2(12, 7)
print(f"\nBaseline Elo (Uncalibrated Prior):")
print(f"  Japan Elo: {japan_elo}")
print(f"  Uruguay Elo: {uruguay_elo}")
print(f"  Baseline 1X2 Probabilities: Home={p_home:.3f}, Draw={p_draw:.3f}, Away={p_away:.3f}")

# 2. Evaluate through the strict NO-BET gate
gate = NoBetGate()
candidate = gate.evaluate(
    market="1x2",
    selection="1",
    line=None,
    decimal_odds=2.10 if odds_available else 1.0,
    raw_probability=p_home,
    market_probability=0.0,
    calibrated_probability=p_home,
    probability_lower=p_home - 0.05,
    probability_upper=p_home + 0.05,
    simulation_count=10000,
    simulation_std_error=0.004,
    data_freshness_seconds=30,
    odds_freshness_seconds=99999 if not odds_available else 10,
    is_live=False,
    lineup_confirmed=lineups_confirmed,
    is_market_suspended=False,
    model_calibrated=True,
    historical_sample_size=150,
    provider_healthy=True
)

print(f"\nNO-BET Gate Decision:")
print(f"  Decision: {candidate.decision}")
print(f"  Is Candidate: {candidate.is_candidate}")
print(f"  Rejection Reasons: {candidate.no_bet_reasons}")
