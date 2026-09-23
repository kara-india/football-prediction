-- ============================================================
-- MIGRATION 000: BASELINE RECONCILIATION & SCHEMA TRACKING
-- Records applied migration state in PostgreSQL to prevent
-- replaying existing DDL and ensure idempotent execution.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on schema_migrations: only read-accessible to authenticated/anon
ALTER TABLE public.schema_migrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read_schema_migrations"
    ON public.schema_migrations FOR SELECT TO anon USING (true);

CREATE POLICY "auth_read_schema_migrations"
    ON public.schema_migrations FOR SELECT TO authenticated USING (true);

-- Insert baseline migration history records if not already recorded
INSERT INTO public.schema_migrations (version, description, applied_at)
VALUES
    ('001', 'Initial platform schema (27 core tables, initial indexes & RLS)', NOW()),
    ('002', 'Seed competitions (21 top leagues, cups & tournaments)', NOW()),
    ('003', 'Seed market definitions (1X2, Over/Under 2.5, BTTS)', NOW()),
    ('004', 'Historical matches (Past 5 years football-data.co.uk dataset)', NOW())
ON CONFLICT (version) DO NOTHING;
