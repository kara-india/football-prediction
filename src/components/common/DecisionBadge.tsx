import React from 'react'

export interface DecisionBadgeProps {
  decision: 'CANDIDATE' | 'NO_BET' | 'HIGH CONFIDENCE CANDIDATE' | string
  reasonCode?: string
  className?: string
}

export default function DecisionBadge({
  decision,
  reasonCode,
  className = '',
}: DecisionBadgeProps) {
  const isCandidate =
    decision === 'CANDIDATE' ||
    decision === 'HIGH CONFIDENCE CANDIDATE' ||
    decision === 'BET_CANDIDATE'

  return (
    <div className={`inline-flex items-center gap-1.5 font-mono ${className}`}>
      <span
        className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wide border ${
          isCandidate
            ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30'
            : 'bg-[#1E293B] text-[#94A3B8] border-[#334155]'
        }`}
      >
        {isCandidate ? 'CANDIDATE' : 'NO BET'}
      </span>
      {reasonCode && !isCandidate && (
        <span className="px-1.5 py-0.5 rounded bg-[#0B0F17] text-[9px] text-[#F59E0B] border border-[#78350F]/50">
          {reasonCode}
        </span>
      )}
    </div>
  )
}
