import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'
import { getDiskCache, setDiskCache } from '@/lib/diskCache'

const BASE_URL = 'https://v3.football.api-sports.io'

export async function fetchApiFootball(path: string, isUserDemand = false): Promise<any> {
  const quota = await canMakeAPIRequest(isUserDemand)
  if (!quota.allowed) {
    throw new Error(quota.reason || 'API-Football quota unavailable')
  }

  const apiKey = process.env.API_FOOTBALL_KEY
  if (!apiKey) {
    throw new Error('API_FOOTBALL_KEY environment variable is not configured.')
  }

  const endpoint = path.startsWith('/') ? path : `/${path}`
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: { 'x-apisports-key': apiKey },
    cache: 'no-store',
  })

  const payload = await response.json()
  recordAPIRequest(endpoint)

  if (!response.ok) {
    throw new Error(`API-Football request failed with HTTP ${response.status}`)
  }

  if (payload?.errors && Object.keys(payload.errors).length > 0) {
    const details =
      typeof payload.errors === 'string'
        ? payload.errors
        : Object.entries(payload.errors)
            .map(([key, value]) => `${key}: ${String(value)}`)
            .join('; ')
    throw new Error(`API-Football ${endpoint}: ${details || 'provider returned an error'}`)
  }

  return payload
}

let cached1xBetBookmakerId: number | null | undefined

/**
 * Cache provider responses by exact endpoint for short, endpoint-appropriate TTLs.
 * This protects the daily quota while preserving freshness requirements at the
 * Champion layer, which validates the bookmaker's own source timestamp.
 */
export async function fetchCachedApiFootball(path: string, ttlMs: number, isUserDemand = true): Promise<any> {
  const cacheKey = `api_football:${path}`
  const cached = getDiskCache<any>(cacheKey, ttlMs)
  if (cached !== null) return cached

  const payload = await fetchApiFootball(path, isUserDemand)
  setDiskCache(cacheKey, payload)
  return payload
}

export async function resolve1xBetBookmakerId(): Promise<number | null> {
  if (cached1xBetBookmakerId !== undefined) {
    return cached1xBetBookmakerId
  }

  const configured = Number(process.env.ODDS_1XBET_BOOKMAKER_ID)
  if (Number.isInteger(configured) && configured > 0) {
    cached1xBetBookmakerId = configured
    return configured
  }

  try {
    const payload = await fetchApiFootball('/odds/bookmakers?search=1xBet', true)
    const bookmakers = Array.isArray(payload?.response) ? payload.response : []
    const exact = bookmakers.find((item: any) => /^(1xBet|1xBet)$/i.test(String(item?.name || '').trim()))
    const fallback = bookmakers.find((item: any) => /1xBet/i.test(String(item?.name || '')))
    const id = Number((exact || fallback)?.id)

    cached1xBetBookmakerId = Number.isInteger(id) && id > 0 ? id : null
    return cached1xBetBookmakerId
  } catch (error) {
    console.warn('[1XBET BOOKMAKER] Unable to resolve bookmaker id', error)
    cached1xBetBookmakerId = null
    return null
  }
}

function oddFromMarket(market: any, labels: RegExp[]): number | null {
  const value = market?.values?.find((item: any) =>
    labels.some((label) => label.test(String(item?.value || ''))),
  )
  const odd = Number(value?.odd)
  return Number.isFinite(odd) && odd > 1 ? odd : null
}

