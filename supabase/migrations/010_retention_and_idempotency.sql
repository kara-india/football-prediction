-- ============================================================
-- MIGRATION 010: PRODUCTION RETENTION & IDEMPOTENCY LOCKING
-- Establishes automated storage governance to keep database
-- safely below Supabase free-tier limits (< 500 MB).
-- Defends inviolable analytical data (matches, predictions, odds)
-- while safely pruning transient high-velocity ticks and logs.
-- ============================================================

-- 1. Ensure transient tables exist with retention-friendly indexing
CREATE TABLE IF NOT EXISTS public.match_event_ticks (
    id BIGSERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES public.matches(id) ON DELETE CASCADE,
    minute INTEGER,
    second INTEGER,
    tick_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_match_event_ticks_created_at 
    ON public.match_event_ticks(created_at);

CREATE TABLE IF NOT EXISTS public.raw_provider_payloads (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_provider_payloads_created_at 
    ON public.raw_provider_payloads(created_at);

-- 2. Enable RLS on transient tables
ALTER TABLE public.match_event_ticks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.raw_provider_payloads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_match_event_ticks" ON public.match_event_ticks;
CREATE POLICY "anon_read_match_event_ticks" 
    ON public.match_event_ticks FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "auth_read_match_event_ticks" ON public.match_event_ticks;
CREATE POLICY "auth_read_match_event_ticks" 
    ON public.match_event_ticks FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "auth_read_raw_provider_payloads" ON public.raw_provider_payloads;
CREATE POLICY "auth_read_raw_provider_payloads" 
    ON public.raw_provider_payloads FOR SELECT TO authenticated USING (true);

-- 3. 64-bit deterministic hash functions for PostgreSQL advisory locking
CREATE OR REPLACE FUNCTION public.fnv1a_64(input_text TEXT)
RETURNS BIGINT AS $$
DECLARE
    hash_val NUMERIC := 14695981039346656037; -- FNV offset basis (64-bit)
    fnv_prime NUMERIC := 1099511628211;       -- FNV prime (64-bit)
    mod_val NUMERIC := 18446744073709551616;  -- 2^64
    i INT;
    b INT;
    bytes BYTEA;
BEGIN
    IF input_text IS NULL THEN
        RETURN 0;
    END IF;
    bytes := convert_to(input_text, 'UTF8');
    FOR i IN 0..octet_length(bytes) - 1 LOOP
        b := get_byte(bytes, i);
        hash_val := ((hash_val # b) * fnv_prime) % mod_val;
    END LOOP;
    IF hash_val >= 9223372036854775808 THEN
        RETURN (hash_val - mod_val)::BIGINT;
    ELSE
        RETURN hash_val::BIGINT;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION public.hash_for_advisory_lock(key_text TEXT)
RETURNS BIGINT AS $$
BEGIN
    IF key_text IS NULL THEN
        RETURN 0;
    END IF;
    RETURN hashtext_extended(key_text, 0);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- 4. Stored procedure: prune_transient_logs(days_to_keep INT DEFAULT 14)
-- Prunes transient rows while leaving analytical tables 100% inviolable.
CREATE OR REPLACE FUNCTION public.prune_transient_logs(
    days_to_keep INT DEFAULT 14
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_ticks_pruned BIGINT := 0;
    v_payloads_pruned BIGINT := 0;
    v_worker_runs_pruned BIGINT := 0;
    v_ticks_cutoff TIMESTAMPTZ;
    v_payloads_cutoff TIMESTAMPTZ;
    v_worker_cutoff TIMESTAMPTZ;
BEGIN
    v_ticks_cutoff := NOW() - (days_to_keep || ' days')::INTERVAL;
    v_payloads_cutoff := NOW() - INTERVAL '7 days';
    v_worker_cutoff := NOW() - INTERVAL '30 days';

    -- 1. Prune match_event_ticks older than days_to_keep
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'match_event_ticks') THEN
        WITH deleted AS (
            DELETE FROM public.match_event_ticks
            WHERE created_at < v_ticks_cutoff
            RETURNING id
        )
        SELECT COUNT(*) INTO v_ticks_pruned FROM deleted;
    END IF;

    -- 2. Prune raw_provider_payloads older than 7 days
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'raw_provider_payloads') THEN
        WITH deleted AS (
            DELETE FROM public.raw_provider_payloads
            WHERE created_at < v_payloads_cutoff
            RETURNING id
        )
        SELECT COUNT(*) INTO v_payloads_pruned FROM deleted;
    END IF;

    -- 3. Prune worker_runs older than 30 days
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'worker_runs') THEN
        WITH deleted AS (
            DELETE FROM public.worker_runs
            WHERE started_at < v_worker_cutoff
            RETURNING id
        )
        SELECT COUNT(*) INTO v_worker_runs_pruned FROM deleted;
    END IF;

    RETURN jsonb_build_object(
        'status', 'success',
        'ticks_pruned', v_ticks_pruned,
        'payloads_pruned', v_payloads_pruned,
        'worker_runs_pruned', v_worker_runs_pruned,
        'total_pruned', v_ticks_pruned + v_payloads_pruned + v_worker_runs_pruned,
        'executed_at', NOW()
    );
END;
$$;
