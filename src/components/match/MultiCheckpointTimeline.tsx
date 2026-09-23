'use client'

import React from 'react'
import TerminalCard from '../ui/terminal/TerminalCard'

export interface CheckpointData {
  stage: 'INITIAL' | 'LINEUP_CONFIRMED' | 'FINAL_PREMATCH' | 'SETTLED'
  label: string
  relativeTime: string // e.g. "T-48h", "T-60m", "T-5m", "FT +10m"
  timestampIST?: string
  status: 'COMPLETED' | 'ACTIVE' | 'PENDING'
  modelProb?: number
  marketProb?: number
  odds?: number
  deltaP?: number // Delta probability relative to previous checkpoint
  edge?: number
  ev?: number
  livImpact?: 'CONFIRMED_EDGE' | 'NEUTRAL' | 'EDGE_DILUTED' | 'AWAITING'
  settlementOutcome?: 'WON' | 'LOST' | 'VOID' | 'PENDING'
  errorCategory?: string
  scoreline?: string
  notes: string
}

export interface MultiCheckpointTimelineProps {
  checkpoints: CheckpointData[]
  matchName: string
  className?: string
}

export default function MultiCheckpointTimeline({
  checkpoints,
  matchName,
  className = '',
}: MultiCheckpointTimelineProps) {
  return (
    <TerminalCard
      title="Prediction Lifecycle & Multi-Checkpoint Lineup Delta"
      subtitle={`Milestone tracking and Lineup Information Value (LIV) for ${matchName}`}
      badge={
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono text-[#D4AF37] bg-[#D4AF37]/10 border border-[#D4AF37]/30 font-semibold">
          Audit Trail
        </span>
      }
      className={className}
      padding="md"
    >
      <div className="space-y-6">
        <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#1E293B]">
          {checkpoints.map((cp, idx) => {
            const isCompleted = cp.status === 'COMPLETED'
            const isActive = cp.status === 'ACTIVE'
            const isPending = cp.status === 'PENDING'

            const dotColor = isCompleted
              ? 'bg-[#10B981] border-[#10B981]'
              : isActive
              ? 'bg-[#3B82F6] border-[#60A5FA] animate-pulse'
              : 'bg-[#0B0F17] border-[#334155]'

            return (
              <div key={idx} className="relative group">
                {/* Node icon / indicator */}
                <div
                  className={`absolute -left-6 sm:-left-8 top-1 w-4 h-4 rounded-full border-2 transition-all flex items-center justify-center ${dotColor}`}
                >
                  {isCompleted && (
                    <span className="w-1.5 h-1.5 rounded-full bg-black shrink-0" />
                  )}
                </div>

                {/* Milestone Card */}
                <div
                  className={`rounded-xl border p-4 text-xs font-mono transition-colors ${
                    isActive
                      ? 'bg-[#0E131B] border-[#3B82F6]/60 shadow-sm'
                      : isCompleted
                      ? 'bg-[#0B0F17] border-[#1E293B] hover:border-[#334155]'
                      : 'bg-[#0B0F17]/50 border-[#1E293B]/60 opacity-60'
                  }`}
                >
                  {/* Header: Stage, Time, Badge */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#1E293B]">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-[#131924] text-[11px] font-bold text-[#F8FAFC]">
                        {cp.relativeTime}
                      </span>
                      <span className="font-semibold text-sm text-[#F8FAFC]">
                        {cp.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {cp.timestampIST && (
                        <span className="text-[10px] text-[#64748B]">
                          {cp.timestampIST}
                        </span>
                      )}
                      <span
                        className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded border font-semibold ${
                          isCompleted
                            ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30'
                            : isActive
                            ? 'bg-[#3B82F6]/15 text-[#3B82F6] border-[#3B82F6]/30'
                            : 'bg-[#64748B]/15 text-[#94A3B8] border-[#64748B]/30'
                        }`}
                      >
                        {cp.status}
                      </span>
                    </div>
                  </div>

                  {/* Body Metrics */}
                  <div className="pt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    {cp.modelProb !== undefined && (
                      <div>
                        <div className="text-[10px] text-[#64748B]">Model Prob</div>
                        <div className="text-sm font-bold text-[#F8FAFC] mt-0.5">
                          {(cp.modelProb * 100).toFixed(1)}%
                        </div>
                      </div>
                    )}

                    {cp.deltaP !== undefined && (
                      <div>
                        <div className="text-[10px] text-[#64748B]">Probability Delta (Δp)</div>
                        <div
                          className={`text-sm font-bold mt-0.5 ${
                            cp.deltaP > 0
                              ? 'text-[#10B981]'
                              : cp.deltaP < 0
                              ? 'text-rose-400'
                              : 'text-[#94A3B8]'
                          }`}
                        >
                          {cp.deltaP > 0 ? `+${(cp.deltaP * 100).toFixed(1)}%` : `${(cp.deltaP * 100).toFixed(1)}%`}
                        </div>
                      </div>
                    )}

                    {cp.odds !== undefined && (
                      <div>
                        <div className="text-[10px] text-[#64748B]">1xBet Odds</div>
                        <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                          {cp.odds.toFixed(2)}
                        </div>
                      </div>
                    )}

                    {cp.ev !== undefined && (
                      <div>
                        <div className="text-[10px] text-[#64748B]">Expected Value</div>
                        <div
                          className={`text-sm font-bold mt-0.5 ${
                            cp.ev > 0 ? 'text-[#10B981]' : 'text-rose-400'
                          }`}
                        >
                          {cp.ev > 0 ? `+${(cp.ev * 100).toFixed(1)}%` : `${(cp.ev * 100).toFixed(1)}%`}
                        </div>
                      </div>
                    )}

                    {cp.scoreline && (
                      <div>
                        <div className="text-[10px] text-[#64748B]">Final Score</div>
                        <div className="text-sm font-bold text-[#F8FAFC] mt-0.5">
                          {cp.scoreline}
                        </div>
                      </div>
                    )}

                    {cp.errorCategory && (
                      <div>
                        <div className="text-[10px] text-[#64748B]">Error Taxonomy</div>
                        <div className="text-xs font-semibold text-[#F59E0B] mt-0.5 truncate">
                          {cp.errorCategory}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Notes / Information Gain narrative */}
                  <div className="mt-3 pt-2 border-t border-[#1E293B]/70 flex flex-wrap items-center justify-between gap-2">
                    <p className="text-[11px] text-[#94A3B8] font-sans flex-1">
                      {cp.notes}
                    </p>
                    {cp.livImpact && (
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          cp.livImpact === 'CONFIRMED_EDGE'
                            ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30 font-semibold'
                            : 'bg-[#1E293B] text-[#94A3B8] border-[#334155]'
                        }`}
                      >
                        LIV: {cp.livImpact.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </TerminalCard>
  )
}