export function extract1xBetOdds(bookmakers: any[]): {
  home: number | null
  draw: number | null
  away: number | null
  over25: number | null
  under25: number | null
  sourceTimestamp: string | null
} | null {
  const bookmaker = (bookmakers || []).find(
    (item: any) => /^1xBet$/i.test(String(item?.name || '').trim()),
  )
  if (!bookmaker) return null

  const markets = bookmaker.bets || []
  const winner = markets.find((item: any) =>
    /match winner|1x2/i.test(String(item?.name || '')),
  )
  const totals = markets.find((item: any) =>
    /over\/under|total goals|goals over\/under/i.test(String(item?.name || '')),
  )

  const odds = {
    home: oddFromMarket(winner, [/^home$/i]),
    draw: oddFromMarket(winner, [/^draw$/i]),
    away: oddFromMarket(winner, [/^away$/i]),
    over25: oddFromMarket(totals, [/^over 2\.5$/i]),
    under25: oddFromMarket(totals, [/^under 2\.5$/i]),
    sourceTimestamp:
      typeof bookmaker?.update === 'string' && Number.isFinite(Date.parse(bookmaker.update))
        ? new Date(bookmaker.update).toISOString()
        : typeof bookmaker?.last_update === 'string' && Number.isFinite(Date.parse(bookmaker.last_update))
          ? new Date(bookmaker.last_update).toISOString()
          : null,
  }

  // A timestamp alone does not constitute a real market.
  const hasRealPrice = [odds.home, odds.draw, odds.away, odds.over25, odds.under25]
    .some((value) => value !== null && Number.isFinite(value) && value > 1)
  return hasRealPrice ? odds : null
}

export function extractProviderForecast(response: any): {
  home: number | null
  draw: number | null
  away: number | null
  winnerName: string | null
  winnerId: number | null
  goalsHome: number | null
  goalsAway: number | null
} | null {
  const prediction = response?.response?.[0]?.predictions
  if (!prediction) return null

  const pct = (value: unknown): number | null => {
    if (typeof value === 'number') return value > 1 ? value / 100 : value
    if (typeof value !== 'string') return null
    const n = Number(value.replace('%', '').trim())
    if (!Number.isFinite(n)) return null
    return value.includes('%') || n > 1 ? n / 100 : n
  }

  const goal = (value: unknown): number | null => {
    const n = Number(value)
    return Number.isFinite(n) ? n : null
  }

  return {
    home: pct(prediction?.percent?.home),
    draw: pct(prediction?.percent?.draw),
    away: pct(prediction?.percent?.away),
    winnerName: prediction?.winner?.name ?? null,
    winnerId: Number.isFinite(Number(prediction?.winner?.id)) ? Number(prediction.winner.id) : null,
    goalsHome: goal(prediction?.goals?.home),
    goalsAway: goal(prediction?.goals?.away),
  }
}

export function extractTeamStatistic(statistics: any[], teamId: number, names: RegExp[]): number | null {
  const teamBlock = (statistics || []).find((item: any) => Number(item?.team?.id) === Number(teamId))
  const stat = (teamBlock?.statistics || []).find((item: any) =>
    names.some((pattern) => pattern.test(String(item?.type || ''))),
  )
  if (stat?.value === null || stat?.value === undefined) return null
  const numeric = Number(String(stat.value).replace('%', '').trim())
  return Number.isFinite(numeric) ? numeric : null
}

export async function fetch1xBetOddsForFixture(fixtureId: number) {
  if (!Number.isInteger(fixtureId) || fixtureId <= 0) return null
  try {
    const payload = await fetchCachedApiFootball('/odds?fixture=' + fixtureId, 30 * 1000, true)
    return extract1xBetOdds(payload?.response?.[0]?.bookmakers || [])
  } catch (error) {
    console.warn('[1XBET ODDS] Fixture lookup failed', fixtureId, error)
    return null
  }
}

function normalizeOddsTeamName(value: unknown): string {
  return String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\b(fc|cf|sc|afc|fk|club|calcio)\b/g, '')
    .replace(/[^a-z0-9]/g, '')
}

function oddsApiTeamMatch(a: unknown, b: unknown): boolean {
  const x = normalizeOddsTeamName(a)
  const y = normalizeOddsTeamName(b)
  if (!x || !y) return false
  return x === y || x.includes(y) || y.includes(x)
}

function pulseScoreTeamMatch(a: unknown, b: unknown): boolean {
  const x = normalizeOddsTeamName(a)
  const y = normalizeOddsTeamName(b)
  if (!x || !y) return false
  return x === y || x.includes(y) || y.includes(x)
}

