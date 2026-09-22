import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import urllib.request
from dotenv import load_dotenv

from python.models.elo import EloSystem
from python.simulation.match_state import MatchState
from python.simulation.event_intensities import EventIntensityEstimator
from python.simulation.monte_carlo import MonteCarloSimulator
from python.calibration.calibrator import ProbabilityCalibrator
from python.calibration.ev_calculator import EVCalculator
from python.calibration.no_bet_gate import NoBetGate
from python.calibration.settlement import SettlementCalculator

load_dotenv('.env.local')
api_key = os.getenv('API_FOOTBALL_KEY')
headers = {'x-apisports-key': api_key}

fixture_id = 1493144

# 1. Fetch Fixture details
url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    fix = data['response'][0]

home_team = fix['teams']['home']['name']
away_team = fix['teams']['away']['name']
home_id = fix['teams']['home']['id']
away_id = fix['teams']['away']['id']
final_home = fix['goals']['home']
final_away = fix['goals']['away']

print("=================================================================")
print(f"FULL ANALYTICAL PIPELINE: {home_team.upper()} vs {away_team.upper()}")
print(f"Competition: {fix['league']['name']} | Kickoff: {fix['fixture']['date']}")
print(f"Final Score: {home_team} {final_home} - {final_away} {away_team}")
print("=================================================================")

# 2. Check Lineups
lineups = fix.get('lineups', [])
print(f"\n[1] LINEUP GATING:")
print(f"  Confirmed Lineups Count: {len(lineups)}")
for l in lineups:
    print(f"  {l['team']['name']} (Formation: {l['formation']}): {len(l['startXI'])} Starters confirmed")

# 3. Pull 1xBet Odds
odds_url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
req = urllib.request.Request(odds_url, headers=headers)
with urllib.request.urlopen(req) as resp:
    odds_data = json.loads(resp.read().decode('utf-8'))
    bookmakers = odds_data['response'][0]['bookmakers']
    onex = next(b for b in bookmakers if b['id'] == 6 or '1x' in b['name'].lower())
    match_winner = next(b for b in onex['bets'] if b['name'] == 'Match Winner')

odds_map = {item['value']: float(item['odd']) for item in match_winner['values']}
home_odd = odds_map['Home']
draw_odd = odds_map['Draw']
away_odd = odds_map['Away']

print(f"\n[2] TARGET BOOKMAKER (1xBet) ODDS:")
print(f"  Home ({home_team}): {home_odd:.2f}")
print(f"  Draw:              {draw_odd:.2f}")
print(f"  Away ({away_team}): {away_odd:.2f}")

ev_calc = EVCalculator()
implied_probs = [ev_calc.compute_implied_probability(o) for o in [home_odd, draw_odd, away_odd]]
margin = ev_calc.compute_margin([home_odd, draw_odd, away_odd])
devigged_probs = ev_calc.de_vig_multiplicative([home_odd, draw_odd, away_odd])

print(f"  1xBet Margin: {margin*100:.2f}%")
print(f"  De-vigged Market Probabilities: Home={devigged_probs[0]:.3f}, Draw={devigged_probs[1]:.3f}, Away={devigged_probs[2]:.3f}")

# 4. Statistical Baseline & Dynamic Intensities
elo = EloSystem()
p_elo_home, p_elo_draw, p_elo_away = elo.predict_1x2(home_id, away_id)

state = MatchState(
    minute=0,
    added_time=0,
    score_home=0,
    score_away=0,
    period='first_half',
    possession_home=50.0,
    shots_home=0,
    shots_away=0,
    shots_on_target_home=0,
    shots_on_target_away=0,
    xg_home=0.0,
    xg_away=0.0,
    corners_home=0,
    corners_away=0,
    fouls_home=0,
    fouls_away=0,
    yellow_cards_home=0,
    yellow_cards_away=0,
    red_cards_home=0,
    red_cards_away=0,
    offsides_home=0,
    offsides_away=0,
    substitutions_home=0,
    substitutions_away=0,
    is_live=False,
    lineup_confirmed=True
)

