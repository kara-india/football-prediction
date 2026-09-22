# PHASE 3 — ZERO-COST DATA INGESTION & NORMALIZATION

## 1. Goal
Ingest clean, validated historical match data covering the past 5 seasons across the 10 target domestic leagues from open-access repositories (football-data.co.uk) without spending any API credits. Implement bulk fixture discovery via API-Football using exactly 1 API call per day, normalize all incoming data into canonical structures (`CanonicalMatch`), and assign data quality scores.

## 2. Criticality
**P1 — HIGH** (Provides the foundational training dataset for Dixon-Coles, Elo, and count models).

## 3. Prerequisites
- Phase 2 completed (quota governance operational).
- Network access to `football-data.co.uk` and Supabase.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 3.1 [Historical CSV Ingestion Engine]**: Create `python/ingestion/football_data_uk.py`:
  - Downloads CSV files for seasons 2019/20 through 2023/24 for the 10 target leagues (E0, SP1, D1, I1, F1, P1, N1, B1, etc.).
  - Extracts date, home/away team, full-time score, half-time score, shots, shots on target, corners, fouls, yellow/red cards, and historical closing odds (Bet365/Pinnacle/Max).
  - Resolves team names to canonical team IDs in Supabase `teams`.
  - Inserts deduplicated rows into Supabase `historical_matches`.
- **Task 3.2 [Bulk Daily Fixture Discovery]**: Create `python/ingestion/fixture_discovery.py`:
  - Calls API-Football `/fixtures?date={YYYY-MM-DD}` once per 24-hour cycle (consuming exactly 1 credit).
  - Filters matches by competition allowlist (top 10 leagues + UEFA CL/EL + Senior Men's Internationals).
  - Normalizes payloads into `CanonicalMatch` objects.
  - Upserts eligible matches into Supabase `matches` with status `NS` (Not Started).
- **Task 3.3 [Data Quality Scorer]**: Create `python/ingestion/quality_scorer.py`:
  - Evaluates completeness of each match record: full stats present (1.0), score and cards only (0.8), score only (0.5).
  - Flags anomalies (e.g., negative shots, mismatched halves, impossible cards).

### Sequential Tasks (Follows 3.1 - 3.3)
- **Task 3.4 [Historical Ingestion Execution & Verification]**: Run the ingestion pipeline to populate 5 years of verified records in Supabase.
- **Task 3.5 [Ingestion Smoke Test]**: Verify in Supabase that at least 15,000 clean historical matches exist with verified temporal order and zero lookahead leakage.

## 5. Files / Modules Affected
- `python/ingestion/football_data_uk.py` [NEW]
- `python/ingestion/fixture_discovery.py` [NEW]
- `python/ingestion/quality_scorer.py` [NEW]
- `python/adapters/api_football.py`
- `tests/test_data_ingestion.py` [NEW]

## 6. Database Changes
- Add indexes on `historical_matches(date, home_team, away_team)`.
- Ensure `matches` has unique constraint on `(provider, provider_fixture_id)`.

## 7. Tests Required
- `tests/test_data_ingestion.py`:
  1. Test team name fuzzy matching against Supabase dictionary (e.g., "Man United" $\to$ "Manchester United").
  2. Test normalization of CSV and API-Football payloads into `CanonicalMatch`.
  3. Verify quality score computation across complete and truncated match records.
  4. Ensure discovery uses strictly 1 API credit and records it in `provider_usage`.

## 8. Acceptance Criteria
- [ ] 5 years of historical match data for all 10 target leagues ingested into Supabase.
- [ ] Daily fixture discovery consumes exactly 1 API-Football request per day.
- [ ] All match records conform to `CanonicalMatch` contract in `docs/DATA_CONTRACTS.md`.
- [ ] Zero financial cost incurred.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build `python/ingestion/football_data_uk.py`, `fixture_discovery.py`, and `quality_scorer.py`.
  2. Execute unit tests in `tests/test_data_ingestion.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Run the historical ingestion CLI command:
     ```powershell
     python -m python.ingestion.football_data_uk --seasons 5
     ```
  2. Inspect Supabase dashboard to verify row count in `historical_matches` increases appropriately.

## 11. Rollback Plan
- Truncate newly inserted historical rows using `DELETE FROM historical_matches WHERE created_at > NOW() - INTERVAL '1 hour'` if data corruption is observed.

## 12. Risks
- External site football-data.co.uk could have transient rate limiting. Implement exponential backoff and local retry.

## 13. What Must NOT Be Considered Complete
- Relying on a small synthetic dummy dataset.
- Ingesting fixtures without canonical schema normalization and quality scoring.
