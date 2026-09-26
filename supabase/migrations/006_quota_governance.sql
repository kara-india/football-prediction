-- ============================================================
-- MIGRATION 006: ATOMIC QUOTA GOVERNANCE & COST SAFETY
--
-- The baseline schema already uses public.provider_usage for
-- endpoint-level provider telemetry. It is intentionally preserved.
-- This migration owns a separate daily quota ledger.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.api_quota_usage (
    provider TEXT NOT NULL DEFAULT 'api-football',
    usage_date DATE NOT NULL,
    user_requests_made INTEGER NOT NULL DEFAULT 0,
    worker_requests_made INTEGER NOT NULL DEFAULT 0,
    daily_limit INTEGER NOT NULL DEFAULT 95,
    user_reserve INTEGER NOT NULL DEFAULT 50,
    worker_budget INTEGER NOT NULL DEFAULT 45,
    safety_buffer INTEGER NOT NULL DEFAULT 5,
    last_requested_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (provider, usage_date),
    CONSTRAINT api_quota_usage_nonnegative
        CHECK (
            user_requests_made >= 0
            AND worker_requests_made >= 0
            AND daily_limit > 0
            AND user_reserve >= 0
            AND worker_budget >= 0
            AND safety_buffer >= 0
        ),
    CONSTRAINT api_quota_usage_budget_consistency
        CHECK (user_reserve + worker_budget + safety_buffer = daily_limit)
);

ALTER TABLE public.api_quota_usage ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.api_quota_usage FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.api_quota_usage TO service_role;

CREATE OR REPLACE FUNCTION public.reserve_api_quota(
    p_provider TEXT DEFAULT 'api-football',
    p_cost INT DEFAULT 1,
    p_is_user BOOLEAN DEFAULT FALSE
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_today DATE := (NOW() AT TIME ZONE 'UTC')::DATE;
    v_row public.api_quota_usage%ROWTYPE;
    v_total_used INT;
    v_rem_user INT;
    v_rem_worker INT;
BEGIN
    IF p_provider IS NULL OR btrim(p_provider) = '' THEN
        RAISE EXCEPTION 'INVALID_PROVIDER';
    END IF;

    IF p_cost IS NULL OR p_cost <= 0 OR p_cost > 95 THEN
        RAISE EXCEPTION 'INVALID_QUOTA_COST';
    END IF;

    INSERT INTO public.api_quota_usage (
        provider, usage_date, user_requests_made, worker_requests_made,
        daily_limit, user_reserve, worker_budget, safety_buffer, last_requested_at
    )
    VALUES (
        p_provider, v_today, 0, 0, 95, 50, 45, 5, NOW()
    )
    ON CONFLICT (provider, usage_date) DO NOTHING;

    SELECT *
      INTO v_row
      FROM public.api_quota_usage
     WHERE provider = p_provider
       AND usage_date = v_today
     FOR UPDATE;

    v_total_used := v_row.user_requests_made + v_row.worker_requests_made;

    IF v_total_used + p_cost > v_row.daily_limit THEN
        RETURN jsonb_build_object(
            'allowed', false,
            'reason', format('Hard safety stop: daily quota reached (%s/%s).', v_total_used, v_row.daily_limit),
            'remaining_user', GREATEST(0, v_row.user_reserve - v_row.user_requests_made),
            'remaining_worker', GREATEST(0, v_row.worker_budget - v_row.worker_requests_made),
            'total_used', v_total_used,
            'date_utc', v_today
        );
    END IF;

    IF p_is_user THEN
        IF v_row.user_requests_made + p_cost > v_row.user_reserve THEN
            RETURN jsonb_build_object(
                'allowed', false,
                'reason', format('User analysis quota reached (%s/%s). Resets at 00:00 UTC.', v_row.user_requests_made, v_row.user_reserve),
                'remaining_user', 0,
                'remaining_worker', GREATEST(0, v_row.worker_budget - v_row.worker_requests_made),
                'total_used', v_total_used,
                'date_utc', v_today
            );
        END IF;

        UPDATE public.api_quota_usage
           SET user_requests_made = user_requests_made + p_cost,
               last_requested_at = NOW()
         WHERE provider = p_provider
           AND usage_date = v_today;

        v_rem_user := v_row.user_reserve - (v_row.user_requests_made + p_cost);
        v_rem_worker := v_row.worker_budget - v_row.worker_requests_made;
    ELSE
        IF v_row.worker_requests_made + p_cost > v_row.worker_budget THEN
            RETURN jsonb_build_object(
                'allowed', false,
                'reason', format('Automated worker budget exhausted (%s/%s).', v_row.worker_requests_made, v_row.worker_budget),
                'remaining_user', GREATEST(0, v_row.user_reserve - v_row.user_requests_made),
                'remaining_worker', 0,
                'total_used', v_total_used,
                'date_utc', v_today
            );
        END IF;

        UPDATE public.api_quota_usage
           SET worker_requests_made = worker_requests_made + p_cost,
               last_requested_at = NOW()
         WHERE provider = p_provider
           AND usage_date = v_today;

        v_rem_user := v_row.user_reserve - v_row.user_requests_made;
        v_rem_worker := v_row.worker_budget - (v_row.worker_requests_made + p_cost);
    END IF;

    RETURN jsonb_build_object(
        'allowed', true,
        'remaining_user', v_rem_user,
        'remaining_worker', v_rem_worker,
        'total_used', v_total_used + p_cost,
        'date_utc', v_today
    );
END;
$$;

REVOKE ALL ON FUNCTION public.reserve_api_quota(TEXT, INT, BOOLEAN)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.reserve_api_quota(TEXT, INT, BOOLEAN)
    TO service_role;

CREATE OR REPLACE FUNCTION public.get_api_quota_status(
    p_provider TEXT DEFAULT 'api-football'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_today DATE := (NOW() AT TIME ZONE 'UTC')::DATE;
    v_row public.api_quota_usage%ROWTYPE;
BEGIN
    SELECT *
      INTO v_row
      FROM public.api_quota_usage
     WHERE provider = p_provider
       AND usage_date = v_today;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'available', true,
            'provider', p_provider,
            'date_utc', v_today,
            'user_requests_made', 0,
            'worker_requests_made', 0,
            'total_used', 0,
            'daily_limit', 95,
            'user_reserve', 50,
            'worker_budget', 45,
            'safety_buffer', 5,
            'remaining_user', 50,
            'remaining_worker', 45
        );
    END IF;

    RETURN jsonb_build_object(
        'available', true,
        'provider', p_provider,
        'date_utc', v_today,
        'user_requests_made', v_row.user_requests_made,
        'worker_requests_made', v_row.worker_requests_made,
        'total_used', v_row.user_requests_made + v_row.worker_requests_made,
        'daily_limit', v_row.daily_limit,
        'user_reserve', v_row.user_reserve,
        'worker_budget', v_row.worker_budget,
        'safety_buffer', v_row.safety_buffer,
        'remaining_user', GREATEST(0, v_row.user_reserve - v_row.user_requests_made),
        'remaining_worker', GREATEST(0, v_row.worker_budget - v_row.worker_requests_made)
    );
END;
$$;

REVOKE ALL ON FUNCTION public.get_api_quota_status(TEXT)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_api_quota_status(TEXT)
    TO service_role;

INSERT INTO public.schema_migrations (version, description, applied_at)
VALUES ('006', 'Atomic daily API quota governor using dedicated api_quota_usage ledger', NOW())
ON CONFLICT (version) DO UPDATE
SET description = EXCLUDED.description,
    applied_at = EXCLUDED.applied_at;
