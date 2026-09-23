import { NextResponse } from 'next/server'
import { getQuotaState } from '@/lib/quotaGuard'

export const dynamic = 'force-dynamic'

interface WorkerVitals {
  last_run_name: string | null
  last_run_timestamp: string | null
  last_run_status: string | null
}

interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  database: 'connected' | 'disconnected'
  quota: {
    remaining: number
    limit: number
    resets_at: string
  }
  workers: WorkerVitals
  timestamp: string
}

export async function GET() {
  const timestamp = new Date().toISOString()
  let dbStatus: 'connected' | 'disconnected' = 'disconnected'
  const workerVitals: WorkerVitals = {
    last_run_name: null,
    last_run_timestamp: null,
    last_run_status: null,
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

  // 1. Lightweight database connectivity ping & latest worker run lookup
  if (supabaseUrl && supabaseKey) {
    try {
      // Query engine_settings to verify database connectivity
      const pingRes = await fetch(
        `${supabaseUrl}/rest/v1/engine_settings?select=key&limit=1`,
        {
          method: 'GET',
          headers: {
            apikey: supabaseKey,
            Authorization: `Bearer ${supabaseKey}`,
          },
          cache: 'no-store',
        }
      )

      if (pingRes.ok) {
        dbStatus = 'connected'

        // Fetch latest worker execution status safely
        try {
          const workerRes = await fetch(
            `${supabaseUrl}/rest/v1/worker_runs?select=worker_name,started_at,status&order=started_at.desc&limit=1`,
            {
              method: 'GET',
              headers: {
                apikey: supabaseKey,
                Authorization: `Bearer ${supabaseKey}`,
              },
              cache: 'no-store',
            }
          )
          if (workerRes.ok) {
            const runs = await workerRes.json()
            if (Array.isArray(runs) && runs.length > 0) {
              workerVitals.last_run_name = runs[0].worker_name || null
              workerVitals.last_run_timestamp = runs[0].started_at || null
              workerVitals.last_run_status = runs[0].status || null
            }
          }
        } catch {
          // Worker lookup failure is non-fatal for primary health
        }
      }
    } catch {
      dbStatus = 'disconnected'
    }
  }

  // 2. Obtain quota metrics from authoritative state
  let remainingQuota = 95
  let quotaLimit = 95
  let resetsAt = `${new Date().toISOString().split('T')[0]}T23:59:59Z`

  try {
    const quotaState = await getQuotaState()
    quotaLimit = quotaState.dailyLimit || 95
    remainingQuota = Math.max(0, quotaLimit - (quotaState.currentUsed || 0))
    resetsAt = `${quotaState.date || new Date().toISOString().split('T')[0]}T23:59:59Z`
  } catch {
    // Retain default safe quota numbers if quotaGuard is unreachable
  }

  // 3. Determine composite health status
  const isHealthy = dbStatus === 'connected' && remainingQuota > 0
  const isDegraded = dbStatus === 'connected' && remainingQuota <= 0

  const status: 'healthy' | 'degraded' | 'unhealthy' = isHealthy
    ? 'healthy'
    : isDegraded
    ? 'degraded'
    : 'unhealthy'

  // 4. Construct sanitized response — STRICTLY ZERO EXPOSURE of keys, tokens, or weights
  const responsePayload: HealthResponse = {
    status,
    database: dbStatus,
    quota: {
      remaining: remainingQuota,
      limit: quotaLimit,
      resets_at: resetsAt,
    },
    workers: workerVitals,
    timestamp,
  }

  return NextResponse.json(responsePayload, {
    status: status === 'healthy' ? 200 : status === 'degraded' ? 200 : 503,
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate',
    },
  })
}
