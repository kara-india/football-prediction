import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'

const CACHE_TTL_MS = 60 * 1000 // 60 seconds cache for live matches
const CACHE_KEY = 'live_matches_cache'

const ALLOWED_LEAGUES = new Set([39, 71, 135, 140, 78, 61, 94, 88, 128, 144, 2, 3, 1, 4, 5, 9, 6, 7, 10])

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
  // 1. Check disk cache first (Zero API calls if fresh within 60s)
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) {
    return NextResponse.json(cached)
  }

  // 2. Strict Quota Guard check (Max 50 automated requests/day)
  const quotaCheck = canMakeAPIRequest(false)
  if (!quotaCheck.allowed) {
    console.warn('[QUOTA GUARD LIVE]', quotaCheck.reason)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }

  const apiKey = process.env.API_FOOTBALL_KEY || '073534f7111a37868a403c5cd51d83fa'
  const headers = { 'x-apisports-key': apiKey }

  try {
    // 3. Exactly 1 request to fetch all global live matches
    const res = await fetch('https://v3.football.api-sports.io/fixtures?live=all', {
      headers
    })
    recordAPIRequest('/fixtures?live=all')

    const json = await res.json()
    const fixtures = json.response || []

    const eligible = fixtures
      .filter((f: any) => isEligibleFixture(f))
      .map((m: any) => ({
        id: m.fixture.id,
        minute: m.fixture.status.elapsed,
        status: m.fixture.status.short,
        statusLong: m.fixture.status.long,
        score: {
          home: m.goals.home ?? 0,
          away: m.goals.away ?? 0
        },
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
        events: m.events || []
      }))

    setDiskCache(CACHE_KEY, eligible)
    return NextResponse.json(eligible)
  } catch (error: any) {
    console.error('Failed to fetch live matches:', error)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }
}
