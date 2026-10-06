import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { fetchApiFootball, extract1xBetOdds, resolve1xBetBookmakerId } from '@/lib/apiFootball'
import { fetchSofaScheduled, isSofaAllowedEvent, sofaMappedFixture } from '@/lib/sofaScore'

const CACHE_TTL_MS = 15 * 60 * 1000
const CACHE_KEY = 'upcoming_fixtures_v3'
const ALLOWED_LEAGUES = new Set([39, 140, 135, 78, 61, 88, 94, 71, 128, 2, 3, 5])
const FIXTURE_QUERY_LEAGUES = Array.from(ALLOWED_LEAGUES)

function isEligibleFixture(m: any): boolean {
  const leagueId = m.league?.id
  if (!ALLOWED_LEAGUES.has(leagueId)) return false
  const excluded = /\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|Reserves)\b/i
  return !(excluded.test(m.teams?.home?.name || '') || excluded.test(m.teams?.away?.name || '') || excluded.test(m.league?.name || ''))
}

async function sofaFallback(today: Date) {
  const dates = [today, new Date(today.getTime() + 24 * 60 * 60 * 1000)]
  const events = (await Promise.all(dates.map((date) => fetchSofaScheduled(date.toISOString().slice(0, 10)))))
    .flat()
    .filter(isSofaAllowedEvent)
    .filter((event) => ['notstarted', 'postponed'].includes(String(event.status?.type || '')))
  const unique = Array.from(new Map(events.map((event) => [event.id, event])).values())
  return unique.slice(0, 50).map(sofaMappedFixture)
}

export async function GET() {
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) return NextResponse.json(cached)

  const today = new Date()
  if (!process.env.API_FOOTBALL_KEY) {
    try {
      const fallback = await sofaFallback(today)
      setDiskCache(CACHE_KEY, fallback)
      return NextResponse.json(fallback, { headers: { 'x-data-source': 'sofascore-fallback' } })
    } catch (error) {
      return NextResponse.json({ error: 'UPSTREAM_UNAVAILABLE', detail: error instanceof Error ? error.message : 'No fixture provider available' }, { status: 502 })
    }
  }

  const todayDate = today.toISOString().slice(0, 10)
  const tomorrowDate = new Date(today.getTime() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

  try {
    const fixtures: any[] = []
    const fixtureErrors: string[] = []
    const season = today.getUTCFullYear()

    for (const leagueId of FIXTURE_QUERY_LEAGUES) {
      try {
        const fixtureJson = await fetchApiFootball(`/fixtures?league=${leagueId}&season=${season}&from=${todayDate}&to=${tomorrowDate}`, true)
        fixtures.push(...(fixtureJson.response || []))
      } catch (error) {
        fixtureErrors.push(`league=${leagueId}: ${error instanceof Error ? error.message : 'request failed'}`)
      }
    }

    const eligible = fixtures.filter((f: any) => isEligibleFixture(f) && ['NS', 'TBD'].includes(f.fixture?.status?.short))
    if (eligible.length === 0 && fixtureErrors.length === FIXTURE_QUERY_LEAGUES.length) {
      throw new Error(fixtureErrors.join(' | '))
    }

    const oddsByFixture = new Map<number, any>()
    const bookmakerId = await resolve1xBetBookmakerId()
    if (bookmakerId) {
      const groups = new Map<string, { leagueId: number; season: number; date: string }>()
      for (const fixture of fixtures) {
        const leagueId = Number(fixture.league?.id)
        const fixtureSeason = Number(fixture.league?.season)
        const date = String(fixture.fixture?.date || '').slice(0, 10)
        if (Number.isInteger(leagueId) && Number.isInteger(fixtureSeason) && date) {
          groups.set(`${leagueId}:${fixtureSeason}:${date}`, { leagueId, season: fixtureSeason, date })
        }
      }
      for (const group of Array.from(groups.values())) {
        try {
          const oddsJson = await fetchApiFootball(`/odds?league=${group.leagueId}&season=${group.season}&date=${group.date}&bookmaker=${bookmakerId}`, true)
          for (const event of oddsJson.response || []) {
            const fixtureId = Number(event.fixture?.id)
            if (Number.isFinite(fixtureId)) oddsByFixture.set(fixtureId, extract1xBetOdds(event.bookmakers || []))
          }
        } catch (error) {
          console.warn('[1XBET ODDS] Failed', error)
        }
      }
    }

    const formatted = fixtures.slice(0, 50).map((m: any) => {
      const fixtureId = Number(m.fixture.id)
      const kickoff = new Date(m.fixture.date)
      const odds1xBet = oddsByFixture.get(fixtureId) || null
      return {
        id: fixtureId,
        kickoff: m.fixture.date,
        venue: m.fixture.venue?.name || 'TBD',
        status: m.fixture.status.short,
        statusLong: m.fixture.status.long,
        league: { id: m.league.id, name: m.league.name, country: m.league.country, logo: m.league.logo },
        teams: {
          home: { id: m.teams.home.id, name: m.teams.home.name, logo: m.teams.home.logo },
          away: { id: m.teams.away.id, name: m.teams.away.name, logo: m.teams.away.logo },
        },
        lineupConfirmed: false,
        lineupExpectedAt: new Date(kickoff.getTime() - 60 * 60 * 1000).toISOString(),
        odds1xBet: odds1xBet ? { home: odds1xBet.home, draw: odds1xBet.draw, away: odds1xBet.away, over25: odds1xBet.over25, under25: odds1xBet.under25 } : null,
        oddsUpdatedAt: odds1xBet?.sourceTimestamp ?? null,
        decision: odds1xBet ? 'FORECAST_AVAILABLE' : 'ODDS_UNAVAILABLE',
        fixtureSource: 'API-Football',
      }
    })

    if (formatted.length === 0) throw new Error('API-Football returned no current fixtures')
    setDiskCache(CACHE_KEY, formatted)
    return NextResponse.json(formatted, { headers: fixtureErrors.length ? { 'x-data-warning': 'one-or-more-competition-queries-failed' } : undefined })
  } catch (error) {
    console.error('API-Football unavailable, trying SofaScore fallback:', error)
    try {
      const fallback = await sofaFallback(today)
      if (fallback.length > 0) {
        setDiskCache(CACHE_KEY, fallback)
        return NextResponse.json(fallback, { headers: { 'x-data-source': 'sofascore-fallback', 'x-primary-provider-warning': 'api-football-unavailable' } })
      }
    } catch (fallbackError) {
      console.error('SofaScore fallback failed:', fallbackError)
    }
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    if (stale !== null) return NextResponse.json(stale, { headers: { 'x-data-state': 'stale' } })
    return NextResponse.json({ error: 'UPSTREAM_UNAVAILABLE', detail: error instanceof Error ? error.message : 'Fixture providers unavailable' }, { status: 502 })
  }
}
