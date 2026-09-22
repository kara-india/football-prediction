import { NextResponse } from 'next/server'

let cache: { data: any[]; timestamp: number } | null = null
const CACHE_TTL_MS = 30 * 1000 // 30 seconds for live matches

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
  const now = Date.now()
  if (cache && now - cache.timestamp < CACHE_TTL_MS) {
    return NextResponse.json(cache.data)
  }

  const apiKey = process.env.API_FOOTBALL_KEY || '073534f7111a37868a403c5cd51d83fa'
  const headers = { 'x-apisports-key': apiKey }

  try {
    const res = await fetch('https://v3.football.api-sports.io/fixtures?live=all', {
      headers,
      next: { revalidate: 30 }
    })
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

    cache = { data: eligible, timestamp: now }
    return NextResponse.json(eligible)
  } catch (error: any) {
    console.error('Failed to fetch live matches:', error)
    return NextResponse.json([])
  }
}
