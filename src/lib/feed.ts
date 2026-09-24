import { canMakeAPIRequest, recordAPIRequest } from '@/lib/quotaGuard'

const API_BASE = 'https://v3.football.api-sports.io'
const API_KEY = () => process.env.API_FOOTBALL_KEY

export interface FeedResult<T> {
  ok: boolean
  data: T
  reason?: string
  status?: number
}

export async function fetchFootball(path: string, userDemand: boolean): Promise<FeedResult<any>> {
  if (!API_KEY()) return { ok: false, data: null, reason: 'API_FOOTBALL_KEY_NOT_CONFIGURED', status: 500 }

  const quota = await canMakeAPIRequest(userDemand)
  if (!quota.allowed) return { ok: false, data: null, reason: quota.reason || 'API_QUOTA_UNAVAILABLE', status: 429 }

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'x-apisports-key': API_KEY() as string },
      cache: 'no-store',
    })
    recordAPIRequest(path)
    const json = await response.json()
    const errors = json?.errors && Object.keys(json.errors).length ? json.errors : null
    if (!response.ok || errors) {
      return { ok: false, data: null, reason: errors ? JSON.stringify(errors) : 'API_FOOTBALL_UPSTREAM_ERROR', status: 502 }
    }
    return { ok: true, data: json?.response ?? [], status: response.status }
  } catch (error: any) {
    return { ok: false, data: null, reason: error?.message || 'API_FOOTBALL_REQUEST_FAILED', status: 502 }
  }
}

export function formatFixture(f: any) {
  const kickoff = new Date(f.fixture.date)
  return {
    id: f.fixture.id,
    kickoff: f.fixture.date,
    venue: f.fixture.venue?.name || 'TBD',
    status: f.fixture.status.short,
    statusLong: f.fixture.status.long,
    league: { id: f.league.id, name: f.league.name, country: f.league.country, logo: f.league.logo },
    teams: {
      home: { id: f.teams.home.id, name: f.teams.home.name, logo: f.teams.home.logo },
      away: { id: f.teams.away.id, name: f.teams.away.name, logo: f.teams.away.logo },
    },
    score: { home: f.goals?.home ?? null, away: f.goals?.away ?? null },
    lineupConfirmed: false,
    lineupExpectedAt: new Date(kickoff.getTime() - 60 * 60 * 1000).toISOString(),
    odds1xBet: null,
    decision: 'ODDS_UNAVAILABLE',
  }
}
