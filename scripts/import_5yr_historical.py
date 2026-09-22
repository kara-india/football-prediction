"""
Historical 5-Year Data Importer from football-data.co.uk to Supabase.
Downloads the past 5 seasons (2019/20 - 2023/24) across major leagues
and stores them directly into Supabase 'historical_matches' table.
"""

import os
import sys
import io
import json
import urllib.request
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL', 'https://qqcxjjkgvqknesrtnwal.supabase.co')
SUPABASE_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh')

# Past 5 Completed Seasons
SEASONS = ['1920', '2021', '2122', '2223', '2324']

# Allowed European Tier-1 Competitions on football-data.co.uk
LEAGUES = {
    'E0': 'Premier League (England)',
    'SP1': 'La Liga (Spain)',
    'I1': 'Serie A (Italy)',
    'D1': 'Bundesliga (Germany)',
    'F1': 'Ligue 1 (France)',
    'N1': 'Eredivisie (Netherlands)',
    'P1': 'Primeira Liga (Portugal)',
    'B1': 'First Division A (Belgium)'
}

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"

def fetch_season_csv(league_code: str, season: str) -> pd.DataFrame:
    url = BASE_URL.format(season=season, league=league_code)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            df = pd.read_csv(io.BytesIO(content), encoding='latin1', on_bad_lines='skip')
            return df
    except Exception as e:
        print(f"  [Notice] Could not download {league_code} {season}: {e}")
        return pd.DataFrame()

def normalize_row(row, league_code: str, league_name: str, season: str):
    date_str = str(row.get('Date', '')).strip()
    match_date = None
    for fmt in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d'):
        try:
            match_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            break
        except:
            continue
            
    if not match_date or not row.get('HomeTeam') or not row.get('AwayTeam'):
        return None

    def safe_int(v):
        try:
            return int(v) if pd.notna(v) else None
        except:
            return None

    def safe_float(v):
        try:
            return float(v) if pd.notna(v) else None
        except:
            return None

    return {
        "league_code": league_code,
        "league_name": league_name,
        "season": f"20{season[:2]}-20{season[2:]}",
        "match_date": match_date,
        "home_team": str(row.get('HomeTeam')).strip(),
        "away_team": str(row.get('AwayTeam')).strip(),
        "fthg": safe_int(row.get('FTHG')),
        "ftag": safe_int(row.get('FTAG')),
        "ftr": str(row.get('FTR', '')).strip() or None,
        "hthg": safe_int(row.get('HTHG')),
        "htag": safe_int(row.get('HTAG')),
        "hs": safe_int(row.get('HS')),
        "as_shots": safe_int(row.get('AS')),
        "hst": safe_int(row.get('HST')),
        "ast": safe_int(row.get('AST')),
        "hf": safe_int(row.get('HF')),
        "af": safe_int(row.get('AF')),
        "hc": safe_int(row.get('HC')),
        "ac": safe_int(row.get('AC')),
        "hy": safe_int(row.get('HY')),
        "ay": safe_int(row.get('AY')),
        "hr": safe_int(row.get('HR')),
        "ar": safe_int(row.get('AR')),
        "b365_h": safe_float(row.get('B365H')),
        "b365_d": safe_float(row.get('B365D')),
        "b365_a": safe_float(row.get('B365A'))
    }

def insert_batch_supabase(records: list):
    url = f"{SUPABASE_URL}/rest/v1/historical_matches"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f"Bearer {SUPABASE_KEY}",
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }
    data = json.dumps(records).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status in (200, 201)
    except urllib.error.HTTPError as e:
        print(f"    [Supabase Upload Notice] Status: {e.code} | {e.read().decode('utf-8')[:200]}")
        return False
    except Exception as e:
        print(f"    [Upload Error] {e}")
        return False

def run_import():
    print("=" * 65)
    print("5-YEAR HISTORICAL FOOTBALL DATA IMPORTER (football-data.co.uk)")
    print(f"Target Seasons: {SEASONS}")
    print(f"Target Leagues: {list(LEAGUES.keys())}")
    print("=" * 65)

    os.makedirs('.cache/football_data', exist_ok=True)
    total_processed = 0

    for league_code, league_name in LEAGUES.items():
        print(f"\nProcessing {league_name} ({league_code})...")
        league_records = []
        for season in SEASONS:
            df = fetch_season_csv(league_code, season)
            if df.empty:
                continue

            # Save local copy in cache as immediate backup
            cache_file = f".cache/football_data/{league_code}_{season}.csv"
            df.to_csv(cache_file, index=False)

            count = 0
            for _, row in df.iterrows():
                rec = normalize_row(row, league_code, league_name, season)
                if rec:
                    league_records.append(rec)
                    count += 1
            print(f"  ✓ Season {season}: {count} matches normalized")

        # Push to Supabase in chunks of 200
        print(f"  Syncing {len(league_records)} matches to Supabase...")
        uploaded = 0
        for i in range(0, len(league_records), 200):
            chunk = league_records[i:i+200]
            success = insert_batch_supabase(chunk)
            if success:
                uploaded += len(chunk)
        
        print(f"  ✓ {uploaded}/{len(league_records)} matches synced to Supabase.")
        total_processed += len(league_records)

    print("\n" + "=" * 65)
    print(f"COMPLETED: Total {total_processed:,} historical matches extracted (Past 5 Years)")
    print("=" * 65)

if __name__ == '__main__':
    run_import()
