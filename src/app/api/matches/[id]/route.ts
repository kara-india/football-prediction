import { NextResponse } from 'next/server'
import { fetchApiFootball, extract1xBetOdds, extractProviderForecast, findApiFootballFixtureByTeams, fetch1xBetOddsForFixture, fetch1xBetLiveOddsFromPulseScore } from '@/lib/apiFootball'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import { fetchSofaEvent, fetchSofaEventExtras, sofaStatus } from '@/lib/sofaScore'
import { fetchEspnSummaryWithForecast } from '@/lib/espn'
import { computeChampionDecision } from '@/lib/championDecision'

function sofaStatistics(raw: any[]) {
  const home: any[] = []
  const away: any[] = []
  for (const period of raw || []) {
    for (const group of period.groups || []) {
      for (const item of group.statisticsItems || []) {
        const type = item.name || item.key
        if (item.homeValue !== undefined) home.push({ type, value: item.homeValue })
        else if (item.home !== undefined) home.push({ type, value: item.home })
        if (item.awayValue !== undefined) away.push({ type, value: item.awayValue })
        else if (item.away !== undefined) away.push({ type, value: item.away })
      }
    }
  }
  return [
    { team: { id: Number(raw?.[0]?.homeTeam?.id || 0) }, statistics: home },
    { team: { id: Number(raw?.[0]?.awayTeam?.id || 0) }, statistics: away },
  ]
}

function sofaLineups(raw: any, homeTeam: any, awayTeam: any) {
  if (!raw?.home || !raw?.away) return []
  const map = (side: any, team: any) => ({
    team: { id: Number(team.id), name: team.name },
    formation: side.formation || 'TBD',
    startXI: (side.players || []).filter((p: any) => p.substitute !== true).slice(0, 11).map((p: any) => ({
      player: { id: p.player?.id, name: p.player?.name, number: p.shirtNumber, pos: p.position },
    })),
    substitutes: (side.substitutes || []).map((p: any) => ({
      player: { id: p.player?.id, name: p.player?.name, number: p.shirtNumber, pos: p.position },
    })),
  })
  return [map(raw.home, homeTeam), map(raw.away, awayTeam)]
}

function sofaEvents(raw: any[]) {
  return (raw || []).map((event: any) => ({
    time: { elapsed: event.time || event.timeSeconds ? Math.floor(Number(event.time || 0)) : null },
    team: { id: event.isHome ? undefined : undefined, name: event.isHome ? undefined : undefined },
    player: { id: event.player?.id, name: event.player?.name || event.playerName },
    type: event.incidentType || 'event',
    detail: event.incidentClass || event.incidentType || 'event',
    comments: event.reason || '',
  }))
}

function sofaH2H(raw: any[]) {
  return (raw || []).slice(0, 10).map((match: any) => ({
    id: Number(match.id),
    date: match.startTimestamp ? new Date(match.startTimestamp * 1000).toISOString() : '',
    status: match.status?.type || 'unknown',
    homeTeam: match.homeTeam?.name || 'Home',
    awayTeam: match.awayTeam?.name || 'Away',
    homeScore: match.homeScore?.current ?? match.homeScore?.display ?? null,
    awayScore: match.awayScore?.current ?? match.awayScore?.display ?? null,
  }))
}