function extractPulseScore1xBetOdds(event: any): any | null {
  const markets = Array.isArray(event?.markets) ? event.markets : []
  const result = markets.find((m: any) =>
    m?.isActive !== false &&
    /^(MATCH_RESULT|1X2)$/i.test(String(m?.canonicalMarket || m?.type || '')),
  )
  const totals = markets.find((m: any) =>
    m?.isActive !== false &&
    /^(OVER_UNDER|TOTALS)$/i.test(String(m?.canonicalMarket || m?.type || '')),
  )

  const selections = (market: any) => Array.isArray(market?.selections) ? market.selections : []
  const findOutcome = (market: any, names: string[], predicate?: (selection: any) => boolean) => {
    const selection = selections(market).find((item: any) => {
      if (item?.isActive === false) return false
      if (predicate && !predicate(item)) return false
      const value = String(item?.canonicalOutcome || item?.outcome || item?.name || '').toLowerCase()
      const raw = String(item?.rawName || '').toLowerCase()
      return names.some((name) => value === name || raw === name)
    })
    const odd = Number(selection?.odds ?? selection?.price)
    return Number.isFinite(odd) && odd > 1 ? odd : null
  }

  const odds = {
    home: findOutcome(result, ['home', '1']),
    draw: findOutcome(result, ['draw', 'x']),
    away: findOutcome(result, ['away', '2']),
    over25: findOutcome(totals, ['over'], (item) => Number(item?.line ?? item?.point) === 2.5),
    under25: findOutcome(totals, ['under'], (item) => Number(item?.line ?? item?.point) === 2.5),
    // Preserve only a timestamp supplied by the live-odds provider. Never
    // manufacture "now" as a source timestamp: that can make old prices appear fresh.
    sourceTimestamp:
      typeof event?.updatedAt === 'string' && Number.isFinite(Date.parse(event.updatedAt))
        ? new Date(event.updatedAt).toISOString()
        : typeof event?.lastUpdate === 'string' && Number.isFinite(Date.parse(event.lastUpdate))
          ? new Date(event.lastUpdate).toISOString()
          : null,
  }

  // A timestamp alone is not an odds market. Return a result only if at least
  // one real decimal price was parsed.
  const hasRealPrice = [odds.home, odds.draw, odds.away, odds.over25, odds.under25]
    .some((value) => value !== null && Number.isFinite(value) && value > 1)
  return hasRealPrice ? odds : null
}

export async function fetch1xBetLiveOddsFromPulseScore(fixtures: Array<{
  id: number
  home: string
  away: string
  kickoff?: string
}>) {
  const apiKey = process.env.PULSESCORE_API_KEY
  if (!apiKey || !fixtures.length) return new Map<number, any>()

  try {
    const url = new URL('https://api.pulsescore.net/api/onexbet/live-events')
    url.searchParams.set('sport', 'soccer')
    url.searchParams.set('limit', '30')
    const response = await fetch(url.toString(), {
      headers: {
        'X-Secret': apiKey,
        Accept: 'application/json',
      },
      cache: 'no-store',
    })
    if (!response.ok) throw new Error(`PulseScore HTTP ${response.status}`)
    const payload = await response.json()
    const events = Array.isArray(payload) ? payload : Array.isArray(payload?.events) ? payload.events : []
    const result = new Map<number, any>()

    for (const fixture of fixtures) {
      const event = events.find((item: any) =>
        pulseScoreTeamMatch(item?.home, fixture.home) &&
        pulseScoreTeamMatch(item?.away, fixture.away),
      )
      if (!event) continue

      const odds = extractPulseScore1xBetOdds(event)
      if (odds) result.set(Number(fixture.id), odds)
    }

    return result
  } catch (error) {
    console.warn('[PULSESCORE 1XBET LIVE] Lookup failed', error)
    return new Map<number, any>()
  }
}

