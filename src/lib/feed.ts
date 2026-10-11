const FOOTBALL_DATA_ORG_BASE_URL = 'https://api.football-data.org/v4'

export interface FeedResult<T> {
  ok: boolean
  data: T | null
  reason?: string
  status?: number
  lastUpdated?: string | null
}

export interface FootballDataMatch {
  id: number
  utcDate: string
  status: string
  minute?: number | null
  competition: { id: number; code: string; name: string; emblem?: string | null }
  homeTeam: { id: number; name: string; shortName?: string; crest?: string | null }
  awayTeam: { id: number; name: string; shortName?: string; crest?: string | null }
  score?: {
    fullTime?: { home?: number | null; away?: number | null }
    regularTime?: { home?: number | null; away?: number | null }
    halfTime?: { home?: number | null; away?: number | null }
  }
  venue?: string | null
  matchday?: number | null
  lastUpdated?: string | null
}

export interface FootballDataMatchesResponse {
  matches: FootballDataMatch[]
}

export async function fetchFootballData(path: string): Promise<FeedResult<FootballDataMatchesResponse | FootballDataMatch>> {
  const token = process.env.FOOTBALL_DATA_ORG_TOKEN
  if (!token) {
    return { ok: false, data: null, reason: 'FOOTBALL_DATA_ORG_NOT_CONFIGURED', status: 503 }
  }

  try {
    const url = new URL(path.replace(/^\/+/, ''), `${FOOTBALL_DATA_ORG_BASE_URL}/`)
    const response = await fetch(url, {
      headers: { 'X-Auth-Token': token, Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(10_000),
    })

    if (!response.ok) {
      const reason = response.status === 429
        ? 'FOOTBALL_DATA_ORG_RATE_LIMITED'
        : response.status === 403 || response.status === 404
          ? 'FOOTBALL_DATA_ORG_COVERAGE_UNAVAILABLE'
          : response.status === 401
            ? 'FOOTBALL_DATA_ORG_AUTH_FAILED'
            : 'FOOTBALL_DATA_ORG_REQUEST_FAILED'
      return { ok: false, data: null, reason, status: response.status }
    }

    const body = await response.json() as FootballDataMatchesResponse | FootballDataMatch
    return {
      ok: true,
      data: body,
      lastUpdated: response.headers.get('date'),
    }
  } catch {
    return { ok: false, data: null, reason: 'FOOTBALL_DATA_ORG_UNREACHABLE', status: 502 }
  }
}

function mapStatus(status: string): string {
  switch (status) {
    case 'SCHEDULED': return 'NS'
    case 'TIMED': return 'NS'
    case 'IN_PLAY':
    case 'LIVE': return 'LIVE'
    case 'PAUSED': return 'HT'
    case 'FINISHED': return 'FT'
    case 'POSTPONED': return 'PST'
    case 'CANCELLED': return 'CANC'
    case 'SUSPENDED': return 'SUSP'
    case 'AWARDED': return 'AWD'
    default: return status
  }
}

export function formatFixture(match: FootballDataMatch) {
  const score = match.score?.fullTime ?? match.score?.regularTime ?? match.score?.halfTime
  const competitionCode = match.competition?.code ?? ''

  return {
    id: match.id,
    kickoff: match.utcDate,
    venue: match.venue || 'Venue unavailable',
    status: mapStatus(match.status),
    statusLong: match.status,
    minute: match.minute ?? null,
    league: {
      id: match.competition.id,
      code: competitionCode,
      name: match.competition.name,
      country: '',
      logo: match.competition.emblem ?? null,
    },
    teams: {
      home: { id: match.homeTeam.id, name: match.homeTeam.name, logo: match.homeTeam.crest ?? null },
      away: { id: match.awayTeam.id, name: match.awayTeam.name, logo: match.awayTeam.crest ?? null },
    },
    score: { home: score?.home ?? null, away: score?.away ?? null },
    lineupConfirmed: false,
    odds1xBet: null,
    decision: 'LINEUP_UNCONFIRMED',
    provider: 'football-data.org',
    providerUpdatedAt: match.lastUpdated ?? null,
    analysisSupported: competitionCode === 'PL',
  }
}
