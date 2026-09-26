/**
 * ATOMIC QUOTA GOVERNANCE CLIENT
 * Strictly enforces ₹0.00 external data cost mandate by capping API-Football
 * requests at 95/day (50 user on-demand analysis, 45 worker automation, 5 safety buffer).
 * Operates with ZERO local filesystem dependencies.
 */

export interface QuotaState {
  date: string
  currentUsed: number
  dailyLimit: number
  maxAutoUsage: number       // 45 requests for automated workers
  userReservedCount: number  // 50 requests strictly reserved for user on-demand analysis
  hardStopLimit: number      // 95 hard ceiling
  lastSyncedAt: string
}

export interface QuotaCheckResult {
  allowed: boolean
  reason?: string
  remainingUser?: number
  remainingWorker?: number
  totalUsed?: number
}

// In-memory runtime quota state (process-isolated failsafe)
let memoryQuota = {
  date: new Date().toISOString().split('T')[0],
  userUsed: 0,
  workerUsed: 0,
  lastResetUtc: new Date().toISOString().split('T')[0],
}

function getTodayUtc(): string {
  return new Date().toISOString().split('T')[0]
}

function checkMemoryRollover() {
  const today = getTodayUtc()
  if (memoryQuota.date !== today) {
    memoryQuota.date = today
    memoryQuota.userUsed = 0
    memoryQuota.workerUsed = 0
    memoryQuota.lastResetUtc = today
  }
}

/**
 * Checks and reserves quota atomically via Supabase stored procedure.
 * Falls back to strict in-memory guard if database RPC is unavailable.
 */
export async function canMakeAPIRequest(
  isUserDemand: boolean = false,
  cost: number = 1
): Promise<QuotaCheckResult> {
  checkMemoryRollover()

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey =
    process.env.SUPABASE_SECRET_KEY ||
    process.env.SUPABASE_SERVICE_ROLE_KEY

  if (supabaseUrl && supabaseKey) {
    try {
      const response = await fetch(`${supabaseUrl}/rest/v1/rpc/reserve_api_quota`, {
        method: 'POST',
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          p_provider: 'api-football',
          p_cost: cost,
          p_is_user: isUserDemand,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        if (result && typeof result === 'object') {
          // Update memory mirrors
          if (result.allowed) {
            if (isUserDemand) {
              memoryQuota.userUsed += cost
            } else {
              memoryQuota.workerUsed += cost
            }
          }
          return {
            allowed: Boolean(result.allowed),
            reason: result.reason,
            remainingUser: result.remaining_user,
            remainingWorker: result.remaining_worker,
            totalUsed: result.total_used,
          }
        }
      }
    } catch {
      // Network/RPC failure — proceed to strict in-memory failsafe check
    }
  }

  // In-memory strict safety enforcement
  const totalUsed = memoryQuota.userUsed + memoryQuota.workerUsed
  const HARD_STOP = 95
  const MAX_WORKER = 45
  const MAX_USER = 50

  if (totalUsed + cost > HARD_STOP) {
    return {
      allowed: false,
      reason: `Hard safety limit reached (${totalUsed}/${HARD_STOP}). All API requests suspended to prevent charges.`,
      totalUsed,
    }
  }

  if (isUserDemand) {
    if (memoryQuota.userUsed + cost > MAX_USER) {
      return {
        allowed: false,
        reason: `User on-demand analysis quota reached (${memoryQuota.userUsed}/${MAX_USER}). Resets at 00:00 UTC.`,
        remainingUser: 0,
        totalUsed,
      }
    }
    memoryQuota.userUsed += cost
    return {
      allowed: true,
      remainingUser: MAX_USER - memoryQuota.userUsed,
      remainingWorker: MAX_WORKER - memoryQuota.workerUsed,
      totalUsed: totalUsed + cost,
    }
  } else {
    if (memoryQuota.workerUsed + cost > MAX_WORKER) {
      return {
        allowed: false,
        reason: `Automated worker budget exhausted (${memoryQuota.workerUsed}/${MAX_WORKER}). Remaining 50 requests reserved for user analysis.`,
        remainingWorker: 0,
        totalUsed,
      }
    }
    memoryQuota.workerUsed += cost
    return {
      allowed: true,
      remainingUser: MAX_USER - memoryQuota.userUsed,
      remainingWorker: MAX_WORKER - memoryQuota.workerUsed,
      totalUsed: totalUsed + cost,
    }
  }
}

/**
 * Returns current read-only quota status for dashboard KPI display.
 */
export async function getQuotaState(): Promise<QuotaState> {
  checkMemoryRollover()
  const today = getTodayUtc()

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey =
    process.env.SUPABASE_SECRET_KEY ||
    process.env.SUPABASE_SERVICE_ROLE_KEY

  if (supabaseUrl && supabaseKey) {
    try {
      const response = await fetch(`${supabaseUrl}/rest/v1/rpc/get_api_quota_status`, {
        method: 'POST',
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ p_provider: 'api-football' }),
      })

      if (response.ok) {
        const data = await response.json()
        if (data && typeof data === 'object') {
          return {
            date: data.date || today,
            currentUsed: data.total_used ?? (memoryQuota.userUsed + memoryQuota.workerUsed),
            dailyLimit: data.daily_limit ?? 95,
            maxAutoUsage: data.worker_budget ?? 45,
            userReservedCount: data.user_reserve ?? 50,
            hardStopLimit: data.daily_limit ?? 95,
            lastSyncedAt: new Date().toISOString(),
          }
        }
      }
    } catch {}
  }

  const totalUsed = memoryQuota.userUsed + memoryQuota.workerUsed
  return {
    date: today,
    currentUsed: totalUsed,
    dailyLimit: 95,
    maxAutoUsage: 45,
    userReservedCount: 50,
    hardStopLimit: 95,
    lastSyncedAt: new Date().toISOString(),
  }
}

/**
 * Optional logging hook for request tracing.
 */
export function recordAPIRequest(endpoint: string, actualRemoteUsed?: number) {
  if (actualRemoteUsed !== undefined) {
    const total = memoryQuota.userUsed + memoryQuota.workerUsed
    if (actualRemoteUsed > total) {
      memoryQuota.workerUsed += (actualRemoteUsed - total)
    }
  }
}
