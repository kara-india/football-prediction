import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv('.env.local')
api_key = os.getenv('API_FOOTBALL_KEY')

headers = {'x-apisports-key': api_key}

def search_team(name):
    url = f"https://v3.football.api-sports.io/teams?search={name}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        for t in data.get('response', []):
            if t['team'].get('national'):
                return t['team']
        if data.get('response'):
            return data['response'][0]['team']
    return None

japan = search_team('Japan')
uruguay = search_team('Uruguay')

print("Japan Team:", japan)
print("Uruguay Team:", uruguay)

if japan and uruguay:
    # 1. Check H2H
    h2h_url = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={japan['id']}-{uruguay['id']}"
    req = urllib.request.Request(h2h_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        fixtures = data.get('response', [])
        print(f"\nH2H Fixtures ({len(fixtures)}):")
        for f in fixtures[:5]:
            fix = f['fixture']
            teams = f['teams']
            goals = f['goals']
            print(f"Fixture ID: {fix['id']} | Date: {fix['date']} | Status: {fix['status']['short']} | {teams['home']['name']} vs {teams['away']['name']}")

    # 2. Check upcoming fixtures for Japan
    next_url = f"https://v3.football.api-sports.io/fixtures?team={japan['id']}&next=5"
    req = urllib.request.Request(next_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        upcoming = data.get('response', [])
        print(f"\nUpcoming fixtures for Japan ({len(upcoming)}):")
        for f in upcoming:
            fix = f['fixture']
            teams = f['teams']
            league = f['league']
            print(f"ID: {fix['id']} | Date: {fix['date']} | Status: {fix['status']['short']} | {league['name']} | {teams['home']['name']} vs {teams['away']['name']}")
