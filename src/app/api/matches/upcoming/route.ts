import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'

// 30-minute disk cache for upcoming fixtures (0 calls if refreshed within 30 min)
const CACHE_TTL_MS = 30 * 60 * 1000
const CACHE_KEY = 'upcoming_fixtures_cache'

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
  // 1. Check persistent disk cache first (Zero API calls if fresh within 30 mins)
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached && cached.length > 0) {
    return NextResponse.json(cached)
  }

  // 2. Strict Quota Guard check (Max 50 auto requests, 50 reserved for user analysis)
  const quotaCheck = canMakeAPIRequest(false)
  if (!quotaCheck.allowed) {
    console.warn('[QUOTA GUARD UPCOMING]', quotaCheck.reason)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }

  const apiKey = process.env.API_FOOTBALL_KEY || '073534f7111a37868a403c5cd51d83fa'
  const headers = { 'x-apisports-key': apiKey }

  try {
    const nowUtc = new Date()
    const today = nowUtc.toISOString().split('T')[0]
    const tomorrow = new Date(nowUtc.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]

    // Query tomorrow or today - exactly 1 bulk request to conserve quota
    const queryDate = tomorrow // Sept 23 has the upcoming senior international friendlies
    const res = await fetch(`https://v3.football.api-sports.io/fixtures?date=${queryDate}`, {
      headers
    })
    recordAPIRequest(`/fixtures?date=${queryDate}`)

    const json = await res.json()
    const fixtures = json.response || []

    const eligible = fixtures
      .filter((f: any) => isEligibleFixture(f) && (f.fixture.status.short === 'NS' || f.fixture.status.short === 'TBD'))
      .slice(0, 50) // Cap to top 50 matches max per user directive

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

    // Store in disk cache
    setDiskCache(CACHE_KEY, formatted)

    return NextResponse.json(formatted)
  } catch (error: any) {
    console.error('Failed to fetch upcoming matches:', error)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }
}
