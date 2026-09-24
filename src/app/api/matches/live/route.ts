import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { fetchFootball, formatFixture } from '@/lib/feed'
import { isEligibleFixture } from '@/lib/fixtureEligibility'

export const dynamic = 'force-dynamic'
export const revalidate = 0
const CACHE_TTL_MS = 60 * 1000
const CACHE_KEY = 'live_matches_cache'
const HEADERS = { 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0' }

export async function GET() {
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) return NextResponse.json(cached, { headers: HEADERS })

  const result = await fetchFootball('/fixtures?live=all', true)
  if (!result.ok) {
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    if (stale?.length) return NextResponse.json(stale, { headers: HEADERS })
    return NextResponse.json({ error: result.reason || 'LIVE_FEED_UNAVAILABLE' }, { status: result.status || 502, headers: HEADERS })
  }

  const live = (result.data as any[]).filter(isEligibleFixture).map(formatFixture).map((m: any, i: number) => {
    const raw = (result.data as any[]).filter(isEligibleFixture)[i]
    return { ...m, minute: raw.fixture.status.elapsed, events: raw.events || [], score: { home: raw.goals?.home ?? 0, away: raw.goals?.away ?? 0 } }
  })
  setDiskCache(CACHE_KEY, live)
  return NextResponse.json(live, { headers: HEADERS })
}
