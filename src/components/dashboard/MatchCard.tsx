'use client'

import React from 'react'
import Link from 'next/link'
import { formatISTDateTime, getTimeUntilKickoff } from '@/lib/dateUtils'

export interface MatchCardProps {
  id: string | number
  kickoff: string
  venue?: string
  status: string
  league: {
    id: number
    name: string
    country?: string
    logo?: string
  }
  teams: {
    home: { id: number; name: string; logo?: string }
    away: { id: number; name: string; logo?: string }
  }
  lineupConfirmed: boolean
  odds1xBet?: { home: number | null; draw: number | null; away: number | null } | null
  decision?: string
  valueEdge?: number
  expectedValue?: number
  onAnalyze?: (id: string | number) => void
  isAnalyzing?: boolean
}

export default function MatchCard({
  id,
  kickoff,
  league,
  teams,
  lineupConfirmed,
  odds1xBet,
  decision = 'LINEUP_UNCONFIRMED',
  valueEdge,
  expectedValue,
  onAnalyze,
  isAnalyzing = false,
}: MatchCardProps) {
  const timeUntil = getTimeUntilKickoff(kickoff)
  const isCandidate = decision === 'CANDIDATE' || decision === 'HIGH CONFIDENCE CANDIDATE'
  const hasOdds = odds1xBet && (odds1xBet.home || odds1xBet.draw || odds1xBet.away)

  return (
    <div className="bg-[#0F172A] border border-[#1E293B] hover:border-[#334155] rounded-xl p-5 transition-all duration-150 flex flex-col justify-between shadow-sm group">
      <div className="space-y-4">
        {/* Card Header: League & Kickoff IST */}
        <div className="flex items-center justify-between text-xs text-[#94A3B8] border-b border-[#1E293B] pb-3">
          <div className="flex items-center gap-2 truncate">
            {league.logo && (
              <img
                src={league.logo}
                alt=""
                className="w-4 h-4 object-contain opacity-80 shrink-0"
              />
            )}
            <span className="font-semibold text-[#F8FAFC] truncate">{league.name}</span>
            {league.country && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#0B0F17] text-[#94A3B8] border border-[#1E293B]">
                {league.country}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px] shrink-0">
            <span className="text-[#64748B]">{timeUntil.text}</span>
            <span className="text-[#1E293B]">·</span>
            <span className="text-[#F8FAFC] font-medium">{formatISTDateTime(kickoff)}</span>
          </div>
        </div>

        {/* Matchup Banner */}
        <div className="flex items-center justify-between py-1">
          {/* Home Team */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-[#0B0F17] border border-[#1E293B] p-2 flex items-center justify-center shrink-0">
              {teams.home.logo ? (
                <img src={teams.home.logo} alt="" className="w-6 h-6 object-contain" />
              ) : (
                <span className="text-xs font-mono font-bold text-[#94A3B8]">
                  {teams.home.name.substring(0, 3).toUpperCase()}
                </span>
              )}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold tracking-tight text-[#F8FAFC] truncate">
                {teams.home.name}
              </div>
              <div className="text-[10px] font-mono text-[#64748B]">Home</div>
            </div>
          </div>

          {/* VS */}
          <div className="px-2 shrink-0">
            <span className="text-[10px] font-mono font-bold text-[#64748B] px-2 py-0.5 rounded-full bg-[#0B0F17] border border-[#1E293B]">
              VS
            </span>
          </div>

          {/* Away Team */}
          <div className="flex items-center justify-end gap-3 flex-1 min-w-0 text-right">
            <div className="min-w-0">
              <div className="text-sm font-semibold tracking-tight text-[#F8FAFC] truncate">
                {teams.away.name}
              </div>
              <div className="text-[10px] font-mono text-[#64748B]">Away</div>
            </div>
            <div className="w-10 h-10 rounded-lg bg-[#0B0F17] border border-[#1E293B] p-2 flex items-center justify-center shrink-0">
              {teams.away.logo ? (
                <img src={teams.away.logo} alt="" className="w-6 h-6 object-contain" />
              ) : (
                <span className="text-xs font-mono font-bold text-[#94A3B8]">
                  {teams.away.name.substring(0, 3).toUpperCase()}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 1xBet Fixed Odds Bar */}
        <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" />
              <span className="text-[#F8FAFC] font-semibold text-[11px]">1xBet Fixed Odds</span>
            </div>
            <span
              className={`text-[10px] font-mono px-2 py-0.2 rounded border ${
                hasOdds
                  ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30 font-semibold'
                  : 'bg-[#1E293B] text-[#64748B] border-[#334155]'
              }`}
            >
              {hasOdds ? 'Verified Feed' : 'Odds Pending'}
            </span>
          </div>

          {hasOdds ? (
            <div className="grid grid-cols-3 gap-2 text-center font-mono">
              <div className="bg-[#0F172A] border border-[#1E293B] rounded p-2">
                <div className="text-[9px] text-[#64748B]">1</div>
                <div className="text-sm font-bold text-[#D4AF37]">{odds1xBet?.home?.toFixed(2) ?? '—'}</div>
              </div>
              <div className="bg-[#0F172A] border border-[#1E293B] rounded p-2">
                <div className="text-[9px] text-[#64748B]">X</div>
                <div className="text-sm font-bold text-[#D4AF37]">{odds1xBet?.draw?.toFixed(2) ?? '—'}</div>
              </div>
              <div className="bg-[#0F172A] border border-[#1E293B] rounded p-2">
                <div className="text-[9px] text-[#64748B]">2</div>
                <div className="text-sm font-bold text-[#D4AF37]">{odds1xBet?.away?.toFixed(2) ?? '—'}</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-2 text-[11px] text-[#64748B] font-mono">
              1xBet odds stored in cache. Open match detail for full analysis.
            </div>
          )}
        </div>

        {/* Value Edge Strip if candidate */}
        {isCandidate && valueEdge && (
          <div className="p-2.5 rounded-lg bg-[#10B981]/10 border border-[#10B981]/30 flex items-center justify-between text-xs font-mono">
            <span className="text-[#10B981] font-semibold">Value Candidate: +{valueEdge.toFixed(1)} pp Edge</span>
            {expectedValue && <span className="text-[#10B981] font-bold">EV: +{expectedValue.toFixed(1)}%</span>}
          </div>
        )}
      </div>

      {/* Card Footer: Lineup Status & Navigation Link */}
      <div className="mt-4 pt-3 border-t border-[#1E293B] flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              lineupConfirmed ? 'bg-[#10B981]' : 'bg-[#F59E0B]'
            }`}
          />
          <span className="text-[#94A3B8]">
            Lineup: {lineupConfirmed ? 'Confirmed' : 'Pending (T-60m)'}
          </span>
        </div>

        <Link
          href={`/matches/${id}`}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1E293B] hover:bg-[#334155] text-[#F8FAFC] font-medium transition-colors"
        >
          <span>Match Terminal</span>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </div>
  )
}
