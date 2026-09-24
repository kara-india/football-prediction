import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { fetchFootball, formatFixture } from '@/lib/feed'
import { isEligibleFixture, isUpcomingFixture } from '@/lib/fixtureEligibility'
import { isActuallyUpcoming } from '@/lib/upcomingFixtures'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const CACHE_TTL_MS = 30 * 60 * 1000
const CACHE_KEY = 'upcoming_fixtures_cache'
const INDIA_TIME_ZONE = 'Asia/Kolkata'
const HEADERS = { 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0' }

function getIndiaDate(date: Date): string {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: INDIA_TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(date)
  const y = parts.find(p => p.type === 'year')?.value
  const m = parts.find(p => p.type === 'month')?.value
  const d = parts.find(p => p.type === 'day')?.value
  if (!y || !m || !d) throw new Error('Failed to calculate India calendar date')
  return `${y}-${m}-${d}`
}

function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: HEADERS })
}

export async function GET() {
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) return json(cached.filter(m => isActuallyUpcoming(m)))

  const query = `date=${getIndiaDate(new Date())}&timezone=${encodeURIComponent(INDIA_TIME_ZONE)}`
  const result = await fetchFootball(`/fixtures?${query}`, true)

  if (!result.ok) {
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    if (stale?.length) return json(stale.filter(m => isActuallyUpcoming(m)))
    return json({ error: result.reason || 'FIXTURE_FEED_UNAVAILABLE' }, result.status || 502)
  }

  const now = Date.now()
  const formatted = (result.data as any[])
    .filter(f => isEligibleFixture(f) && isUpcomingFixture(f, now))
    .sort((a, b) => new Date(a.fixture.date).getTime() - new Date(b.fixture.date).getTime())
    .slice(0, 50)
    .map(formatFixture)

  setDiskCache(CACHE_KEY, formatted)
  return json(formatted)
}
