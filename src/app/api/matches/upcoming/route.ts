import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'

const CACHE_TTL_MS = 15 * 60 * 1000
const CACHE_KEY = 'upcoming_fixtures_v2'

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

function extract1xBet(bookmakers: any[]): {
  home: number | null
  draw: number | null
  away: number | null
  over25: number | null
  under25: number | null
} | null {
  const bookmaker = (bookmakers || []).find(
    (b: any) => Number(b.id) === 6 || /1xBet/i.test(String(b.name || '')),
  )
  if (!bookmaker) return null

  const markets = bookmaker.bets || []
  const winner = markets.find((b: any) => /match winner|1x2/i.test(String(b.name || '')))
  const totals = markets.find((b: any) =>
    /over\/under|total goals|goals over\/under/i.test(String(b.name || '')),
  )

  const getOdd = (market: any, labels: RegExp[]): number | null => {
    const value = market?.values?.find((v: any) =>
      labels.some((label) => label.test(String(v.value || ''))),
    )
    const odd = Number(value?.odd)
    return Number.isFinite(odd) && odd > 1 ? odd : null
  }

  const result = {
    home: getOdd(winner, [/^home$/i]),
    draw: getOdd(winner, [/^draw$/i]),
    away: getOdd(winner, [/^away$/i]),
    over25: getOdd(totals, [/^over 2\.5$/i, /^over$/i]),
    under25: getOdd(totals, [/^under 2\.5$/i, /^under$/i]),
  }

  return Object.values(result).some((v) => v !== null) ? result : null
}

async function fetchJson(url: string, headers: HeadersInit) {
  const res = await fetch(url, { headers, cache: 'no-store' })
  const json = await res.json()
  if (!res.ok) {
    throw new Error(`Upstream request failed: ${res.status}`)
  }
  return json
}

export async function GET() {
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) return NextResponse.json(cached)

  const quotaCheck = await canMakeAPIRequest(false)
  if (!quotaCheck.allowed) {
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }

  const API_KEY = process.env.API_FOOTBALL_KEY
  if (!API_KEY) {
    return NextResponse.json(
      { error: 'API_FOOTBALL_KEY environment variable is not configured.' },
      { status: 500 },
    )
  }

  const headers = { 'x-apisports-key': API_KEY }
  const today = new Date()
  const todayDate = today.toISOString().slice(0, 10)
  const tomorrowDate = new Date(today.getTime() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

  try {
    const fixtureUrl =
      `https://v3.football.api-sports.io/fixtures?from=${todayDate}&to=${tomorrowDate}`
    const fixtureJson = await fetchJson(fixtureUrl, headers)
    recordAPIRequest(`/fixtures?from=${todayDate}&to=${tomorrowDate}`)

    const fixtures = (fixtureJson.response || [])
      .filter((f: any) =>
        isEligibleFixture(f) &&
        ['NS', 'TBD'].includes(f.fixture?.status?.short),
      )

    const oddsByFixture = new Map<number, ReturnType<typeof extract1xBet>>()

    // Odds are fetched from the real API-Football bookmaker feed. Never synthesize
    // prices when 1xBet is absent. One request per date keeps quota bounded.
    for (const date of [todayDate, tomorrowDate]) {
      const oddsUrl = `https://v3.football.api-sports.io/odds?date=${date}&bookmaker=6`
      const oddsJson = await fetchJson(oddsUrl, headers)
      recordAPIRequest(`/odds?date=${date}&bookmaker=6`)

      for (const event of oddsJson.response || []) {
        const fixtureId = Number(event.fixture?.id)
        if (Number.isFinite(fixtureId)) {
          oddsByFixture.set(fixtureId, extract1xBet(event.bookmakers || []))
        }
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
        odds1xBet,
        decision: odds1xBet ? 'FORECAST_AVAILABLE' : 'ODDS_UNAVAILABLE',
      }
    })

    setDiskCache(CACHE_KEY, formatted)
    return NextResponse.json(formatted)
  } catch (error) {
    console.error('Failed to fetch upcoming matches:', error)
    const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
    return NextResponse.json(stale || [])
  }
}
