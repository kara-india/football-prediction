/**
 * Server-side API quota governor client.
 *
 * The authoritative quota lives in Supabase/PostgreSQL.
 * This module deliberately fails closed when the quota governor cannot
 * be reached or returns an invalid response. A process-local counter cannot
 * safely enforce a provider-wide cap across serverless instances.
 */

export interface QuotaState {
  date: string
  currentUsed: number
  dailyLimit: number
  maxAutoUsage: number
  userReservedCount: number
  hardStopLimit: number
  lastSyncedAt: string
  available: boolean
  reason?: string
}

export interface QuotaCheckResult {
  allowed: boolean
  reason?: string
  remainingUser?: number
  remainingWorker?: number
  totalUsed?: number
  dateUtc?: string
}

function getConfig(): { url: string; serviceRoleKey: string } | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !serviceRoleKey) return null
  return { url, serviceRoleKey }
}

export async function canMakeAPIRequest(
  isUserDemand = false,
  cost = 1,
): Promise<QuotaCheckResult> {
  if (!Number.isSafeInteger(cost) || cost <= 0) {
    return { allowed: false, reason: 'INVALID_QUOTA_COST' }
  }

  const config = getConfig()
  if (!config) {
    return { allowed: false, reason: 'QUOTA_GOVERNOR_UNCONFIGURED' }
  }

  try {
    const response = await fetch(
      `${config.url}/rest/v1/rpc/reserve_api_quota`,
      {
        method: 'POST',
        headers: {
          apikey: config.serviceRoleKey,
          Authorization: `Bearer ${config.serviceRoleKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          p_provider: 'api-football',
          p_cost: cost,
          p_is_user: isUserDemand,
        }),
        cache: 'no-store',
      },
    )

    if (!response.ok) {
      return { allowed: false, reason: `QUOTA_GOVERNOR_HTTP_${response.status}` }
    }

    const result = await response.json()
    if (!result || typeof result !== 'object' || typeof result.allowed !== 'boolean') {
      return { allowed: false, reason: 'QUOTA_GOVERNOR_INVALID_RESPONSE' }
    }

    return {
      allowed: result.allowed,
      reason: typeof result.reason === 'string' ? result.reason : undefined,
      remainingUser:
        typeof result.remaining_user === 'number' ? result.remaining_user : undefined,
      remainingWorker:
        typeof result.remaining_worker === 'number' ? result.remaining_worker : undefined,
      totalUsed:
        typeof result.total_used === 'number' ? result.total_used : undefined,
      dateUtc:
        typeof result.date_utc === 'string' ? result.date_utc : undefined,
    }
  } catch {
    return { allowed: false, reason: 'QUOTA_GOVERNOR_UNAVAILABLE' }
  }
}

export async function getQuotaState(): Promise<QuotaState> {
  const today = new Date().toISOString().slice(0, 10)
  const config = getConfig()

  if (!config) {
    return {
      date: today,
      currentUsed: 0,
      dailyLimit: 95,
      maxAutoUsage: 45,
      userReservedCount: 50,
      hardStopLimit: 95,
      lastSyncedAt: new Date().toISOString(),
      available: false,
      reason: 'QUOTA_GOVERNOR_UNCONFIGURED',
    }
  }

  try {
    const response = await fetch(
      `${config.url}/rest/v1/rpc/get_api_quota_status`,
      {
        method: 'POST',
        headers: {
          apikey: config.serviceRoleKey,
          Authorization: `Bearer ${config.serviceRoleKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ p_provider: 'api-football' }),
        cache: 'no-store',
      },
    )

    if (!response.ok) {
      return {
        date: today,
        currentUsed: 0,
        dailyLimit: 95,
        maxAutoUsage: 45,
        userReservedCount: 50,
        hardStopLimit: 95,
        lastSyncedAt: new Date().toISOString(),
        available: false,
        reason: `QUOTA_GOVERNOR_HTTP_${response.status}`,
      }
    }

    const data = await response.json()
    if (!data || typeof data !== 'object' || data.available !== true) {
      return {
        date: today,
        currentUsed: 0,
        dailyLimit: 95,
        maxAutoUsage: 45,
        userReservedCount: 50,
        hardStopLimit: 95,
        lastSyncedAt: new Date().toISOString(),
        available: false,
        reason: 'QUOTA_GOVERNOR_INVALID_RESPONSE',
      }
    }

    return {
      date: typeof data.date_utc === 'string' ? data.date_utc : today,
      currentUsed: typeof data.total_used === 'number' ? data.total_used : 0,
      dailyLimit: typeof data.daily_limit === 'number' ? data.daily_limit : 95,
      maxAutoUsage:
        typeof data.worker_budget === 'number' ? data.worker_budget : 45,
      userReservedCount:
        typeof data.user_reserve === 'number' ? data.user_reserve : 50,
      hardStopLimit:
        typeof data.daily_limit === 'number' ? data.daily_limit : 95,
      lastSyncedAt: new Date().toISOString(),
      available: true,
    }
  } catch {
    return {
      date: today,
      currentUsed: 0,
      dailyLimit: 95,
      maxAutoUsage: 45,
      userReservedCount: 50,
      hardStopLimit: 95,
      lastSyncedAt: new Date().toISOString(),
      available: false,
      reason: 'QUOTA_GOVERNOR_UNAVAILABLE',
    }
  }
}
