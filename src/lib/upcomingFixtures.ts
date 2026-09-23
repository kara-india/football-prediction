const TERMINAL_STATUSES = new Set(['FT', 'AET', 'PEN', 'PST', 'CANC', 'ABD', 'AWD', 'WO'])

export function isActuallyUpcoming(m: any, nowMs = Date.now()): boolean {
  const kickoffMs = new Date(m?.kickoff).getTime()
  return Number.isFinite(kickoffMs) &&
    kickoffMs > nowMs &&
    !TERMINAL_STATUSES.has(m?.status)
}
