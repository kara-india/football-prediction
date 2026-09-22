import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv('.env.local')
headers = {'x-apisports-key': os.getenv('API_FOOTBALL_KEY')}

for fix_id in [1493144, 1610876]:
    url = f"https://v3.football.api-sports.io/fixtures?id={fix_id}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        if data.get('response'):
            fix = data['response'][0]
            print(f"\n=== FIXTURE {fix_id} ===")
            print("Match:", fix['teams']['home']['name'], "vs", fix['teams']['away']['name'])
            print("League:", fix['league']['name'])
            print("Status:", fix['fixture']['status'])
            print("Lineups count:", len(fix.get('lineups', [])))
            print("Events count:", len(fix.get('events', [])))
            print("Statistics available:", len(fix.get('statistics', [])))
            
    # Check odds
    odds_url = f"https://v3.football.api-sports.io/odds?fixture={fix_id}"
    req = urllib.request.Request(odds_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        resp_list = data.get('response', [])
        print(f"Odds response count for {fix_id}:", len(resp_list))
        if resp_list:
            b_list = resp_list[0].get('bookmakers', [])
            print(f"Bookmakers available ({len(b_list)}):", [b['name'] for b in b_list])
            onex = [b for b in b_list if b['id'] == 6 or '1x' in b['name'].lower()]
            if onex:
                print("1xBet odds found! Markets:")
                for b in onex[0].get('bets', [])[:3]:
                    print(f"  {b['name']}: {b['values']}")
