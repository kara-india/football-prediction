/**
 * Match Intelligence Status & Lineup Gate Messaging
 * Generates transparent user-facing status indicators and countdowns
 * strictly adhering to the Lineup Gate (analysis unlocks at T-60m with verified lineups).
 */

export interface MatchGateStatus {
  state: 'LOCKED' | 'AWAITING_LINEUPS' | 'LINEUPS_CONFIRMED' | 'LIVE' | 'FINISHED'
  badgeLabel: string
  badgeVariant: 'neutral' | 'warning' | 'emerald' | 'gold' | 'live'
  message: string
  isAnalysisUnlocked: boolean
  minutesToKickoff: number
}

export function evaluateMatchGateStatus(
  kickoffUtc: string | Date,
  lineupConfirmed: boolean = false,
  status: string = 'NS'
): MatchGateStatus {
  const now = new Date()
  const kickoff = typeof kickoffUtc === 'string' ? new Date(kickoffUtc) : kickoffUtc
  const diffMs = kickoff.getTime() - now.getTime()
  const minutesToKickoff = Math.round(diffMs / 60000)

  // 1. Finished Matches
  if (['FT', 'AET', 'PEN', 'PST', 'CANC'].includes(status)) {
    return {
      state: 'FINISHED',
      badgeLabel: status === 'FT' ? 'Full Time' : status,
      badgeVariant: 'neutral',
      message: 'Match completed • Official settlement recorded.',
      isAnalysisUnlocked: true,
      minutesToKickoff,
    }
  }

  // 2. In-Play Matches
  if (['LIVE', '1H', '2H', 'HT', 'ET', 'BT'].includes(status)) {
    return {
      state: 'LIVE',
      badgeLabel: status === 'HT' ? 'Half Time' : 'Live In-Play',
      badgeVariant: 'live',
      message: 'Match currently live • In-play probability tracking active.',
      isAnalysisUnlocked: true,
      minutesToKickoff,
    }
  }

  // 3. Pre-Match: Lineups Officially Confirmed (T-60m to T-0m)
  if (lineupConfirmed) {
    return {
      state: 'LINEUPS_CONFIRMED',
      badgeLabel: 'Lineups Confirmed',
      badgeVariant: 'emerald',
      message: 'Official lineups verified • Real-time intelligence active.',
      isAnalysisUnlocked: true,
      minutesToKickoff,
    }
  }

  // 4. Pre-Match: Within 60m but Awaiting Official Starting XI Sheets
  if (minutesToKickoff <= 60 && minutesToKickoff > 0) {
    return {
      state: 'AWAITING_LINEUPS',
      badgeLabel: `Kickoff in ${minutesToKickoff}m`,
      badgeVariant: 'warning',
      message: 'Awaiting confirmed lineups from match officials (T-60m window active).',
      isAnalysisUnlocked: false,
      minutesToKickoff,
    }
  }

  // 5. Pre-Match: Kickoff > 60m away (Locked Gate)
  const hours = Math.floor(minutesToKickoff / 60)
  const remMinutes = minutesToKickoff % 60
  const timeText = hours > 0 ? `${hours}h ${remMinutes}m` : `${minutesToKickoff}m`

  return {
    state: 'LOCKED',
    badgeLabel: `Kickoff in ${timeText}`,
    badgeVariant: 'gold',
    message: 'Upcoming • Analysis unlocks at T-60m once official lineups are announced.',
    isAnalysisUnlocked: false,
    minutesToKickoff,
  }
}
