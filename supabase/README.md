# Supabase Migrations

Contains SQL migrations for the football prediction platform database.

## Applying Migrations

You can apply these migrations using the provided python script:

```bash
export SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...
python scripts/apply_migrations.py
```

Or using the TypeScript runner:

```bash
npx ts-node scripts/run_migrations.ts
```