export async function fetch1xBetLiveOddsFromOddsApi(fixtures: Array<{
  id: number
  home: string
  away: string
  kickoff?: string
}>) {
  const apiKey = process.env.ODDS_API_KEY
  if (!apiKey || !fixtures.length) return new Map<number, any>()

  try {
    const url = new URL('https://api.the-odds-api.com/v4/sports/upcoming/odds')
    url.searchParams.set('apiKey', apiKey)
    url.searchParams.set('regions', 'eu')
    url.searchParams.set('markets', 'h2h,totals')
    url.searchParams.set('bookmakers', 'onexbet')
    url.searchParams.set('oddsFormat', 'decimal')
    const response = await fetch(url.toString(), { cache: 'no-store' })
    if (!response.ok) throw new Error(`Odds API HTTP ${response.status}`)
    const events = await response.json()
    const result = new Map<number, any>()

    for (const fixture of fixtures) {
      const event = (Array.isArray(events) ? events : []).find((item: any) =>
        oddsApiTeamMatch(item?.home_team, fixture.home) &&
        oddsApiTeamMatch(item?.away_team, fixture.away)
      )
      if (!event) continue

      const bookmaker = (event.bookmakers || []).find((b: any) =>
        String(b?.key || '').toLowerCase() === 'onexbet' ||
        /1xBet/i.test(String(b?.title || ''))
      )
      if (!bookmaker) continue

      const h2h = (bookmaker.markets || []).find((m: any) => m?.key === 'h2h')
      const totals = (bookmaker.markets || []).find((m: any) => m?.key === 'totals')
      const outcomeOdd = (market: any, names: string[]) => {
        const outcome = (market?.outcomes || []).find((o: any) =>
          names.some((name) => String(o?.name || '').toLowerCase() === name.toLowerCase())
        )
        const odd = Number(outcome?.price)
        return Number.isFinite(odd) && odd > 1 ? odd : null
      }

      const odds = {
        home: outcomeOdd(h2h, [event.home_team]),
        draw: outcomeOdd(h2h, ['Draw']),
        away: outcomeOdd(h2h, [event.away_team]),
        over25: (() => {
          const outcome = (totals?.outcomes || []).find((o: any) =>
            String(o?.name || '').toLowerCase() === 'over' && Number(o?.point) === 2.5
          )
          const odd = Number(outcome?.price)
          return Number.isFinite(odd) && odd > 1 ? odd : null
        })(),
        under25: (() => {
          const outcome = (totals?.outcomes || []).find((o: any) =>
            String(o?.name || '').toLowerCase() === 'under' && Number(o?.point) === 2.5
          )
          const odd = Number(outcome?.price)
          return Number.isFinite(odd) && odd > 1 ? odd : null
        })(),
        sourceTimestamp: typeof bookmaker?.last_update === 'string'
          ? bookmaker.last_update
          : typeof event?.last_update === 'string'
            ? event.last_update
            : null,
      }

      if (Object.values(odds).some((value) => value !== null && value !== '')) {
        result.set(Number(fixture.id), odds)
      }
    }

    return result
  } catch (error) {
    console.warn('[1XBET ODDS API FALLBACK] Live lookup failed', error)
    return new Map<number, any>()
  }
}

function normalizeTeamName(value: unknown): string {
  return String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '')
}

export async function findApiFootballFixtureByTeams(homeTeam: string, awayTeam: string, date: string) {
  try {
    const payload = await fetchCachedApiFootball('/fixtures?date=' + encodeURIComponent(date), 5 * 60 * 1000, true)
    const home = normalizeTeamName(homeTeam)
    const away = normalizeTeamName(awayTeam)
    const matches = Array.isArray(payload?.response) ? payload.response : []
    return matches.find((fixture: any) => {
      const h = normalizeTeamName(fixture?.teams?.home?.name)
      const a = normalizeTeamName(fixture?.teams?.away?.name)
      return (h === home && a === away) || (h.includes(home) && a.includes(away))
    }) || null
  } catch (error) {
    console.warn('[API-FOOTBALL FIXTURE RESOLUTION] Failed', error)
    return null
  }
}
