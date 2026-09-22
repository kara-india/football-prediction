import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv('.env.local')
api_key = os.getenv('API_FOOTBALL_KEY')
headers = {'x-apisports-key': api_key}

fixture_id = 1628995

# 1. Fetch fixture full details (including lineups, events)
url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    fix = data.get('response', [])[0]
    print("=== FIXTURE DETAILS ===")
    print("ID:", fix['fixture']['id'])
    print("Date (UTC):", fix['fixture']['date'])
    print("Status:", fix['fixture']['status'])
    print("League:", fix['league']['name'], "(ID:", fix['league']['id'], ")")
    print("Teams:", fix['teams']['home']['name'], "vs", fix['teams']['away']['name'])
    print("Lineups present?:", len(fix.get('lineups', [])))
    if fix.get('lineups'):
        for l in fix['lineups']:
            print(f"  Team: {l['team']['name']}, Formation: {l.get('formation')}, Starters count: {len(l.get('startXI', []))}")
    else:
        print("  Lineups: None reported yet.")

# 2. Check odds for this fixture
odds_url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
req = urllib.request.Request(odds_url, headers=headers)
with urllib.request.urlopen(req) as resp:
    odds_data = json.loads(resp.read().decode('utf-8'))
    bookmakers = odds_data.get('response', [])
    print("\n=== ODDS DETAILS ===")
    print(f"Bookmakers count: {len(bookmakers)}")
    if bookmakers:
        b_list = bookmakers[0].get('bookmakers', [])
        print(f"Available bookmakers ({len(b_list)}):", [b['name'] for b in b_list])
        onexbet = [b for b in b_list if b['id'] == 6 or '1x' in b['name'].lower()]
        if onexbet:
            print("1xBet found:", onexbet[0]['name'])
            for m in onexbet[0].get('bets', []):
                print(f"  Market: {m['name']} -> {m['values']}")
        else:
            print("1xBet odds not in response yet.")
    else:
        print("No odds published yet for this fixture.")
