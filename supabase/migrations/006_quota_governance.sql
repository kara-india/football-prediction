-- ============================================================
-- MIGRATION 006: ATOMIC QUOTA GOVERNANCE & COST SAFETY ENGINE
-- Strict enforcement of the ₹0.00 external data cost mandate.
-- Enforces a 95 total daily request ceiling with:
--   - 50 requests strictly reserved for user on-demand analysis
--   - 45 requests for scheduled background worker operations
--   - 5 requests as an untouched safety buffer
-- ============================================================

-- Ensure provider_usage table has exact schema for atomic governance
CREATE TABLE IF NOT EXISTS public.provider_usage (
    id SERIAL,
    provider TEXT NOT NULL DEFAULT 'api-football',
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    user_requests_made INTEGER NOT NULL DEFAULT 0,
    worker_requests_made INTEGER NOT NULL DEFAULT 0,
    daily_limit INTEGER NOT NULL DEFAULT 95,
    user_reserve INTEGER NOT NULL DEFAULT 50,
    worker_budget INTEGER NOT NULL DEFAULT 45,
    safety_buffer INTEGER NOT NULL DEFAULT 5,
    last_requested_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (provider, usage_date)
);

-- Enable RLS
ALTER TABLE public.provider_usage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_provider_usage" ON public.provider_usage;
CREATE POLICY "anon_read_provider_usage" 
    ON public.provider_usage FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "auth_read_provider_usage" ON public.provider_usage;
CREATE POLICY "auth_read_provider_usage" 
    ON public.provider_usage FOR SELECT TO authenticated USING (true);

-- ------------------------------------------------------------
-- ATOMIC QUOTA RESERVATION STORED FUNCTION
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.reserve_api_quota(
    p_provider TEXT DEFAULT 'api-football',
    p_cost INT DEFAULT 1,
    p_is_user BOOLEAN DEFAULT FALSE
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_today DATE := (NOW() AT TIME ZONE 'UTC')::DATE;
    v_row public.provider_usage%ROWTYPE;
    v_total_used INT;
    v_rem_user INT;
    v_rem_worker INT;
BEGIN
    -- Ensure row exists for today UTC
    INSERT INTO public.provider_usage (
        provider, usage_date, user_requests_made, worker_requests_made,
        daily_limit, user_reserve, worker_budget, safety_buffer, last_requested_at
    )
    VALUES (
        p_provider, v_today, 0, 0, 95, 50, 45, 5, NOW()
    )
    ON CONFLICT (provider, usage_date) DO NOTHING;

    -- Lock the row for update to guarantee atomicity and prevent race conditions
    SELECT * INTO v_row
    FROM public.provider_usage
    WHERE provider = p_provider AND usage_date = v_today
    FOR UPDATE;

    v_total_used := v_row.user_requests_made + v_row.worker_requests_made;

    -- 1. HARD STOP CHECK: Total requests cannot exceed daily_limit (95)
    IF v_total_used + p_cost > v_row.daily_limit THEN
        RETURN jsonb_build_object(
            'allowed', false,
            'reason', format('Hard safety stop: daily quota reached (%s/%s). Preserving 5 safety buffer.', v_total_used, v_row.daily_limit),
            'remaining_user', GREATEST(0, v_row.user_reserve - v_row.user_requests_made),
            'remaining_worker', GREATEST(0, v_row.worker_budget - v_row.worker_requests_made),
            'total_used', v_total_used
        );
    END IF;

    -- 2. USER ANALYSIS BUDGET CHECK
    IF p_is_user THEN
        IF v_row.user_requests_made + p_cost > v_row.user_reserve THEN
            RETURN jsonb_build_object(
                'allowed', false,
                'reason', format('User analysis quota reached (%s/%s). Resets at 00:00 UTC.', v_row.user_requests_made, v_row.user_reserve),
                'remaining_user', 0,
                'remaining_worker', GREATEST(0, v_row.worker_budget - v_row.worker_requests_made),
                'total_used', v_total_used
            );
        END IF;

        -- Deduct from user budget
        UPDATE public.provider_usage
        SET user_requests_made = user_requests_made + p_cost,
            last_requested_at = NOW()
        WHERE provider = p_provider AND usage_date = v_today;

        v_rem_user := v_row.user_reserve - (v_row.user_requests_made + p_cost);
        v_rem_worker := v_row.worker_budget - v_row.worker_requests_made;

        RETURN jsonb_build_object(
            'allowed', true,
            'remaining_user', v_rem_user,
            'remaining_worker', v_rem_worker,
            'total_used', v_total_used + p_cost
        );

    -- 3. AUTOMATED WORKER BUDGET CHECK
    ELSE
        IF v_row.worker_requests_made + p_cost > v_row.worker_budget THEN
            RETURN jsonb_build_object(
                'allowed', false,
                'reason', format('Automated worker budget exhausted (%s/%s). Remaining requests strictly reserved for user on-demand analysis.', v_row.worker_requests_made, v_row.worker_budget),
                'remaining_user', GREATEST(0, v_row.user_reserve - v_row.user_requests_made),
                'remaining_worker', 0,
                'total_used', v_total_used
            );
        END IF;

        -- Deduct from worker budget
        UPDATE public.provider_usage
        SET worker_requests_made = worker_requests_made + p_cost,
            last_requested_at = NOW()
        WHERE provider = p_provider AND usage_date = v_today;

        v_rem_user := v_row.user_reserve - v_row.user_requests_made;
        v_rem_worker := v_row.worker_budget - (v_row.worker_requests_made + p_cost);

        RETURN jsonb_build_object(
            'allowed', true,
            'remaining_user', v_rem_user,
            'remaining_worker', v_rem_worker,
            'total_used', v_total_used + p_cost
        );
    END IF;
END;
$$;

-- Grant execution to anon and authenticated
GRANT EXECUTE ON FUNCTION public.reserve_api_quota(TEXT, INT, BOOLEAN) TO anon, authenticated, service_role;

-- ------------------------------------------------------------
-- QUOTA STATUS QUERY FUNCTION (READ-ONLY)
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_api_quota_status(
    p_provider TEXT DEFAULT 'api-football'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_today DATE := (NOW() AT TIME ZONE 'UTC')::DATE;
    v_row public.provider_usage%ROWTYPE;
BEGIN
    SELECT * INTO v_row
    FROM public.provider_usage
    WHERE provider = p_provider AND usage_date = v_today;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'provider', p_provider,
            'date', v_today,
            'user_requests_made', 0,
            'worker_requests_made', 0,
            'total_used', 0,
            'daily_limit', 95,
            'user_reserve', 50,
            'worker_budget', 45,
            'remaining_user', 50,
            'remaining_worker', 45
        );
    END IF;

    RETURN jsonb_build_object(
        'provider', p_provider,
        'date', v_today,
        'user_requests_made', v_row.user_requests_made,
        'worker_requests_made', v_row.worker_requests_made,
        'total_used', v_row.user_requests_made + v_row.worker_requests_made,
        'daily_limit', v_row.daily_limit,
        'user_reserve', v_row.user_reserve,
        'worker_budget', v_row.worker_budget,
        'remaining_user', GREATEST(0, v_row.user_reserve - v_row.user_requests_made),
        'remaining_worker', GREATEST(0, v_row.worker_budget - v_row.worker_requests_made)
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_api_quota_status(TEXT) TO anon, authenticated, service_role;

-- Record migration 006
INSERT INTO public.schema_migrations (version, description, applied_at)
VALUES ('006', 'Atomic quota governance function and provider_usage daily budgeting', NOW())
ON CONFLICT (version) DO NOTHING;
