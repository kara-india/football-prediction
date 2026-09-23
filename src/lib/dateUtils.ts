/**
 * Date & Time Utilities for Indian Standard Time (IST, UTC+5:30)
 * All match timings, countdowns, and data timestamps are formatted here.
 */

export function formatISTDateTime(isoString: string | Date | null | undefined): string {
  if (!isoString) return '—'
  const date = typeof isoString === 'string' ? new Date(isoString) : isoString
  if (isNaN(date.getTime())) return '—'

  return (
    date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }) + ' IST'
  )
}

export function formatISTTime(isoString: string | Date | null | undefined): string {
  if (!isoString) return '—'
  const date = typeof isoString === 'string' ? new Date(isoString) : isoString
  if (isNaN(date.getTime())) return '—'

  return (
    date.toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }) + ' IST'
  )
}

export function formatISTDate(isoString: string | Date | null | undefined): string {
  if (!isoString) return '—'
  const date = typeof isoString === 'string' ? new Date(isoString) : isoString
  if (isNaN(date.getTime())) return '—'

  return date.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function getTimeUntilKickoff(kickoffUtc: string | Date): {
  text: string
  minutesRemaining: number
  isPast: boolean
  isWithin60m: boolean
} {
  const kickoff = typeof kickoffUtc === 'string' ? new Date(kickoffUtc) : kickoffUtc
  const now = new Date()
  const diffMs = kickoff.getTime() - now.getTime()
  const diffMinutes = Math.round(diffMs / 60000)

  if (diffMs <= 0) {
    return {
      text: 'Kickoff imminent',
      minutesRemaining: 0,
      isPast: true,
      isWithin60m: true,
    }
  }

  const hours = Math.floor(diffMinutes / 60)
  const remMinutes = diffMinutes % 60

  let text = ''
  if (hours >= 24) {
    const days = Math.floor(hours / 24)
    text = `in ${days}d ${hours % 24}h`
  } else if (hours > 0) {
    text = `in ${hours}h ${remMinutes}m`
  } else {
    text = `in ${diffMinutes}m`
  }

  return {
    text,
    minutesRemaining: diffMinutes,
    isPast: false,
    isWithin60m: diffMinutes <= 60,
  }
}
