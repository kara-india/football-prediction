import { NextResponse } from 'next/server'
import { fetchFootballData, FootballDataMatchesResponse, formatFixture } from '@/lib/feed'
import { isEligibleFixture } from '@/lib/fixtureEligibility'
import { acquireProviderRequestLock, isProviderCacheConfigured, readProviderCache, recordProviderRequest, writeProviderCache } from '@/lib/providerCache'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const HEADERS = { 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0' }

function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: HEADERS })
}

export async function POST() {
  if (!isProviderCacheConfigured()) return json({ error: 'PROVIDER_CACHE_NOT_CONFIGURED' }, 503)

  const from = new Date()
  const to = new Date(from.getTime() + 14 * 24 * 60 * 60 * 1000)
  const dateFrom = from.toISOString().slice(0, 10)
  const dateTo = to.toISOString().slice(0, 10)
  const cacheKey = `fixtures:PL:${dateFrom}:${dateTo}`
  try {
    const cached = await readProviderCache<SyncResult>(cacheKey)
    if (cached) return json({ ...cached.payload, syncedAt: cached.syncedAt, cached: true })

    const locked = await acquireProviderRequestLock(`sync:${cacheKey}`, 30)
    if (!locked) {
      const waiting = await waitForFixtureCache(cacheKey)
      if (waiting) return json({ ...waiting.payload, syncedAt: waiting.syncedAt, cached: true })
      return json({ error: 'FIXTURE_SYNC_IN_PROGRESS' }, 409)
    }

    const endpoint = `/competitions/PL/matches?dateFrom=${dateFrom}&dateTo=${dateTo}`
    const result = await fetchFootballData(endpoint)
    await recordProviderRequest({ provider: 'football-data.org', endpoint, quotaCost: 1, responseStatus: result.status || (result.ok ? 200 : 502) })

    if (!result.ok) {
      return json({ error: result.reason || 'FIXTURE_FEED_UNAVAILABLE' }, result.status || 502)
    }

    const matches = (result.data as FootballDataMatchesResponse).matches || []
    const fixtures = matches
      .filter(isEligibleFixture)
      .filter(match => ['SCHEDULED', 'TIMED', 'LIVE', 'IN_PLAY', 'PAUSED'].includes(match.status))
      .sort((a, b) => new Date(a.utcDate).getTime() - new Date(b.utcDate).getTime())
      .slice(0, 100)
      .map(formatFixture)

    const payload: SyncResult = { fixtures, syncedAt: new Date().toISOString(), source: 'football-data.org' }
    await writeProviderCache({ cacheKey, provider: 'football-data.org', payload, ttlSeconds: 10 * 60, syncedAt: payload.syncedAt })
    return json(payload)
  } catch {
    return json({ error: 'PROVIDER_CACHE_UNAVAILABLE' }, 503)
  }
}

interface SyncResult { fixtures: ReturnType<typeof formatFixture>[]; syncedAt: string; source: string }

async function waitForFixtureCache(cacheKey: string) {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 250))
    const cached = await readProviderCache<SyncResult>(cacheKey)
    if (cached) return cached
  }
  return null
}
