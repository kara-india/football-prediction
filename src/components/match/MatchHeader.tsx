'use client'

import React, { useState } from 'react'
import { formatISTDateTime, getTimeUntilKickoff } from '@/lib/dateUtils'

export interface MatchHeaderProps {
  matchId: string
  homeTeam: {
    name: string
    logo?: string
    form?: string[] // e.g. ['W', 'D', 'W', 'W', 'L']
    score?: number
  }
  awayTeam: {
    name: string
    logo?: string
    form?: string[]
    score?: number
  }
  competition: {
    name: string
    country?: string
    logo?: string
    round?: string
  }
  status: string // 'NS', 'LIVE', '1H', '2H', 'HT', 'FT'
  minute?: number
  kickoffUtc: string
  venue?: string
  referee?: string
  onRefresh?: () => Promise<void>
}

export default function MatchHeader({
  matchId,
  homeTeam,
  awayTeam,
  competition,
  status,
  minute,
  kickoffUtc,
  venue = 'Official Venue TBD',
  referee = 'Match Officials Verified',
  onRefresh,
}: MatchHeaderProps) {
  const [refreshing, setRefreshing] = useState(false)
  const isLive = ['1H', '2H', 'HT', 'ET', 'LIVE'].includes(status)
  const isFinished = ['FT', 'AET', 'PEN'].includes(status)
  const isUpcoming = status === 'NS' || status === 'TBD'
  const timeUntil = getTimeUntilKickoff(kickoffUtc)

  const handleRefreshClick = async () => {
    if (!onRefresh || refreshing) return
    setRefreshing(true)
    try {
      await onRefresh()
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl overflow-hidden shadow-sm">
      {/* Top Metadata Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 sm:px-6 py-3 bg-[#0B0F17] border-b border-[#1E293B] text-xs font-mono">
        <div className="flex items-center gap-2 truncate">
          {competition.logo ? (
            <img
              src={competition.logo}
              alt=""
              className="w-4 h-4 object-contain opacity-90 shrink-0"
            />
          ) : (
            <span className="w-2 h-2 rounded-full bg-[#3B82F6]" />
          )}
          <span className="font-semibold text-[#F8FAFC] truncate">{competition.name}</span>
          {competition.country && (
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#131924] text-[#94A3B8] border border-[#1E293B]">
              {competition.country}
            </span>
          )}
          {competition.round && (
            <span className="text-[#64748B] hidden sm:inline">· {competition.round}</span>
          )}
          <span className="text-[#64748B]">· ID: {matchId}</span>
        </div>

        {/* Kickoff / Elapsed time & On-Demand Refresh */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[#64748B] hidden sm:inline">Kickoff (IST):</span>
            <span className="text-[#F8FAFC] font-semibold">
              {formatISTDateTime(kickoffUtc)}
            </span>
          </div>

          {onRefresh && (
            <button
              onClick={handleRefreshClick}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#1E293B] hover:bg-[#334155] text-[#F8FAFC] text-xs transition-colors disabled:opacity-50"
              title="Refresh match telemetry (Uses 1 user credit)"
            >
              <svg
                className={`w-3.5 h-3.5 text-[#D4AF37] ${refreshing ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span className="hidden sm:inline">{refreshing ? 'Refreshing' : 'Refresh'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Score & Teams Arena */}
      <div className="px-4 sm:px-8 py-6">
        <div className="grid grid-cols-7 items-center gap-2 sm:gap-6">
          {/* Home Team */}
          <div className="col-span-3 flex flex-col sm:flex-row items-center sm:justify-end gap-3 text-center sm:text-right min-w-0">
            <div className="order-2 sm:order-1 min-w-0">
              <h2 className="text-base sm:text-2xl font-bold tracking-tight text-[#F8FAFC] truncate">
                {homeTeam.name}
              </h2>
              <div className="text-[11px] font-mono text-[#94A3B8] mt-0.5">Home</div>
              {homeTeam.form && (
                <div className="flex items-center justify-center sm:justify-end gap-1 mt-1.5">
                  {homeTeam.form.map((res, idx) => (
                    <span
                      key={idx}
                      className={`w-4 h-4 rounded text-[9px] font-mono font-bold flex items-center justify-center ${
                        res === 'W'
                          ? 'bg-[#10B981]/20 text-[#10B981]'
                          : res === 'D'
                          ? 'bg-[#F59E0B]/20 text-[#F59E0B]'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {res}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="order-1 sm:order-2 w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-[#0B0F17] border border-[#1E293B] p-2.5 flex items-center justify-center shrink-0 shadow-sm">
              {homeTeam.logo ? (
                <img
                  src={homeTeam.logo}
                  alt={homeTeam.name}
                  className="w-10 h-10 object-contain"
                />
              ) : (
                <span className="text-sm font-mono font-bold text-[#94A3B8]">
                  {homeTeam.name.substring(0, 3).toUpperCase()}
                </span>
              )}
            </div>
          </div>

          {/* Central Score / Status */}
          <div className="col-span-1 flex flex-col items-center justify-center text-center">
            {isLive ? (
              <div className="space-y-1">
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-ping" />
                  {minute}&apos;
                </span>
                <div className="text-2xl sm:text-4xl font-mono font-extrabold text-[#D4AF37] tracking-tight">
                  {homeTeam.score ?? 0} – {awayTeam.score ?? 0}
                </div>
                <div className="text-[10px] font-mono text-[#94A3B8]">{status}</div>
              </div>
            ) : isFinished ? (
              <div className="space-y-1">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1E293B] text-[#94A3B8]">
                  Full Time
                </span>
                <div className="text-2xl sm:text-4xl font-mono font-extrabold text-[#F8FAFC]">
                  {homeTeam.score ?? 0} – {awayTeam.score ?? 0}
                </div>
              </div>
            ) : (
              <div className="space-y-1.5">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#D4AF37]/15 text-[#D4AF37] border border-[#D4AF37]/30">
                  {timeUntil.text}
                </span>
                <div className="text-lg sm:text-2xl font-mono font-bold text-[#64748B]">
                  VS
                </div>
                <div className="text-[10px] font-mono text-[#94A3B8]">Scheduled</div>
              </div>
            )}
          </div>

          {/* Away Team */}
          <div className="col-span-3 flex flex-col sm:flex-row items-center sm:justify-start gap-3 text-center sm:text-left min-w-0">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl bg-[#0B0F17] border border-[#1E293B] p-2.5 flex items-center justify-center shrink-0 shadow-sm">
              {awayTeam.logo ? (
                <img
                  src={awayTeam.logo}
                  alt={awayTeam.name}
                  className="w-10 h-10 object-contain"
                />
              ) : (
                <span className="text-sm font-mono font-bold text-[#94A3B8]">
                  {awayTeam.name.substring(0, 3).toUpperCase()}
                </span>
              )}
            </div>
            <div className="min-w-0">
              <h2 className="text-base sm:text-2xl font-bold tracking-tight text-[#F8FAFC] truncate">
                {awayTeam.name}
              </h2>
              <div className="text-[11px] font-mono text-[#94A3B8] mt-0.5">Away</div>
              {awayTeam.form && (
                <div className="flex items-center justify-center sm:justify-start gap-1 mt-1.5">
                  {awayTeam.form.map((res, idx) => (
                    <span
                      key={idx}
                      className={`w-4 h-4 rounded text-[9px] font-mono font-bold flex items-center justify-center ${
                        res === 'W'
                          ? 'bg-[#10B981]/20 text-[#10B981]'
                          : res === 'D'
                          ? 'bg-[#F59E0B]/20 text-[#F59E0B]'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {res}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Venue & Ref info bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 sm:px-6 py-2.5 bg-[#0B0F17] border-t border-[#1E293B] text-[11px] font-mono text-[#64748B]">
        <div className="flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-[#94A3B8]">{venue}</span>
        </div>

        <div className="flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span className="text-[#94A3B8]">{referee}</span>
        </div>
      </div>
    </div>
  )
}
