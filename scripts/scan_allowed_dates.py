import os
import json
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv('.env.local')
api_key = os.getenv('API_FOOTBALL_KEY')
headers = {'x-apisports-key': api_key}

ALLOWED_LEAGUES = {39, 71, 135, 140, 78, 61, 94, 88, 128, 144, 2, 3, 1, 4, 5, 9, 6, 7, 10}

for check_date in ['2026-09-22', '2026-09-23', '2026-09-24', '2026-09-25']:
    url = f"https://v3.football.api-sports.io/fixtures?date={check_date}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        matches = data.get('response', [])
        allowed = [m for m in matches if m['league']['id'] in ALLOWED_LEAGUES]
        print(f"Date {check_date}: {len(allowed)} matches in allowed leagues:")
        for m in allowed:
            f = m['fixture']
            t = m['teams']
            league = m['league']
            print(f"  ID: {f['id']} | {league['name']} | Status: {f['status']['short']} | Time: {f['date']} | {t['home']['name']} vs {t['away']['name']}")
