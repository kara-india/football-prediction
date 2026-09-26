import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { fetchApiFootball, extract1xBetOdds } from '@/lib/apiFootball'

const CACHE_TTL_MS = 15 * 60 * 1000
const CACHE_KEY = 'upcoming_fixtures_v3'

const ALLOWED_LEAGUES = new Set([
  39, 71, 135, 140, 78, 61, 94, 88, 128, 144,
  2, 3, 1, 4, 5, 9, 6, 7, 10,
])

function isEligibleFixture(m: any): boolean {
  const leagueId = m.league?.id
  if (!ALLOWED_LEAGUES.has(leagueId)) return false

  const home = m.teams?.home?.name || ''
  const away = m.teams?.away?.name || ''
  const leagueName = m.league?.name || ''
  const excluded = /\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|Reserves)\b/i

  return !(excluded.test(home) || excluded.test(away) || excluded.test(leagueName))
}

export async function GET() {
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) return NextResponse.json(cached)

  if (!process.env.API_FOOTBALL_KEY) {
    return NextResponse.json(
      { error: 'API_FOOTBALL_KEY environment variable is not configured.' },
      { status: 500 },
    )
  }

  const today = new Date()
  const todayDate = today.toISOString().slice(0, 10)
  const tomorrowDate = new Date(today.getTime() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

  try {
    const fixtureJson = await fetchApiFootball(
      `/fixtures?from=${todayDate}&to=${tomorrowDate}`,
      false,
    )

    const fixtures = (fixtureJson.response || [])
      .filter((f: any) =>
        isEligibleFixture(f) &&
        ['NS', 'TBD'].includes(f.fixture?.status?.short),
      )

    const oddsByFixture = new Map<number, any>()

    // API-Football retains real bookmaker odds for the recent pre-match window.
    // We query each date once and never synthesize an absent 1xBet price.
    for (const date of [todayDate, tomorrowDate]) {
      try {
        const oddsJson = await fetchApiFootball(`/odds?date=${date}`, false)
        for (const event of oddsJson.response || []) {
          const fixtureId = Number(event.fixture?.id)
          if (Number.isFinite(fixtureId)) {
            oddsByFixture.set(fixtureId, extract1xBetOdds(event.bookmakers || []))
          }
        }
      } catch (error) {
        console.warn(`[1XBET ODDS] Failed to fetch odds for ${date}`, error)
      }
    }

    const formatted = fixtures.slice(0, 50).map((m: any) => {
      const fixtureId = Number(m.fixture.id)
      const kickoff = new Date(m.fixture.date)
      const lineupExpectedAt = new Date(kickoff.getTime() - 60 * 60 * 1000)
      const odds1xBet = oddsByFixture.get(fixtureId) || null

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
          logo: m.league.logo,
        },
        teams: {
          home: {
            id: m.teams.home.id,
            name: m.teams.home.name,
            logo: m.teams.home.logo,
          },
          away: {
            id: m.teams.away.id,
            name: m.teams.away.name,
            logo: m.teams.away.logo,
          },
        },
        lineupConfirmed: false,
        lineupExpectedAt: lineupExpectedAt.toISOString(),
        odds1xBet: odds1xBet
          ? {
              home: odds1xBet.home,
              draw: odds1xBet.draw,
              away: odds1xBet.away,
              over25: odds1xBet.over25,
              under25: odds1xBet.under25,
            }
          : null,
        oddsUpdatedAt: odds1xBet?.sourceTimestamp ?? null,
        decision: odds1xBet ? 'FORECAST_AVAILABLE' : 'ODDS_UNAVAILABLE',
      }
    })

    setDiskCache(CACHE_KEY, formatted)
    return NextResponse.json(formatted)
  } catch (error) {
    console.error('Failed to fetch upcoming matches:', error)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    if (stale !== null) {
      return NextResponse.json(stale, {
        headers: { 'x-data-state': 'stale' },
      })
    }
    return NextResponse.json(
      {
        error: 'UPSTREAM_UNAVAILABLE',
        detail: error instanceof Error ? error.message : 'API-Football request failed',
      },
      { status: 502 },
    )
  }
}
