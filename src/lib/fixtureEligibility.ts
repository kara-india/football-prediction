export const ALLOWED_LEAGUES = new Set([39, 71, 135, 140, 78, 61, 94, 88, 128, 144, 2, 3, 1, 4, 5, 9, 6, 7, 10])

const EXCLUDED = /\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|Reserves)\b/i

export function isEligibleFixture(fixture: any): boolean {
  const leagueId = fixture?.league?.id
  if (!ALLOWED_LEAGUES.has(leagueId)) return false
  const home = String(fixture?.teams?.home?.name || '')
  const away = String(fixture?.teams?.away?.name || '')
  const league = String(fixture?.league?.name || '')
  return !EXCLUDED.test(home) && !EXCLUDED.test(away) && !EXCLUDED.test(league)
}

export function isFutureFixture(fixture: any, nowMs = Date.now()): boolean {
  const ts = new Date(fixture?.fixture?.date ?? fixture?.kickoff).getTime()
  return Number.isFinite(ts) && ts > nowMs
}

export function isUpcomingFixture(fixture: any, nowMs = Date.now()): boolean {
  const status = fixture?.fixture?.status?.short ?? fixture?.status
  return isFutureFixture(fixture, nowMs) && !['FT','AET','PEN','PST','CANC','ABD','AWD','WO'].includes(status)
}
