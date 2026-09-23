'use client'

import React, { useEffect, useState } from 'react'

export interface DataFreshnessBadgeProps {
  timestamp?: string | Date | null
  staleThresholdSeconds?: number
  label?: string
  className?: string
  showDot?: boolean
}

export default function DataFreshnessBadge({
  timestamp,
  staleThresholdSeconds = 120,
  label,
  className = '',
  showDot = true,
}: DataFreshnessBadgeProps) {
  const [secondsElapsed, setSecondsElapsed] = useState<number | null>(null)

  useEffect(() => {
    if (!timestamp) {
      setSecondsElapsed(null)
      return
    }

    const calculateElapsed = () => {
      const time = typeof timestamp === 'string' ? new Date(timestamp).getTime() : timestamp.getTime()
      if (isNaN(time)) {
        setSecondsElapsed(null)
        return
      }
      const now = Date.now()
      const diffSec = Math.max(0, Math.floor((now - time) / 1000))
      setSecondsElapsed(diffSec)
    }

    calculateElapsed()
    const interval = setInterval(calculateElapsed, 5000)
    return () => clearInterval(interval)
  }, [timestamp])

  if (!timestamp || secondsElapsed === null) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono text-[#64748B] bg-[#0B0F17] border border-[#1E293B] ${className}`}
      >
        {showDot && <span className="w-1.5 h-1.5 rounded-full bg-[#64748B]" />}
        {label ? `${label}: ` : ''}No telemetry
      </span>
    )
  }

  const isStale = secondsElapsed >= staleThresholdSeconds
  const isWarning = !isStale && secondsElapsed >= staleThresholdSeconds / 2

  let timeString = ''
  if (isStale) {
    const mins = Math.floor(secondsElapsed / 60)
    timeString = `Stale: ${mins}m ago`
  } else if (secondsElapsed < 60) {
    timeString = `${secondsElapsed}s ago`
  } else {
    const mins = Math.floor(secondsElapsed / 60)
    const secs = secondsElapsed % 60
    timeString = `${mins}m ${secs}s ago`
  }

  const dotColor = isStale
    ? 'bg-[#EF4444]'
    : isWarning
    ? 'bg-[#F59E0B]'
    : 'bg-[#10B981]'

  const textColor = isStale
    ? 'text-[#FCA5A5]'
    : isWarning
    ? 'text-[#FCD34D]'
    : 'text-[#94A3B8]'

  const borderColor = isStale
    ? 'border-[#7F1D1D]/50'
    : isWarning
    ? 'border-[#78350F]/50'
    : 'border-[#1E293B]'

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-[#0B0F17] border transition-colors ${borderColor} ${textColor} ${className}`}
      title={typeof timestamp === 'string' ? timestamp : timestamp.toISOString()}
    >
      {showDot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />}
      <span>
        {label ? `${label}: ` : ''}
        {timeString}
      </span>
    </span>
  )
}
