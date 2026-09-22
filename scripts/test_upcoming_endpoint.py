import urllib.request
import json

try:
    with urllib.request.urlopen('http://localhost:3000/api/matches/upcoming') as r:
        data = json.loads(r.read().decode('utf-8'))
        print('Upcoming matches count:', len(data))
        for m in data:
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            kickoff = m['kickoff']
            odds = m['odds1xBet']
            lineups = m['lineupConfirmed']
            exp = m['lineupExpectedAt']
            print(f"- ID: {m['id']} | {home} vs {away} | Kickoff: {kickoff} | 1xBet: {odds} | Lineups Confirmed: {lineups} | Expected Lineups: {exp}")
except Exception as e:
    print('Error:', e)
