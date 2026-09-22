import urllib.request
import json

url = 'https://qqcxjjkgvqknesrtnwal.supabase.co/rest/v1/historical_matches?select=match_date,league_name,season,home_team,away_team,fthg,ftag,ftr,b365_h,b365_d,b365_a&limit=6&order=id.asc'
headers = {
    'apikey': 'sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh',
    'Authorization': 'Bearer sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print("=== LIVE PROOF FROM YOUR SUPABASE DATABASE ===")
    for m in data:
        date = m['match_date']
        season = m['season']
        league = m['league_name']
        match = f"{m['home_team']} {m['fthg']} - {m['ftag']} {m['away_team']}"
        odds = f"Home={m['b365_h']} | Draw={m['b365_d']} | Away={m['b365_a']}"
        print(f"Date: {date} | Season: {season} | {league} | {match} | Odds: {odds}")
