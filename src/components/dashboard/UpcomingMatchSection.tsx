'use client'

import React, { useEffect, useState } from 'react'

interface Match {
  id: number
  kickoff: string
  venue: string
  status: string
  statusLong: string
  league: {
    id: number
    name: string
    country: string
    logo: string
  }
  teams: {
    home: { id: number; name: string; logo: string }
    away: { id: number; name: string; logo: string }
  }
  lineupConfirmed: boolean
  lineupExpectedAt: string
  odds1xBet: { home: number | null; draw: number | null; away: number | null } | null
  decision: string
}

export default function UpcomingMatchSection() {
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUpcoming = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/matches/upcoming')
      if (!res.ok) throw new Error('Failed to load upcoming fixtures')
      const data = await res.json()
      setMatches(data)
    } catch (err: any) {
      setError(err.message || 'Error loading matches')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUpcoming()
  }, [])

  const formatKickoffIST = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }) + ' IST'
  }

  const formatLineupTimeIST = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }) + ' IST'
  }

  const getTimeUntil = (isoString: string) => {
    const diff = new Date(isoString).getTime() - Date.now()
    if (diff <= 0) return 'Kickoff imminent'
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    if (hours > 24) {
      const days = Math.floor(hours / 24)
      return `in ${days}d ${hours % 24}h`
    }
    return `in ${hours}h ${mins}m`
  }

  return (
    <section className="space-y-5">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-medium tracking-tight text-white">Upcoming Fixtures</h2>
            <span className="text-[11px] font-mono text-neutral-400 bg-white/[0.04] border border-white/[0.08] px-2 py-0.5 rounded-full">
              {matches.length} Scheduled
            </span>
          </div>
          <p className="text-[13px] text-neutral-500 font-normal">
            Statistical prediction models unlock once official starting XIs are verified
          </p>
        </div>

        <button
          onClick={fetchUpcoming}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 text-[12px] font-medium text-neutral-300 bg-[#0e0e11] hover:bg-[#16161a] hover:text-white border border-white/[0.08] rounded-lg transition-colors disabled:opacity-50 font-mono shadow-sm"
        >
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {loading ? 'Updating' : 'Refresh'}
        </button>
      </div>

      {loading && matches.length === 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse bg-[#0a0a0c] border border-white/[0.06] rounded-2xl p-6 space-y-4">
              <div className="h-4 bg-neutral-900 rounded w-1/4"></div>
              <div className="h-16 bg-neutral-900/60 rounded"></div>
              <div className="h-10 bg-neutral-900/40 rounded"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-[#120a0a] border border-rose-900/40 text-rose-300 text-xs p-4 rounded-xl flex items-center justify-between">
          <span>Failed to load fixtures: {error}</span>
          <button onClick={fetchUpcoming} className="underline text-xs">Retry</button>
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-[#0a0a0c] border border-white/[0.06] rounded-2xl p-10 text-center text-neutral-500 text-sm">
          No matches scheduled in allowlisted competitions in the next 48 hours.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {matches.map((m) => {
            const has1xBet = m.odds1xBet && (m.odds1xBet.home || m.odds1xBet.draw || m.odds1xBet.away)

            return (
              <div
                key={m.id}
                className="bg-[#0c0c0e] border border-white/[0.08] hover:border-white/[0.16] rounded-2xl p-6 transition-all duration-200 flex flex-col justify-between"
              >
                <div className="space-y-5">
                  {/* Card Header: League & Kickoff */}
                  <div className="flex items-center justify-between text-xs text-neutral-400 border-b border-white/[0.06] pb-3">
                    <div className="flex items-center gap-2">
                      {m.league.logo && (
                        <img src={m.league.logo} alt="" className="w-4 h-4 object-contain opacity-80" />
                      )}
                      <span className="font-medium text-neutral-300">{m.league.name}</span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      <span className="text-neutral-500">{getTimeUntil(m.kickoff)}</span>
                      <span className="text-neutral-700">·</span>
                      <span className="text-neutral-300 font-medium">{formatKickoffIST(m.kickoff)}</span>
                    </div>
                  </div>

                  {/* Match Matchup Typography */}
                  <div className="flex items-center justify-between py-2 px-2">
                    <div className="flex items-center gap-3.5 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-full bg-white/[0.03] border border-white/[0.08] p-2 flex items-center justify-center shrink-0">
                        {m.teams.home.logo ? (
                          <img src={m.teams.home.logo} alt={m.teams.home.name} className="w-6 h-6 object-contain" />
                        ) : (
                          <span className="text-xs font-mono font-medium text-neutral-400">{m.teams.home.name.substring(0, 3)}</span>
                        )}
                      </div>
                      <span className="text-base font-semibold tracking-tight text-white truncate">
                        {m.teams.home.name}
                      </span>
                    </div>

                    <span className="text-[11px] font-mono text-neutral-600 px-3 shrink-0">
                      VS
                    </span>

                    <div className="flex items-center justify-end gap-3.5 flex-1 min-w-0 text-right">
                      <span className="text-base font-semibold tracking-tight text-white truncate">
                        {m.teams.away.name}
                      </span>
                      <div className="w-10 h-10 rounded-full bg-white/[0.03] border border-white/[0.08] p-2 flex items-center justify-center shrink-0">
                        {m.teams.away.logo ? (
                          <img src={m.teams.away.logo} alt={m.teams.away.name} className="w-6 h-6 object-contain" />
                        ) : (
                          <span className="text-xs font-mono font-medium text-neutral-400">{m.teams.away.name.substring(0, 3)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 1xBet Minimalist Odds Pill */}
                  <div className="bg-[#070709] border border-white/[0.06] rounded-xl p-3 space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-neutral-500 uppercase tracking-wider">1xBet Fixed Odds</span>
                      {has1xBet ? (
                        <span className="text-emerald-400 text-[10px]">Verified Feed</span>
                      ) : (
                        <span className="text-neutral-600 text-[10px]">Pending</span>
                      )}
                    </div>

                    {has1xBet ? (
                      <div className="grid grid-cols-3 gap-2 text-center font-mono">
                        <div className="bg-[#0f0f12] border border-white/[0.04] rounded-lg py-2">
                          <div className="text-[10px] text-neutral-500">1</div>
                          <div className="text-sm font-semibold text-[#d4af37] mt-0.5">
                            {m.odds1xBet?.home?.toFixed(2) ?? '—'}
                          </div>
                          <div className="text-[10px] text-neutral-500">
                            {m.odds1xBet?.home ? `${(100 / m.odds1xBet.home).toFixed(1)}%` : ''}
                          </div>
                        </div>

                        <div className="bg-[#0f0f12] border border-white/[0.04] rounded-lg py-2">
                          <div className="text-[10px] text-neutral-500">X</div>
                          <div className="text-sm font-semibold text-[#d4af37] mt-0.5">
                            {m.odds1xBet?.draw?.toFixed(2) ?? '—'}
                          </div>
                          <div className="text-[10px] text-neutral-500">
                            {m.odds1xBet?.draw ? `${(100 / m.odds1xBet.draw).toFixed(1)}%` : ''}
                          </div>
                        </div>

                        <div className="bg-[#0f0f12] border border-white/[0.04] rounded-lg py-2">
                          <div className="text-[10px] text-neutral-500">2</div>
                          <div className="text-sm font-semibold text-[#d4af37] mt-0.5">
                            {m.odds1xBet?.away?.toFixed(2) ?? '—'}
                          </div>
                          <div className="text-[10px] text-neutral-500">
                            {m.odds1xBet?.away ? `${(100 / m.odds1xBet.away).toFixed(1)}%` : ''}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 font-mono text-center py-1">
                        Odds will update on-demand
                      </p>
                    )}
                  </div>

                  {/* Understated Lineup Notice */}
                  <div className="bg-[#070709] border border-white/[0.06] rounded-xl p-3 text-xs text-neutral-400 space-y-1">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-neutral-300 font-medium">Starting Lineup Verification</span>
                      <span className="text-[#d4af37] font-medium">{formatLineupTimeIST(m.lineupExpectedAt)}</span>
                    </div>
                    <p className="text-[11px] text-neutral-500 leading-relaxed font-normal">
                      Full Monte Carlo simulation and 1xBet EV evaluation activate ~60 minutes before kickoff upon official manager announcement.
                    </p>
                  </div>
                </div>

                {/* Card Footer */}
                <div className="mt-5 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-neutral-500">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400/80"></span>
                    <span>Gate: <span className="text-neutral-300">LINEUP_UNCONFIRMED</span></span>
                  </div>
                  <span>#{m.id}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
