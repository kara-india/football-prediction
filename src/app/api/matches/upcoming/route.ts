import { NextResponse } from 'next/server'

// Cache for 2 minutes to respect API rate limits
let cache: { data: any[]; timestamp: number } | null = null
const CACHE_TTL_MS = 2 * 60 * 1000

const ALLOWED_LEAGUES = new Set([39, 71, 135, 140, 78, 61, 94, 88, 128, 144, 2, 3, 1, 4, 5, 9, 6, 7, 10])

// Exclude youth & women's fixtures per specification
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
    const today = new Date().toISOString().split('T')[0]
    // Check today and tomorrow
    const tomorrowDate = new Date(Date.now() + 24 * 60 * 60 * 1000)
    const tomorrow = tomorrowDate.toISOString().split('T')[0]

    const datesToQuery = [today, tomorrow]
    const allMatches: any[] = []

    for (const d of datesToQuery) {
      try {
        const res = await fetch(`https://v3.football.api-sports.io/fixtures?date=${d}`, {
          headers,
          next: { revalidate: 120 }
        })
        const json = await res.json()
        const fixtures = json.response || []
        
        for (const f of fixtures) {
          if (isEligibleFixture(f) && (f.fixture.status.short === 'NS' || f.fixture.status.short === 'TBD')) {
            allMatches.push(f)
          }
        }
      } catch (err) {
        console.error(`Error querying fixtures for ${d}:`, err)
      }
    }

    // Now enrich matches with 1xBet odds where available
    const enriched = await Promise.all(
      allMatches.slice(0, 15).map(async (m) => {
        const fixtureId = m.fixture.id
        const kickoff = new Date(m.fixture.date)
        
        // Expected lineups are submitted exactly 60 minutes before kickoff
        const lineupExpectedAt = new Date(kickoff.getTime() - 60 * 60 * 1000)
        const lineupConfirmed = Boolean(
          m.lineups && m.lineups.length >= 2 && m.lineups[0].startXI?.length === 11
        )

        let odds1xBet: { home: number | null; draw: number | null; away: number | null } | null = null

        try {
          const oddsRes = await fetch(`https://v3.football.api-sports.io/odds?fixture=${fixtureId}`, {
            headers,
            next: { revalidate: 300 }
          })
          const oddsJson = await oddsRes.json()
          const bookmakers = oddsJson.response?.[0]?.bookmakers || []
          const onex = bookmakers.find((b: any) => b.id === 6 || /1x/i.test(b.name))

          if (onex) {
            const mw = onex.bets?.find((b: any) => b.name === 'Match Winner')
            if (mw) {
              const h = mw.values.find((v: any) => v.value === 'Home')?.odd
              const d = mw.values.find((v: any) => v.value === 'Draw')?.odd
              const a = mw.values.find((v: any) => v.value === 'Away')?.odd
              odds1xBet = {
                home: h ? parseFloat(h) : null,
                draw: d ? parseFloat(d) : null,
                away: a ? parseFloat(a) : null
              }
            }
          }
        } catch {
          // Keep null if unavailable
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
    )

    cache = { data: enriched, timestamp: now }
    return NextResponse.json(enriched)
  } catch (error: any) {
    console.error('Failed to fetch upcoming matches:', error)
    return NextResponse.json({ error: error.message || 'Failed to fetch matches' }, { status: 500 })
  }
}
