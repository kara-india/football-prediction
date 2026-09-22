import os
import json
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv('.env.local')
api_key = os.getenv('API_FOOTBALL_KEY')
headers = {'x-apisports-key': api_key}

# Allowed competition IDs from our registry
# 39: EPL, 71: Brazil Serie A, 135: Italy Serie A, 140: La Liga, 78: Bundesliga, 61: Ligue 1
# 94: Portugal, 88: Eredivisie, 128: Argentina, 144: Belgium, 2: UCL, 3: UEL, 1: World Cup, 4: Euro, 5: Nations League, 9: Copa America, 6: AFCON, 7: Asian Cup, 10: Friendlies
ALLOWED_LEAGUES = {39, 71, 135, 140, 78, 61, 94, 88, 128, 144, 2, 3, 1, 4, 5, 9, 6, 7, 10}

print("=== CHECKING FOR LIVE MATCHES ACROSS ALL LEAGUES ===")
live_url = "https://v3.football.api-sports.io/fixtures?live=all"
req = urllib.request.Request(live_url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    live_matches = data.get('response', [])
    print(f"Total live matches currently globally: {len(live_matches)}")
    
    allowed_live = [m for m in live_matches if m['league']['id'] in ALLOWED_LEAGUES]
    print(f"Live matches in our allowed competitions: {len(allowed_live)}")
    for m in allowed_live:
        fix = m['fixture']
        teams = m['teams']
        goals = m['goals']
        league = m['league']
        print(f"ID: {fix['id']} | {league['name']} | {fix['status']['elapsed']}' ({fix['status']['short']}) | {teams['home']['name']} {goals['home']} - {goals['away']} {teams['away']['name']}")

print("\n=== CHECKING TODAY'S MATCHES IN ALLOWED COMPETITIONS ===")
today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
print("UTC Date:", today_str)

today_url = f"https://v3.football.api-sports.io/fixtures?date={today_str}"
req = urllib.request.Request(today_url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    today_matches = data.get('response', [])
    print(f"Total fixtures scheduled today globally: {len(today_matches)}")
    
    allowed_today = [m for m in today_matches if m['league']['id'] in ALLOWED_LEAGUES]
    print(f"Fixtures in our allowed competitions today: {len(allowed_today)}")
    for m in allowed_today:
        fix = m['fixture']
        teams = m['teams']
        league = m['league']
        print(f"ID: {fix['id']} | {league['name']} | Status: {fix['status']['short']} | Kickoff: {fix['date']} | {teams['home']['name']} vs {teams['away']['name']}")
