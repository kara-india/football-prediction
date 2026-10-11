export interface FeedResult<T> {
  ok: boolean
  data: T
  reason?: string
  status?: number
}

export async function fetchFootball(_path: string, _userDemand: boolean): Promise<FeedResult<any>> {
  // Recovery A0: API-Football is not a runtime provider. Do not call the network.
  return {
    ok: false,
    data: null,
    reason: 'API_FOOTBALL_REMOVED',
    status: 410,
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
