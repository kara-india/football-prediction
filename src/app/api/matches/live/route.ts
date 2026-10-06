import { NextResponse } from 'next/server'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'
import {
  fetchApiFootball,
  extract1xBetOdds,
  fetch1xBetLiveOddsFromPulseScore,
  fetch1xBetLiveOddsFromOddsApi,
} from '@/lib/apiFootball'
import { fetchSofaLive, isSofaAllowedEvent, sofaMappedFixture } from '@/lib/sofaScore'
import { fetchEspnLiveEvents, espnMappedFixture } from '@/lib/espn'

const CACHE_TTL_MS = 60 * 1000
const CACHE_KEY = 'live_matches_cache'

function isEligibleFixture(m: any): boolean {
  // Live mode mirrors all senior provider fixtures so available 1xBet live
  // markets can be matched to the exact same terminal fixture.
  const excluded = /\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|W|Reserves)\b/i
  return !(
    excluded.test(m.teams?.home?.name || '') ||
    excluded.test(m.teams?.away?.name || '') ||
    excluded.test(m.league?.name || '')
  )
}

async function espnFallback() {
  const fixtures = (await fetchEspnLiveEvents()).map(({ event, league, name }) => espnMappedFixture(event, league, name))
  const pulseFixtures = fixtures.map((fixture: any) => ({
    id: Number(fixture.providerEventId),
    home: String(fixture.teams?.home?.name || ''),
    away: String(fixture.teams?.away?.name || ''),
    kickoff: fixture.kickoff,
  })).filter((fixture: any) => Number.isFinite(fixture.id))
  const pulseOdds = await fetch1xBetLiveOddsFromPulseScore(pulseFixtures)
  return fixtures.map((fixture: any) => ({
    ...fixture,
    odds1xBet: pulseOdds.get(Number(fixture.providerEventId)) || null,
    oddsUpdatedAt: pulseOdds.get(Number(fixture.providerEventId))?.sourceTimestamp || null,
  }))
}

async function sofaFallback() {
  const events = (await fetchSofaLive()).filter(isSofaAllowedEvent)
  return events.map(sofaMappedFixture)
}

export async function GET() {
  const cached = getDiskCache<any[]>(CACHE_KEY, CACHE_TTL_MS)
  if (cached !== null) return NextResponse.json(cached)

  try {
    const json = await fetchApiFootball('/fixtures?live=all', true)
    const eligible = (json.response || []).filter((f: any) => isEligibleFixture(f))
    const liveOddsByFixture = new Map<number, any>()

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
        console.warn('[1XBET LIVE ODDS] API-Football unavailable', error)
      }
    }

    const unresolvedFixtures = eligible
      .filter((m: any) => !liveOddsByFixture.get(Number(m.fixture.id)))
      .map((m: any) => ({
        id: Number(m.fixture.id),
        home: String(m.teams?.home?.name || ''),
        away: String(m.teams?.away?.name || ''),
        kickoff: m.fixture?.date,
      }))

    // PulseScore is a direct 1xBet live feed and is preferred over generic
    // bookmaker aggregation because it covers the full 1xBet live soccer board.
    const pulseScoreOdds = await fetch1xBetLiveOddsFromPulseScore(unresolvedFixtures)
    pulseScoreOdds.forEach((odds, fixtureId) => {
      if (!liveOddsByFixture.get(fixtureId)) liveOddsByFixture.set(fixtureId, odds)
    })

    const stillUnresolved = unresolvedFixtures.filter(
      (fixture: { id: number; home: string; away: string; kickoff?: string }) =>
        !liveOddsByFixture.get(Number(fixture.id)),
    )
    const fallbackOdds = await fetch1xBetLiveOddsFromOddsApi(stillUnresolved)
    fallbackOdds.forEach((odds, fixtureId) => {
      if (!liveOddsByFixture.get(fixtureId)) liveOddsByFixture.set(fixtureId, odds)
    })

    const mapped = eligible.map((m: any) => ({
      id: m.fixture.id,
      kickoff: m.fixture.date,
      minute: m.fixture.status.elapsed,
      status: m.fixture.status.short,
      statusLong: m.fixture.status.long,
      score: { home: m.goals.home ?? 0, away: m.goals.away ?? 0 },
      league: { id: m.league.id, name: m.league.name, country: m.league.country, logo: m.league.logo },
      teams: {
        home: { id: m.teams.home.id, name: m.teams.home.name, logo: m.teams.home.logo },
        away: { id: m.teams.away.id, name: m.teams.away.name, logo: m.teams.away.logo },
      },
      odds1xBet: liveOddsByFixture.get(Number(m.fixture.id)) || null,
      events: m.events || [],
      fixtureSource: 'API-Football',
    }))

    setDiskCache(CACHE_KEY, mapped)
    return NextResponse.json(mapped)
  } catch (error) {
    console.error('API-Football live feed unavailable, trying SofaScore:', error)
    try {
      const fallback = await espnFallback()
      if (fallback.length > 0) {
        setDiskCache(CACHE_KEY, fallback)
        return NextResponse.json(fallback, { headers: { 'x-data-source': 'espn-fallback' } })
      }
      const fallbackSofa = await sofaFallback()
      setDiskCache(CACHE_KEY, fallbackSofa)
      return NextResponse.json(fallbackSofa, { headers: { 'x-data-source': 'sofascore-fallback' } })
    } catch (fallbackError) {
      console.error('SofaScore live fallback failed:', fallbackError)
      const stale = getDiskCache<any[]>(CACHE_KEY, Infinity)
      return NextResponse.json(stale || [])
    }
  }
}
