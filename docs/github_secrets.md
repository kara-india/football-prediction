# GitHub Secrets Documentation

The following secrets must be configured in your GitHub repository settings under **Settings > Secrets and variables > Actions**:

- `SUPABASE_URL`: The URL of your Supabase project (e.g. `https://<ref>.supabase.co`).
- `SUPABASE_SERVICE_ROLE_KEY`: The service role key for Supabase, which has admin privileges. Find this in **Project Settings > API**.
- `API_FOOTBALL_KEY`: Your API key for API-Sports (api-sports.io). A free tier is available.
- `ODDS_API_KEY`: Your API key for The Odds API (optional).
- `LEARNING_ENABLED`: Optional override to toggle the Learner worker functionality.

**IMPORTANT**: Never hardcode these values in the repository code or documentation. Always use GitHub Actions Secrets.
