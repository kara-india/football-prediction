# Operations Guide

## How to enable the engine
To enable the engine, set the `engine_enabled` setting in your Supabase database or environment.

## GitHub Actions Secrets Setup
You will need to configure the following secrets in your repository settings:
- `SUPABASE_URL`: e.g. https://qqcxjjkgvqknesrtnwal.supabase.co
- `SUPABASE_SERVICE_ROLE_KEY`: Obtain from Supabase dashboard (Project Settings > API)
- `API_FOOTBALL_KEY`: Free tier, register at api-sports.io
- `ODDS_API_KEY`: Optional, The Odds API

## Worker Schedule Explanation
- **Collector Worker**: Runs every 15 minutes to gather live match data and odds.
- **Evaluator Worker**: Runs daily at 3 AM UTC to settle paper bets and update prediction results.
- **Learner Worker**: Runs weekly on Monday at 4 AM UTC to learn from the week's data.

## How to monitor worker runs
Check the Actions tab in your GitHub repository for logs of the scheduled jobs.

## Engine ON/OFF instructions
Toggle `engine_enabled` in the database settings.

## How to check provider health
Hit the `/providers/status` endpoint on the running engine or run the FastAPI app locally.

## How to apply schema migrations
Apply migrations via Supabase CLI or dashboard.
