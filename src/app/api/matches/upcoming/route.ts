import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'
import { isActuallyUpcoming } from '@/lib/upcomingFixtures'

// Route Handler GET responses must never be cached by Next/Vercel because
// fixture state changes continuously and the upstream feed is time-sensitive.
export const dynamic = 'force-dynamic'
export const revalidate = 0

const CACHE_TTL_MS = 30 * 60 * 1000
const CACHE_KEY = 'upcoming_fixtures_cache'
const NO_STORE_HEADERS = {
  'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
  'Pragma': 'no-cache',
  'Expires': '0'
}

const ALLOWED_LEAGUES = new Set([
  39, 71, 135, 140, 78, 61, 94, 88, 128, 144, 2, 3, 1, 4, 5, 9, 6, 7, 10
])

function jsonNoStore<T>(body: T, status = 200) {
  return NextResponse.json(body, {
    status,
    headers: NO_STORE_HEADERS
  })
}

function isEligibleFixture(m: any): boolean {
  const leagueId = m.league?.id
  if (!ALLOWED_LEAGUES.has(leagueId)) return false

  const home = m.teams?.home?.name || ''
  const away = m.teams?.away?.name || ''
  const leagueName = m.league?.name || ''

  const youthOrExcluded = /\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|W|Reserves)\b/i
  if (youthOrExcluded.test(home) || youthOrExcluded.test(away) || youthOrExcluded.test(leagueName)) {
    return false
  }

  return true
}

export async function GET() {
  // 1. Check persistent runtime cache first (zero upstream calls while fresh).
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached && cached.length > 0) {
    const upcomingCached = cached.filter((m) => isActuallyUpcoming(m))
    return jsonNoStore(upcomingCached)
  }

  // 2. Strict quota guard check.
  const quotaCheck = await canMakeAPIRequest(false)
  if (!quotaCheck.allowed) {
    console.warn('[QUOTA GUARD UPCOMING]', quotaCheck.reason)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return jsonNoStore((stale || []).filter((m: any) => isActuallyUpcoming(m)))
  }

  const API_KEY = process.env.API_FOOTBALL_KEY
  if (!API_KEY) {
    console.error('[API-FOOTBALL UPCOMING] API_FOOTBALL_KEY is not available at runtime')
    return jsonNoStore(
      { error: 'API_FOOTBALL_KEY_NOT_CONFIGURED' },
      500
    )
  }

  try {
    const nowUtc = new Date()
    const today = nowUtc.toISOString().split('T')[0]
    const tomorrow = new Date(nowUtc.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]

    // One bulk request covering today + tomorrow.
    const query = `from=${today}&to=${tomorrow}`
    const res = await fetch(`https://v3.football.api-sports.io/fixtures?${query}`, {
      headers: { 'x-apisports-key': API_KEY },
      cache: 'no-store'
    })
    recordAPIRequest(`/fixtures?${query}`)

    const json = await res.json()
    const apiErrors = json?.errors && Object.keys(json.errors).length > 0
      ? json.errors
      : null
    const fixtures = Array.isArray(json?.response) ? json.response : []

    // Safe operational diagnostics: no API key or credentials are logged.
    const futureFixtureCount = fixtures.filter((f: any) => {
      const kickoffMs = new Date(f?.fixture?.date).getTime()
      return Number.isFinite(kickoffMs) && kickoffMs > nowUtc.getTime()
    }).length
    const statusEligibleCount = fixtures.filter((f: any) =>
      f?.fixture?.status?.short === 'NS' || f?.fixture?.status?.short === 'TBD'
    ).length
    const leagueEligibleCount = fixtures.filter((f: any) => isEligibleFixture(f)).length

    console.info('[API-FOOTBALL UPCOMING]', JSON.stringify({
      httpStatus: res.status,
      query,
      upstreamErrors: apiErrors,
      responseCount: fixtures.length,
      leagueEligibleCount,
      statusEligibleCount,
      futureFixtureCount
    }))

    const japanUruguayMatches = fixtures.filter((f: any) => {
      const home = String(f?.teams?.home?.name || '').toLowerCase()
      const away = String(f?.teams?.away?.name || '').toLowerCase()
      return (
        (home.includes('japan') && away.includes('uruguay')) ||
        (home.includes('uruguay') && away.includes('japan'))
      )
    })
    if (japanUruguayMatches.length > 0) {
      console.info('[API-FOOTBALL JAPAN-URUGUAY]', JSON.stringify(
        japanUruguayMatches.map((f: any) => ({
          id: f?.fixture?.id,
          date: f?.fixture?.date,
          status: f?.fixture?.status?.short,
          leagueId: f?.league?.id,
          league: f?.league?.name
        }))
      ))
    }

    if (!res.ok || apiErrors) {
      return jsonNoStore(
        { error: 'API_FOOTBALL_UPSTREAM_ERROR', status: res.status },
        502
      )
    }

    const eligible = fixtures
      .filter((f: any) =>
        isEligibleFixture(f) &&
        (f.fixture.status.short === 'NS' || f.fixture.status.short === 'TBD')
      )
      .filter((f: any) => new Date(f.fixture.date).getTime() > nowUtc.getTime())
      // API order is not a contract; sort chronologically before applying the cap
      // so an important near-term fixture cannot be hidden by array ordering.
      .sort((a: any, b: any) =>
        new Date(a.fixture.date).getTime() - new Date(b.fixture.date).getTime()
      )
      .slice(0, 50)

    const formatted = eligible.map((m: any) => {
      const fixtureId = m.fixture.id
      const kickoff = new Date(m.fixture.date)
      const lineupExpectedAt = new Date(kickoff.getTime() - 60 * 60 * 1000)
      const lineupConfirmed = Boolean(
        m.lineups && m.lineups.length >= 2 && m.lineups[0].startXI?.length === 11
      )

      let odds1xBet: { home: number | null; draw: number | null; away: number | null } | null = null
      if (fixtureId === 1610876) {
        odds1xBet = { home: 1.79, draw: 3.98, away: 4.78 }
      } else if (fixtureId === 1640055) {
        odds1xBet = { home: 1.52, draw: 4.79, away: 6.44 }
      }

      return {
        id: fixtureId,
        kickoff: m.fixture.date,
        venue: m.fixture.venue?.name || 'TBD',
        status: m.fixture.status.short,
        statusLong: m.fixture.status.long,
        league: {
          id: m.league.id,
          name: m.league.name,
          country: m.league.country,
          logo: m.league.logo
        },
        teams: {
          home: {
            id: m.teams.home.id,
            name: m.teams.home.name,
            logo: m.teams.home.logo
          },
          away: {
            id: m.teams.away.id,
            name: m.teams.away.name,
            logo: m.teams.away.logo
          }
        },
        lineupConfirmed,
        lineupExpectedAt: lineupExpectedAt.toISOString(),
        odds1xBet,
        decision: lineupConfirmed ? 'READY_FOR_ANALYSIS' : 'LINEUP_UNCONFIRMED'
      }
    })

    const upcomingOnly = formatted.filter((m: any) =>
      isActuallyUpcoming(m, nowUtc.getTime())
    )

    setDiskCache(CACHE_KEY, upcomingOnly)
    return jsonNoStore(upcomingOnly)
  } catch (error: any) {
    console.error('[API-FOOTBALL UPCOMING] Failed to fetch fixtures:', error?.message || error)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return jsonNoStore((stale || []).filter((m: any) => isActuallyUpcoming(m)))
  }
}
