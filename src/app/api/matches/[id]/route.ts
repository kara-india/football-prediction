import { NextResponse } from 'next/server'
import { fetchApiFootball, extract1xBetOdds, extractProviderForecast } from '@/lib/apiFootball'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  const fixtureId = Number(params.id)
  if (!Number.isInteger(fixtureId) || fixtureId <= 0) {
    return NextResponse.json({ error: 'Invalid fixture id.' }, { status: 400 })
  }

  const cacheKey = `match_detail_${fixtureId}`
  const cached = getDiskCache<any>(cacheKey, 60 * 1000)
  if (cached) return NextResponse.json(cached)

  try {
    const fixtureJson = await fetchApiFootball(`/fixtures?id=${fixtureId}`, true)
    const fixture = fixtureJson.response?.[0]
    if (!fixture) {
      return NextResponse.json({ error: 'Fixture not found.' }, { status: 404 })
    }

    const homeId = Number(fixture.teams?.home?.id)
    const awayId = Number(fixture.teams?.away?.id)

    const [oddsResult, predictionResult, h2hResult] = await Promise.allSettled([
      fetchApiFootball(`/odds?fixture=${fixtureId}&bookmaker=6`, true),
      fetchApiFootball(`/predictions?fixture=${fixtureId}`, true),
      Number.isInteger(homeId) && Number.isInteger(awayId)
        ? fetchApiFootball(`/fixtures/headtohead?h2h=${homeId}-${awayId}`, true)
        : Promise.resolve({ response: [] }),
    ])

    const odds =
      oddsResult.status === 'fulfilled'
        ? extract1xBetOdds(oddsResult.value.response?.[0]?.bookmakers || [])
        : null

    const providerForecast =
      predictionResult.status === 'fulfilled'
        ? extractProviderForecast(predictionResult.value)
        : null

    const history =
      h2hResult.status === 'fulfilled'
        ? (h2hResult.value.response || []).slice(0, 10).map((match: any) => ({
            id: Number(match.fixture?.id),
            date: match.fixture?.date,
            status: match.fixture?.status?.short,
            homeTeam: match.teams?.home?.name,
            awayTeam: match.teams?.away?.name,
            homeScore: match.goals?.home,
            awayScore: match.goals?.away,
          }))
        : []

    const payload = {
      fixture: {
        id: fixtureId,
        kickoff: fixture.fixture?.date,
        venue: fixture.fixture?.venue?.name || 'TBD',
        status: fixture.fixture?.status?.short || 'TBD',
        statusLong: fixture.fixture?.status?.long || 'Unknown',
        minute: fixture.fixture?.status?.elapsed ?? null,
        referee: fixture.fixture?.referee || null,
        league: fixture.league || null,
        teams: fixture.teams || null,
        score: fixture.goals || null,
        events: fixture.events || [],
        statistics: fixture.statistics || [],
        lineups: fixture.lineups || [],
      },
      odds1xBet: odds
        ? {
            home: odds.home,
            draw: odds.draw,
            away: odds.away,
            over25: odds.over25,
            under25: odds.under25,
          }
        : null,
      oddsUpdatedAt: odds?.sourceTimestamp ?? null,
      forecast: providerForecast,
      forecastSource: providerForecast ? 'API-Football provider forecast' : null,
      history,
      generatedAt: new Date().toISOString(),
    }

    setDiskCache(cacheKey, payload)
    return NextResponse.json(payload)
  } catch (error) {
    console.error(`[MATCH DETAIL] Failed for fixture ${fixtureId}`, error)
    return NextResponse.json(
      { error: 'Unable to fetch live match detail from the upstream provider.' },
      { status: 502 },
    )
  }
}
