'use client'

import React from 'react'
import TerminalCard from '../ui/terminal/TerminalCard'
import DataFreshnessBadge from '../ui/terminal/DataFreshnessBadge'
import { LiveStateData } from './TriColumnMatrix'

export interface LiveStatePanelProps {
  liveState?: LiveStateData
  homeTeamName?: string
  awayTeamName?: string
  className?: string
}

export default function LiveStatePanel({
  liveState,
  homeTeamName = 'Home',
  awayTeamName = 'Away',
  className = '',
}: LiveStatePanelProps) {
  if (!liveState) {
    return (
      <TerminalCard
        title="Live Match State & Hazard Telemetry"
        subtitle="Real-time fixture momentum, xG accumulation, and card intensity"
        className={className}
      >
        <div className="p-8 text-center text-xs font-mono text-[#64748B] space-y-1">
          <p className="text-[#F8FAFC] font-semibold">Pre-Match State • Not Started</p>
          <p>Continuous hazard tracking activates at kickoff.</p>
        </div>
      </TerminalCard>
    )
  }

  const isLive = ['1H', '2H', 'HT', 'ET', 'LIVE'].includes(liveState.status)
  const totalXg = Math.max(0.01, liveState.homeXg + liveState.awayXg)
  const homeXgPercent = Math.round((liveState.homeXg / totalXg) * 100)
  const awayXgPercent = 100 - homeXgPercent

  const totalPossession = (liveState.homePossession || 50) + (liveState.awayPossession || 50)
  const homePossPercent = Math.round(((liveState.homePossession || 50) / totalPossession) * 100)

  return (
    <TerminalCard
      title="Live Match State & Hazard Telemetry"
      subtitle={`In-play continuous telemetry for ${homeTeamName} vs ${awayTeamName}`}
      badge={
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
            isLive
              ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
              : 'bg-[#1E293B] text-[#94A3B8] border border-[#334155]'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-[#10B981] animate-ping' : 'bg-[#64748B]'}`} />
          {isLive ? `Minute ${liveState.minute}' (${liveState.status})` : liveState.status}
        </span>
      }
      actions={
        <DataFreshnessBadge
          timestamp={liveState.stateFreshnessTimestamp}
          label="State"
          staleThresholdSeconds={120}
        />
      }
      className={className}
      padding="none"
    >
      <div className="p-4 sm:p-5 space-y-5 text-xs font-mono">
        {/* Scoreboard Strip */}
        <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1E293B] flex items-center justify-between">
          <div className="flex-1 text-left truncate">
            <span className="text-sm font-bold text-[#F8FAFC]">{homeTeamName}</span>
          </div>
          <div className="px-4 text-2xl font-bold text-[#D4AF37]">
            {liveState.homeScore} – {liveState.awayScore}
          </div>
          <div className="flex-1 text-right truncate">
            <span className="text-sm font-bold text-[#F8FAFC]">{awayTeamName}</span>
          </div>
        </div>

        {/* Statistical Metrics Stack */}
        <div className="space-y-3.5">
          {/* Expected Goals (xG) Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-[#10B981] font-bold">{liveState.homeXg.toFixed(2)}</span>
              <span className="text-[#64748B] uppercase tracking-wider text-[10px]">Expected Goals (xG)</span>
              <span className="text-[#3B82F6] font-bold">{liveState.awayXg.toFixed(2)}</span>
            </div>
            <div className="w-full bg-[#131924] rounded-full h-2 flex overflow-hidden">
              <div className="bg-[#10B981] h-2 transition-all duration-300" style={{ width: `${homeXgPercent}%` }} />
              <div className="bg-[#3B82F6] h-2 transition-all duration-300" style={{ width: `${awayXgPercent}%` }} />
            </div>
          </div>

          {/* Possession Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-[#F8FAFC]">{homePossPercent}%</span>
              <span className="text-[#64748B] uppercase tracking-wider text-[10px]">Ball Possession</span>
              <span className="text-[#F8FAFC]">{100 - homePossPercent}%</span>
            </div>
            <div className="w-full bg-[#131924] rounded-full h-1.5 flex overflow-hidden">
              <div className="bg-[#10B981] h-1.5" style={{ width: `${homePossPercent}%` }} />
              <div className="bg-[#3B82F6] h-1.5" style={{ width: `${100 - homePossPercent}%` }} />
            </div>
          </div>

          {/* Detailed comparative rows */}
          <div className="pt-2 divide-y divide-[#1E293B] border-t border-[#1E293B]">
            <div className="py-2 flex justify-between items-center text-[11px]">
              <span className="text-[#F8FAFC]">{liveState.homeShots}</span>
              <span className="text-[#64748B]">Total Shots</span>
              <span className="text-[#F8FAFC]">{liveState.awayShots}</span>
            </div>

            <div className="py-2 flex justify-between items-center text-[11px]">
              <span className="text-[#10B981] font-semibold">{liveState.homeShotsOnTarget}</span>
              <span className="text-[#64748B]">Shots on Target</span>
              <span className="text-[#3B82F6] font-semibold">{liveState.awayShotsOnTarget}</span>
            </div>

            <div className="py-2 flex justify-between items-center text-[11px]">
              <span className="text-[#F8FAFC]">{liveState.homeCorners}</span>
              <span className="text-[#64748B]">Corner Kicks</span>
              <span className="text-[#F8FAFC]">{liveState.awayCorners}</span>
            </div>

            <div className="py-2 flex justify-between items-center text-[11px]">
              <span className="text-[#F8FAFC]">{liveState.homeFouls}</span>
              <span className="text-[#64748B]">Fouls Committed</span>
              <span className="text-[#F8FAFC]">{liveState.awayFouls}</span>
            </div>

            <div className="py-2 flex justify-between items-center text-[11px]">
              <span className="text-[#F59E0B]">
                {liveState.homeYellowCards}Y {liveState.homeRedCards > 0 ? `· ${liveState.homeRedCards}R` : ''}
              </span>
              <span className="text-[#64748B]">Disciplinary Cards</span>
              <span className="text-[#F59E0B]">
                {liveState.awayYellowCards}Y {liveState.awayRedCards > 0 ? `· ${liveState.awayRedCards}R` : ''}
              </span>
            </div>
          </div>
        </div>
      </div>
    </TerminalCard>
  )
}
