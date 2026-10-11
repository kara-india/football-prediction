import 'server-only'

const CACHE_TABLE = 'provider_request_cache'
const LOG_TABLE = 'provider_request_logs'
const QUOTA_TABLE = 'provider_quota_snapshots'

export type ProviderName = 'football-data.org' | 'the-odds-api'

export interface ProviderQuotaSnapshot {
  provider: ProviderName
  remote_used: number | null
  remote_remaining: number | null
  last_request_cost: number | null
  last_request_at: string
  updated_at: string
}

export function isProviderCacheConfigured(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY)
}

function restUrl(path: string): URL {
  const base = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!base || !key) throw new Error('PROVIDER_CACHE_NOT_CONFIGURED')
  return new URL(`/rest/v1/${path}`, base)
}

function headers(prefer?: string): HeadersInit {
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!key) throw new Error('PROVIDER_CACHE_NOT_CONFIGURED')
  return {
    apikey: key,
    Authorization: `Bearer ${key}`,
    'Content-Type': 'application/json',
    ...(prefer ? { Prefer: prefer } : {}),
  }
}

export async function readProviderCache<T>(cacheKey: string): Promise<{ payload: T; syncedAt: string; expiresAt: string; providerMetadata: Record<string, unknown> } | null> {
  const url = restUrl(CACHE_TABLE)
  url.searchParams.set('select', 'payload,synced_at,expires_at,provider_metadata')
  url.searchParams.set('cache_key', `eq.${cacheKey}`)
  url.searchParams.set('expires_at', `gt.${new Date().toISOString()}`)
  const response = await fetch(url, { headers: headers(), cache: 'no-store', signal: AbortSignal.timeout(5000) })
  if (!response.ok) throw new Error(`PROVIDER_CACHE_READ_FAILED_${response.status}`)
  const rows = await response.json() as Array<{ payload: T; synced_at: string; expires_at: string; provider_metadata: Record<string, unknown> }>
  const row = rows[0]
  return row ? { payload: row.payload, syncedAt: row.synced_at, expiresAt: row.expires_at, providerMetadata: row.provider_metadata || {} } : null
}

export async function writeProviderCache<T>(input: {
  cacheKey: string
  provider: ProviderName
  payload: T
  providerMetadata?: Record<string, unknown>
  ttlSeconds: number
  syncedAt?: string
}): Promise<void> {
  const url = restUrl(CACHE_TABLE)
  const syncedAt = input.syncedAt || new Date().toISOString()
  const response = await fetch(url, {
    method: 'POST',
    headers: headers('resolution=merge-duplicates,return=minimal'),
    cache: 'no-store',
    signal: AbortSignal.timeout(5000),
    body: JSON.stringify({
      cache_key: input.cacheKey,
      provider: input.provider,
      payload: input.payload,
      provider_metadata: input.providerMetadata || {},
      synced_at: syncedAt,
      expires_at: new Date(Date.parse(syncedAt) + input.ttlSeconds * 1000).toISOString(),
      updated_at: new Date().toISOString(),
    }),
  })
  if (!response.ok) throw new Error(`PROVIDER_CACHE_WRITE_FAILED_${response.status}`)
}

export async function acquireProviderRequestLock(lockKey: string, seconds = 30): Promise<boolean> {
  const url = restUrl('rpc/try_acquire_provider_request_lock')
  const response = await fetch(url, {
    method: 'POST',
    headers: headers(),
    cache: 'no-store',
    signal: AbortSignal.timeout(5000),
    body: JSON.stringify({ p_lock_key: lockKey, p_lock_seconds: seconds }),
  })
  if (!response.ok) throw new Error(`PROVIDER_LOCK_FAILED_${response.status}`)
  return response.json() as Promise<boolean>
}

export async function recordProviderRequest(input: {
  provider: ProviderName
  endpoint: string
  quotaCost?: number
  responseStatus?: number
  remoteUsed?: number | null
  remoteRemaining?: number | null
}): Promise<void> {
  const url = restUrl(LOG_TABLE)
  const response = await fetch(url, {
    method: 'POST',
    headers: headers('return=minimal'),
    cache: 'no-store',
    signal: AbortSignal.timeout(5000),
    body: JSON.stringify({
      provider: input.provider,
      endpoint: input.endpoint,
      quota_cost: input.quotaCost ?? 0,
      response_status: input.responseStatus ?? null,
      remote_used: input.remoteUsed ?? null,
      remote_remaining: input.remoteRemaining ?? null,
    }),
  })
  if (!response.ok) throw new Error(`PROVIDER_LOG_WRITE_FAILED_${response.status}`)
}

export async function saveProviderQuota(input: {
  provider: ProviderName
  remoteUsed?: number | null
  remoteRemaining?: number | null
  lastRequestCost?: number | null
}): Promise<void> {
  const url = restUrl(QUOTA_TABLE)
  const response = await fetch(url, {
    method: 'POST',
    headers: headers('resolution=merge-duplicates,return=minimal'),
    cache: 'no-store',
    signal: AbortSignal.timeout(5000),
    body: JSON.stringify({
      provider: input.provider,
      remote_used: input.remoteUsed ?? null,
      remote_remaining: input.remoteRemaining ?? null,
      last_request_cost: input.lastRequestCost ?? null,
      last_request_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }),
  })
  if (!response.ok) throw new Error(`PROVIDER_QUOTA_WRITE_FAILED_${response.status}`)
}

export async function readProviderQuota(provider: ProviderName): Promise<ProviderQuotaSnapshot | null> {
  const url = restUrl(QUOTA_TABLE)
  url.searchParams.set('select', 'provider,remote_used,remote_remaining,last_request_cost,last_request_at,updated_at')
  url.searchParams.set('provider', `eq.${provider}`)
  const response = await fetch(url, { headers: headers(), cache: 'no-store', signal: AbortSignal.timeout(5000) })
  if (!response.ok) throw new Error(`PROVIDER_QUOTA_READ_FAILED_${response.status}`)
  const rows = await response.json() as ProviderQuotaSnapshot[]
  return rows[0] || null
}

export async function readProviderMonthlyRequestCount(provider: ProviderName): Promise<number> {
  const monthStart = new Date()
  monthStart.setUTCDate(1)
  monthStart.setUTCHours(0, 0, 0, 0)
  const url = restUrl(LOG_TABLE)
  url.searchParams.set('select', 'id')
  url.searchParams.set('provider', `eq.${provider}`)
  url.searchParams.set('requested_at', `gte.${monthStart.toISOString()}`)
  const requestHeaders = new Headers(headers('count=exact'))
  requestHeaders.set('Range', '0-0')
  const response = await fetch(url, {
    method: 'HEAD',
    headers: requestHeaders,
    cache: 'no-store',
    signal: AbortSignal.timeout(5000),
  })
  if (!response.ok) throw new Error(`PROVIDER_USAGE_READ_FAILED_${response.status}`)
  const contentRange = response.headers.get('content-range')
  const total = contentRange?.split('/')[1]
  return total && total !== '*' ? Number(total) || 0 : 0
}
