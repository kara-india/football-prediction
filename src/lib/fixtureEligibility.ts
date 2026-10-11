const EXCLUDED = /\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|Reserves)\b/i

export function isEligibleFixture(fixture: any): boolean {
  const home = String(fixture?.homeTeam?.name || fixture?.teams?.home?.name || '')
  const away = String(fixture?.awayTeam?.name || fixture?.teams?.away?.name || '')
  const league = String(fixture?.competition?.name || fixture?.league?.name || '')
  return !EXCLUDED.test(home) && !EXCLUDED.test(away) && !EXCLUDED.test(league)
}

export function isFutureFixture(fixture: any, nowMs = Date.now()): boolean {
  const ts = new Date(fixture?.fixture?.date ?? fixture?.utcDate ?? fixture?.kickoff).getTime()
  return Number.isFinite(ts) && ts > nowMs
}

export function isUpcomingFixture(fixture: any, nowMs = Date.now()): boolean {
  const status = fixture?.fixture?.status?.short ?? fixture?.status
  return isFutureFixture(fixture, nowMs) && ![
    'FT', 'AET', 'PEN', 'PST', 'CANC', 'ABD', 'AWD', 'WO',
    'FINISHED', 'POSTPONED', 'CANCELLED', 'AWARDED', 'LIVE', 'IN_PLAY', 'PAUSED',
  ].includes(status)
}