export async function GET(_request: Request, { params }: { params: { id: string } }) {
  const rawId = params.id
  const espnMatch = rawId.match(/^espn:([^:]+):(\d+)$/)
  if (espnMatch) {
    try {
      const { summary, forecast, forecastSource } = await fetchEspnSummaryWithForecast(espnMatch[1], espnMatch[2])
      const header = summary.header?.competitions?.[0] || summary.header?.competitions?.[0]
      const competitors = Object.fromEntries((header?.competitors || []).map((c:any)=>[c.homeAway,c]))
      const home = competitors.home?.team || {}
      const away = competitors.away?.team || {}
      const kickoff = summary.header?.competitions?.[0]?.date || summary.header?.season?.startDate || new Date().toISOString()
      const apiFixture = await findApiFootballFixtureByTeams(home.displayName || home.name || '', away.displayName || away.name || '', kickoff.slice(0,10))
      const apiOdds = apiFixture?.fixture?.id ? await fetch1xBetOddsForFixture(Number(apiFixture.fixture.id)) : null
      const payload = { fixture: { id: Number(espnMatch[2]), kickoff, venue: summary.gameInfo?.venue?.fullName || 'TBD', status: summary.header?.competitions?.[0]?.status?.type?.state === 'in' ? 'LIVE' : summary.header?.competitions?.[0]?.status?.type?.state === 'post' ? 'FT' : 'NS', statusLong: summary.header?.competitions?.[0]?.status?.type?.detail || 'Unknown', minute: null, referee: summary.gameInfo?.officials?.[0]?.fullName || null, league: { name: summary.header?.league?.name || espnMatch[1] }, teams: { home: { id: Number(home.id||0), name: home.displayName||home.name||'Home', logo: home.logo }, away: { id: Number(away.id||0), name: away.displayName||away.name||'Away', logo: away.logo } }, score: { home: Number(competitors.home?.score||0), away: Number(competitors.away?.score||0) }, events: summary.keyEvents || summary.plays || [], statistics: summary.boxscore?.teams || [], lineups: summary.rosters || [] }, odds1xBet: apiOdds ? { home: apiOdds.home, draw: apiOdds.draw, away: apiOdds.away, over25: apiOdds.over25, under25: apiOdds.under25 } : null, oddsUpdatedAt: apiOdds?.sourceTimestamp ?? null, forecast, forecastSource, history: (summary.seasonseries || []).filter((m:any)=>m?.id || m?.competitions?.length).slice(0,10).map((m:any)=>({id:Number(m.id||0),date:m.date||'',status:m.status?.type?.state||'unknown',homeTeam:m.competitions?.[0]?.competitors?.find((c:any)=>c.homeAway==='home')?.team?.displayName||'',awayTeam:m.competitions?.[0]?.competitors?.find((c:any)=>c.homeAway==='away')?.team?.displayName||'',homeScore:Number(m.competitions?.[0]?.competitors?.find((c:any)=>c.homeAway==='home')?.score||0),awayScore:Number(m.competitions?.[0]?.competitors?.find((c:any)=>c.homeAway==='away')?.score||0)})),generatedAt:new Date().toISOString(),fixtureSource:'ESPN' }
      return NextResponse.json(payload)
    } catch (error) { console.error('[MATCH DETAIL] ESPN fallback failed',error); return NextResponse.json({error:'Unable to fetch ESPN fixture detail.'},{status:502}) }
  }
  const fixtureId = Number(params.id)
  if (!Number.isInteger(fixtureId) || fixtureId <= 0) return NextResponse.json({ error: 'Invalid fixture id.' }, { status: 400 })
  const cacheKey = `match_detail_${fixtureId}`
  const cached = getDiskCache<any>(cacheKey, 60 * 1000)
  if (cached) return NextResponse.json(cached)

  try {
    const fixtureJson = await fetchApiFootball(`/fixtures?id=${fixtureId}`, true)
    const fixture = fixtureJson.response?.[0]
    if (!fixture) return NextResponse.json({ error: 'Fixture not found.' }, { status: 404 })
    const homeId = Number(fixture.teams?.home?.id)
    const awayId = Number(fixture.teams?.away?.id)
    let liveOdds: any = null
    try {
      const liveOddsPayload = await fetchApiFootball('/odds/live', true)
      const liveOddsEvent = (liveOddsPayload.response || []).find((event: any) => Number(event.fixture?.id) === fixtureId)
      liveOdds = liveOddsEvent ? extract1xBetOdds(liveOddsEvent.bookmakers || []) : null
    } catch (error) {
      console.warn('[MATCH DETAIL] Live 1xBet odds lookup failed', fixtureId, error)
    }

    const [oddsResult, predictionResult, h2hResult] = await Promise.allSettled([
      fetchApiFootball(`/odds?fixture=${fixtureId}`, true),
      fetchApiFootball(`/predictions?fixture=${fixtureId}`, true),
      Number.isInteger(homeId) && Number.isInteger(awayId) ? fetchApiFootball(`/fixtures/headtohead?h2h=${homeId}-${awayId}`, true) : Promise.resolve({ response: [] }),
    ])
    const prematchOdds = oddsResult.status === 'fulfilled' ? extract1xBetOdds(oddsResult.value.response?.[0]?.bookmakers || []) : null
    let odds = liveOdds || prematchOdds
    if (!odds && fixture.fixture?.status?.short && ['1H', '2H', 'ET', 'P'].includes(String(fixture.fixture.status.short))) {
      const pulseScoreOdds = await fetch1xBetLiveOddsFromPulseScore([{
        id: fixtureId,
        home: String(fixture.teams?.home?.name || ''),
        away: String(fixture.teams?.away?.name || ''),
        kickoff: fixture.fixture?.date,
      }])
      odds = pulseScoreOdds.get(fixtureId) || null
    }
    const providerForecast = predictionResult.status === 'fulfilled' ? extractProviderForecast(predictionResult.value) : null
    const championDecision = computeChampionDecision({
      fixtureId,
      minute: Number(fixture.fixture?.status?.elapsed || 0),
      scoreHome: Number(fixture.goals?.home || 0),
      scoreAway: Number(fixture.goals?.away || 0),
      status: String(fixture.fixture?.status?.short || ''),
      homeTeam: String(fixture.teams?.home?.name || 'Home'),
      awayTeam: String(fixture.teams?.away?.name || 'Away'),
      forecast: providerForecast ? { home: providerForecast.home, draw: providerForecast.draw, away: providerForecast.away } : null,
      odds: odds ? { home: odds.home, draw: odds.draw, away: odds.away, over25: odds.over25, under25: odds.under25 } : null,
      oddsUpdatedAt: odds?.sourceTimestamp ?? null,
    })
    const history = h2hResult.status === 'fulfilled' ? (h2hResult.value.response || []).slice(0, 10).map((match: any) => ({ id: Number(match.fixture?.id), date: match.fixture?.date, status: match.fixture?.status?.short, homeTeam: match.teams?.home?.name, awayTeam: match.teams?.away?.name, homeScore: match.goals?.home, awayScore: match.goals?.away })) : []
    const payload = { fixture: { id: fixtureId, kickoff: fixture.fixture?.date, venue: fixture.fixture?.venue?.name || 'TBD', status: fixture.fixture?.status?.short || 'TBD', statusLong: fixture.fixture?.status?.long || 'Unknown', minute: fixture.fixture?.status?.elapsed ?? null, referee: fixture.fixture?.referee || null, league: fixture.league || null, teams: fixture.teams || null, score: fixture.goals || null, events: fixture.events || [], statistics: fixture.statistics || [], lineups: fixture.lineups || [] }, odds1xBet: odds ? { home: odds.home, draw: odds.draw, away: odds.away, over25: odds.over25, under25: odds.under25 } : null, oddsUpdatedAt: odds?.sourceTimestamp ?? null, forecast: providerForecast, forecastSource: providerForecast ? 'API-Football provider forecast' : null, championDecision, history, generatedAt: new Date().toISOString(), fixtureSource: 'API-Football' }
    setDiskCache(cacheKey, payload)
    return NextResponse.json(payload)
  } catch (error) {
    console.error(`[MATCH DETAIL] API-Football failed for fixture ${fixtureId}, trying SofaScore`, error)
    try {
      const event = await fetchSofaEvent(fixtureId)
      const extras = await fetchSofaEventExtras(fixtureId)
      const home = event.homeTeam || {}
      const away = event.awayTeam || {}
      const homeTeam = { id: Number(home.id), name: home.name || 'Home', logo: undefined }
      const awayTeam = { id: Number(away.id), name: away.name || 'Away', logo: undefined }
      const payload = {
        fixture: {
          id: fixtureId,
          kickoff: event.startTimestamp ? new Date(event.startTimestamp * 1000).toISOString() : new Date().toISOString(),
          venue: event.venue?.name || 'TBD',
          status: sofaStatus(event),
          statusLong: event.status?.description || event.status?.type || 'Unknown',
          minute: event.status?.type === 'inprogress' && event.time?.currentPeriodStartTimestamp ? Math.max(0, Math.floor((Date.now() - event.time.currentPeriodStartTimestamp * 1000) / 60000)) : null,
          referee: event.referee?.name || null,
          league: { id: Number(event.tournament?.uniqueTournament?.id || 0), name: event.tournament?.uniqueTournament?.name || event.tournament?.name || 'Competition', country: event.tournament?.category?.name },
          teams: { home: homeTeam, away: awayTeam },
          score: { home: event.homeScore?.current ?? event.homeScore?.display ?? null, away: event.awayScore?.current ?? event.awayScore?.display ?? null },
          events: sofaEvents(extras.incidents),
          statistics: sofaStatistics(extras.statistics),
          lineups: sofaLineups(extras.lineups, homeTeam, awayTeam),
        },
        odds1xBet: null,
        oddsUpdatedAt: null,
        forecast: null,
        forecastSource: null,
        history: sofaH2H(extras.h2h),
        generatedAt: new Date().toISOString(),
        fixtureSource: 'SofaScore',
      }
      setDiskCache(cacheKey, payload)
      return NextResponse.json(payload)
    } catch (fallbackError) {
      console.error('[MATCH DETAIL] SofaScore fallback failed', fallbackError)
      return NextResponse.json({ error: 'Unable to fetch live match detail from available providers.' }, { status: 502 })
    }
  }
}
