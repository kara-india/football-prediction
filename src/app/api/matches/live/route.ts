import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { fetchApiFootball, extract1xBetOdds } from '@/lib/apiFootball'

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

  try {
    // Browser-driven live refreshes use the user reservation pool.
    const json = await fetchApiFootball('/fixtures?live=all', true)
    const fixtures = json.response || []

    const eligible = fixtures.filter((f: any) => isEligibleFixture(f))

    let liveOddsByFixture = new Map<number, any>()
    if (eligible.length > 0) {
      try {
        const oddsJson = await fetchApiFootball('/odds/live', true)
        for (const event of oddsJson.response || []) {
          const fixtureId = Number(event.fixture?.id)
          if (Number.isFinite(fixtureId)) {
            liveOddsByFixture.set(fixtureId, extract1xBetOdds(event.bookmakers || []))
          }
        }
      } catch (error) {
        console.warn('[1XBET LIVE ODDS] Unavailable', error)
      }
    }

    const eligibleMapped = eligible.map((m: any) => ({
        id: m.fixture.id,
        kickoff: m.fixture.date,
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
        odds1xBet: liveOddsByFixture.get(Number(m.fixture.id)) || null,
        events: m.events || []
      }))

    setDiskCache(CACHE_KEY, eligibleMapped)
    return NextResponse.json(eligibleMapped)
  } catch (error: any) {
    console.error('Failed to fetch live matches:', error)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }
}
