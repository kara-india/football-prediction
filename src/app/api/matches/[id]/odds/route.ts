import { NextResponse } from 'next/server'
import { acquireProviderRequestLock, isProviderCacheConfigured, readProviderCache, recordProviderRequest, saveProviderQuota, writeProviderCache } from '@/lib/providerCache'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const BASE_URL = 'https://api.the-odds-api.com/v4'
const SPORT_KEY = 'soccer_epl'
const BOOKMAKER_KEY = 'onexbet'
const HEADERS = { 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0' }

interface RequestedFixture {
  id: number
  kickoff: string
  status: string
  league: { code?: string }
  teams: { home: { name: string }; away: { name: string } }
}

function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: HEADERS })
}

function normalizedName(value: string): string {
  return value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase().replace(/[^a-z0-9]/g, '')
}

function validFixture(value: unknown): value is RequestedFixture {
  if (!value || typeof value !== 'object') return false
  const fixture = value as Partial<RequestedFixture>
  return Number.isInteger(fixture.id)
    && typeof fixture.kickoff === 'string'
    && Number.isFinite(Date.parse(fixture.kickoff))
    && (fixture.status === 'LIVE' || fixture.status === 'HT' || (fixture.status === 'NS' && Date.parse(fixture.kickoff) > Date.now()))
    && fixture.league?.code === 'PL'
    && typeof fixture.teams?.home?.name === 'string'
    && typeof fixture.teams?.away?.name === 'string'
}

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params
  if (!/^\d+$/.test(id)) return json({ error: 'INVALID_FIXTURE_ID' }, 400)

  let fixture: unknown
  try {
    fixture = await request.json()
  } catch {
    return json({ error: 'INVALID_FIXTURE' }, 400)
  }
  if (!validFixture(fixture) || fixture.id !== Number(id)) return json({ error: 'INVALID_FIXTURE' }, 400)
  if (!isProviderCacheConfigured()) return json({ error: 'PROVIDER_CACHE_NOT_CONFIGURED' }, 503)

  const apiKey = process.env.ODDS_API_KEY
  if (!apiKey) return json({ error: 'ODDS_API_NOT_CONFIGURED' }, 503)

  const live = fixture.status === 'LIVE' || fixture.status === 'HT'
  const ttlSeconds = live ? 60 : 5 * 60
  const cacheKey = `odds:${fixture.id}`
  try {
    const cached = await readProviderCache<OddsResponse>(cacheKey)
    if (cached) return json({ ...cached.payload, cached: true, syncedAt: cached.syncedAt })

    const locked = await acquireProviderRequestLock(`odds:${fixture.id}`, 30)
    if (!locked) {
      const waiting = await waitForOddsCache(cacheKey)
      if (waiting) return json({ ...waiting.payload, cached: true, syncedAt: waiting.syncedAt })
      return json({ error: 'ODDS_LOOKUP_IN_PROGRESS' }, 409)
    }

    // The event directory is explicitly documented as quota-free. We use it to
    // locate one EPL event, then spend credits only on that event's requested markets.
    const eventsUrl = new URL(`${BASE_URL}/sports/${SPORT_KEY}/events`)
    eventsUrl.searchParams.set('apiKey', apiKey)
    eventsUrl.searchParams.set('dateFormat', 'iso')
    const eventResponse = await fetch(eventsUrl, { cache: 'no-store', signal: AbortSignal.timeout(10_000) })
    await recordProviderRequest({ provider: 'the-odds-api', endpoint: `/sports/${SPORT_KEY}/events`, quotaCost: 0, responseStatus: eventResponse.status })
    if (!eventResponse.ok) return json({ error: eventResponse.status === 401 || eventResponse.status === 403 ? 'ODDS_API_AUTH_FAILED' : 'ODDS_EVENT_LOOKUP_FAILED' }, eventResponse.status === 429 ? 429 : 502)

    const events = await eventResponse.json() as Array<{ id?: string; home_team?: string; away_team?: string; commence_time?: string }>
    const home = normalizedName(fixture.teams.home.name)
    const away = normalizedName(fixture.teams.away.name)
    const kickoff = Date.parse(fixture.kickoff)
    const event = Array.isArray(events) ? events.find(candidate => {
      if (!candidate.id || !candidate.home_team || !candidate.away_team || !candidate.commence_time) return false
      const sameTeams = normalizedName(candidate.home_team) === home && normalizedName(candidate.away_team) === away
      return sameTeams && Math.abs(Date.parse(candidate.commence_time) - kickoff) <= 6 * 60 * 60 * 1000
    }) : undefined

    if (!event?.id) {
      const unavailable: OddsResponse = { markets: [], reason: 'ODDS_NOT_LISTED', bookmaker: BOOKMAKER_KEY, quotaCost: 0 }
      await writeProviderCache({ cacheKey, provider: 'the-odds-api', payload: unavailable, providerMetadata: { eventLookup: 'not-listed' }, ttlSeconds })
      return json(unavailable)
    }

    const oddsUrl = new URL(`${BASE_URL}/sports/${SPORT_KEY}/events/${encodeURIComponent(event.id)}/odds`)
    oddsUrl.searchParams.set('apiKey', apiKey)
    oddsUrl.searchParams.set('bookmakers', BOOKMAKER_KEY)
    oddsUrl.searchParams.set('markets', 'h2h,totals')
    oddsUrl.searchParams.set('oddsFormat', 'decimal')
    oddsUrl.searchParams.set('dateFormat', 'iso')
    const oddsResponse = await fetch(oddsUrl, { cache: 'no-store', signal: AbortSignal.timeout(10_000) })
    const remaining = numberHeader(oddsResponse.headers.get('x-requests-remaining'))
    const used = numberHeader(oddsResponse.headers.get('x-requests-used'))
    const lastCost = numberHeader(oddsResponse.headers.get('x-requests-last'))
    await recordProviderRequest({ provider: 'the-odds-api', endpoint: `/sports/${SPORT_KEY}/events/{eventId}/odds`, quotaCost: lastCost ?? 0, responseStatus: oddsResponse.status, remoteUsed: used, remoteRemaining: remaining })
    await saveProviderQuota({ provider: 'the-odds-api', remoteUsed: used, remoteRemaining: remaining, lastRequestCost: lastCost })
    if (!oddsResponse.ok) return json({ error: oddsResponse.status === 401 || oddsResponse.status === 403 ? 'ODDS_API_AUTH_FAILED' : 'ODDS_REQUEST_FAILED' }, oddsResponse.status === 429 ? 429 : 502)

    const payload = await oddsResponse.json() as { bookmakers?: Array<{ key?: string; title?: string; markets?: Array<{ key?: string; last_update?: string; outcomes?: Array<{ name?: string; price?: number; point?: number }> }> }> }
    const bookmaker = payload.bookmakers?.find(item => item.key === BOOKMAKER_KEY)
    const markets = (bookmaker?.markets || []).flatMap(market => (market.outcomes || []).map(outcome => ({
      market: market.key,
      selection: outcome.name,
      line: outcome.point ?? null,
      decimalOdds: typeof outcome.price === 'number' ? outcome.price : null,
      sourceUpdatedAt: market.last_update ?? null,
    })))

    const response: OddsResponse = {
      bookmaker: bookmaker?.title || BOOKMAKER_KEY,
      bookmakerKey: BOOKMAKER_KEY,
      providerEventId: event.id,
      markets,
      reason: bookmaker ? null : 'BOOKMAKER_UNAVAILABLE',
      creditsRemaining: oddsResponse.headers.get('x-requests-remaining'),
      creditsUsed: oddsResponse.headers.get('x-requests-used'),
      creditsLastRequest: oddsResponse.headers.get('x-requests-last'),
      quotaCost: lastCost ?? 0,
    }
    await writeProviderCache({ cacheKey, provider: 'the-odds-api', payload: response, providerMetadata: { providerEventId: event.id }, ttlSeconds })
    return json(response)
  } catch {
    return json({ error: 'ODDS_API_UNREACHABLE' }, 502)
  }
}

interface OddsResponse {
  bookmaker?: string
  bookmakerKey?: string
  providerEventId?: string
  markets: Array<{ market?: string; selection?: string; line?: number | null; decimalOdds?: number | null; sourceUpdatedAt?: string | null }>
  reason?: string | null
  error?: string
  quotaCost?: number
  creditsRemaining?: string | null
  creditsUsed?: string | null
  creditsLastRequest?: string | null
}

function numberHeader(value: string | null): number | null {
  if (value === null) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

async function waitForOddsCache(cacheKey: string) {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 250))
    const cached = await readProviderCache<OddsResponse>(cacheKey)
    if (cached) return cached
  }
  return null
}