# 5. Path-Dependent Monte Carlo Simulation (50,000 paths)
mc = MonteCarloSimulator(seed=42)
intensity_est = EventIntensityEstimator()

# Prior expected goal intensity ~1.1 home, 0.9 away for Argentine league
sim_result = mc.simulate_match_from_state(
    state=state,
    home_lambda=1.15,
    away_lambda=0.90,
    intensity_estimator=intensity_est,
    n_simulations=50000
)

market_probs = mc.extract_market_probabilities(sim_result)
sim_home = market_probs['1x2']['1']
sim_draw = market_probs['1x2']['X']
sim_away = market_probs['1x2']['2']

print(f"\n[3] MONTE CARLO SIMULATION ({sim_result.simulation_count:,} Paths, Seed=42):")
print(f"  Simulated Probabilities: Home={sim_home:.3f}, Draw={sim_draw:.3f}, Away={sim_away:.3f}")
print(f"  Convergence Standard Error: {sim_result.std_error:.5f}")
print(f"  Over 2.5 Goals: {market_probs.get('over_under_25', {}).get('over', 0):.3f}")
print(f"  BTTS Yes:       {market_probs.get('btts', {}).get('yes', 0):.3f}")

# 6. Calibration Layer
calibrator = ProbabilityCalibrator()
cal_home = calibrator.calibrate(sim_home, market='1x2')
cal_draw = calibrator.calibrate(sim_draw, market='1x2')
cal_away = calibrator.calibrate(sim_away, market='1x2')

# 7. Expected Value & NO-BET Gate Evaluation
gate = NoBetGate()
markets_to_eval = [
    ('Home', '1', home_odd, sim_home, devigged_probs[0], cal_home),
    ('Draw', 'X', draw_odd, sim_draw, devigged_probs[1], cal_draw),
    ('Away', '2', away_odd, sim_away, devigged_probs[2], cal_away),
]

print(f"\n[4] EXPECTED VALUE & 15-GATE DECISION MATRIX:")
print(f"{'Selection':<8} | {'1xBet':<6} | {'Implied%':<9} | {'Model%':<7} | {'Calib%':<7} | {'EV':<7} | {'Decision':<14} | {'Reason'}")
print("-" * 85)

settler = SettlementCalculator()
for name, sel, odds, raw_p, mkt_p, cal_p in markets_to_eval:
    ev = ev_calc.compute_ev_binary(cal_p, odds)
    ci_lower = max(0.01, cal_p - 0.04)
    ci_upper = min(0.99, cal_p + 0.04)
    
    cand = gate.evaluate(
        market="1x2",
        selection=sel,
        line=None,
        decimal_odds=odds,
        raw_probability=raw_p,
        market_probability=mkt_p,
        calibrated_probability=cal_p,
        probability_lower=ci_lower,
        probability_upper=ci_upper,
        simulation_count=sim_result.simulation_count,
        simulation_std_error=sim_result.std_error,
        data_freshness_seconds=20,
        odds_freshness_seconds=30,
        is_live=False,
        lineup_confirmed=True,
        is_market_suspended=False,
        model_calibrated=True,
        historical_sample_size=350,
        provider_healthy=True
    )
    
    reasons_str = ", ".join(cand.no_bet_reasons) if cand.no_bet_reasons else "NONE (PASS)"
    print(f"{name:<8} | {odds:<6.2f} | {100/odds:<8.1f}% | {raw_p*100:<6.1f}% | {cal_p*100:<6.1f}% | {ev*100:>+5.1f}% | {cand.decision:<14} | {reasons_str}")

# 8. Settlement against actual result
actual_1x2_res = settler.settle_1x2(final_home, final_away, '1')
print(f"\n[5] MARKET SETTLEMENT AUDIT:")
print(f"  Actual Result: {home_team} {final_home} - {final_away} {away_team}")
print(f"  1X2 Winning Selection: {'Home (1)' if final_home > final_away else 'Away (2)' if final_away > final_home else 'Draw (X)'}")
