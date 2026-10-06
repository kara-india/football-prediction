import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'

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
      typeof bookmaker?.update === 'string'
        ? bookmaker.update
        : typeof bookmaker?.last_update === 'string'
          ? bookmaker.last_update
          : null,
  }

  return Object.values(odds).some((value) => value !== null && value !== '')
    ? odds
    : null
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
    const payload = await fetchApiFootball('/odds?fixture=' + fixtureId, true)
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
    const payload = await fetchApiFootball('/fixtures?date=' + encodeURIComponent(date), true)
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
