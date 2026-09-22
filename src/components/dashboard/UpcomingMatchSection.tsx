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

  // Explicitly format to Indian Standard Time (IST, UTC+5:30)
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
    <section className="space-y-4">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-emerald-950/80 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
              <span className="text-amber-400">❖</span> Upcoming Matches
            </h2>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 font-mono">
              {matches.length} Scheduled
            </span>
            <span className="text-[11px] font-mono text-amber-300 bg-amber-950/50 border border-amber-800/70 px-2 py-0.5 rounded font-semibold">
              IST (UTC+5:30)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Strict statistical predictions unlock once official starting lineups are confirmed (~60m before kickoff)
          </p>
        </div>

        <button
          onClick={fetchUpcoming}
          disabled={loading}
          className="inline-flex items-center gap-1.5 self-start sm:self-auto px-3.5 py-1.5 text-xs font-semibold text-emerald-300 bg-[#0c1618] hover:bg-[#122023] active:bg-black border border-emerald-800/80 rounded-lg transition disabled:opacity-50 font-mono shadow-sm"
        >
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {loading ? 'Refreshing...' : 'Refresh Fixtures'}
        </button>
      </div>

      {loading && matches.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse bg-[#0d1618] border border-emerald-950 rounded-xl p-5 space-y-4">
              <div className="h-4 bg-slate-800 rounded w-1/3"></div>
              <div className="flex justify-between items-center py-4">
                <div className="h-8 bg-slate-800 rounded w-1/3"></div>
                <div className="h-6 bg-slate-800 rounded w-12"></div>
                <div className="h-8 bg-slate-800 rounded w-1/3"></div>
              </div>
              <div className="h-10 bg-slate-800/50 rounded"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-rose-950/40 border border-rose-900/50 text-rose-300 text-sm p-4 rounded-xl flex items-center justify-between">
          <span>Failed to load upcoming fixtures: {error}</span>
          <button onClick={fetchUpcoming} className="underline hover:text-white text-xs font-mono">Retry</button>
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-[#0b1315] border border-emerald-950 rounded-xl p-8 text-center text-slate-400">
          <p className="text-sm">No eligible upcoming matches scheduled in your allowlisted competitions in the next 48 hours.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {matches.map((m) => {
            const has1xBet = m.odds1xBet && (m.odds1xBet.home || m.odds1xBet.draw || m.odds1xBet.away)

            return (
              <div
                key={m.id}
                className="bg-gradient-to-b from-[#0c1417] to-[#090f11] border border-emerald-950/90 hover:border-amber-500/50 rounded-2xl p-5 shadow-xl transition-all duration-200 flex flex-col justify-between group"
              >
                <div>
                  {/* Top Bar: League & IST Countdown */}
                  <div className="flex items-center justify-between gap-2 border-b border-emerald-950/80 pb-2.5 mb-3 text-xs">
                    <div className="flex items-center gap-2">
                      {m.league.logo && (
                        <img src={m.league.logo} alt="" className="w-4 h-4 object-contain" />
                      )}
                      <span className="font-semibold text-slate-200">{m.league.name}</span>
                      {m.league.country && (
                        <span className="text-slate-500">· {m.league.country}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs font-mono">
                      <span className="text-amber-400 font-bold">{getTimeUntil(m.kickoff)}</span>
                      <span className="text-slate-600">·</span>
                      <span className="text-slate-300 font-semibold">{formatKickoffIST(m.kickoff)}</span>
                    </div>
                  </div>

                  {/* Teams Display */}
                  <div className="grid grid-cols-7 items-center py-2 text-center">
                    <div className="col-span-3 flex flex-col items-center gap-1.5">
                      <div className="w-13 h-13 bg-[#111c1f] rounded-2xl p-2.5 flex items-center justify-center border border-emerald-900/40 shadow-inner group-hover:border-emerald-700/60 transition">
                        {m.teams.home.logo ? (
                          <img src={m.teams.home.logo} alt={m.teams.home.name} className="w-8 h-8 object-contain" />
                        ) : (
                          <span className="text-sm font-bold text-amber-400 font-mono">{m.teams.home.name.substring(0, 3)}</span>
                        )}
                      </div>
                      <span className="text-sm font-extrabold text-white tracking-wide leading-tight">
                        {m.teams.home.name}
                      </span>
                    </div>

                    <div className="col-span-1 flex flex-col items-center">
                      <span className="text-[11px] uppercase font-mono font-black text-amber-400/90 bg-[#142023] px-2 py-0.5 rounded border border-amber-500/20 shadow">
                        VS
                      </span>
                    </div>

                    <div className="col-span-3 flex flex-col items-center gap-1.5">
                      <div className="w-13 h-13 bg-[#111c1f] rounded-2xl p-2.5 flex items-center justify-center border border-emerald-900/40 shadow-inner group-hover:border-emerald-700/60 transition">
                        {m.teams.away.logo ? (
                          <img src={m.teams.away.logo} alt={m.teams.away.name} className="w-8 h-8 object-contain" />
                        ) : (
                          <span className="text-sm font-bold text-amber-400 font-mono">{m.teams.away.name.substring(0, 3)}</span>
                        )}
                      </div>
                      <span className="text-sm font-extrabold text-white tracking-wide leading-tight">
                        {m.teams.away.name}
                      </span>
                    </div>
                  </div>

                  {/* 1xBet Gold Odds Market Bar */}
                  <div className="mt-4 bg-[#070b0c] border border-amber-500/30 rounded-xl p-3 shadow-inner">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <div className="flex items-center gap-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50"></span>
                        <span className="font-bold text-amber-300 font-mono tracking-wide">1xBet Fixed Odds (Target Price)</span>
                      </div>
                      {has1xBet ? (
                        <span className="text-[10px] text-emerald-400 font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800">
                          ● FEED VERIFIED
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-500 font-mono">PENDING ODDS</span>
                      )}
                    </div>

                    {has1xBet ? (
                      <div className="grid grid-cols-3 gap-2 text-center font-mono">
                        <div className="bg-[#0e1619] border border-emerald-950 hover:border-amber-500/40 rounded-lg py-2 transition">
                          <div className="text-[10px] text-slate-400 uppercase font-medium">1 ({m.teams.home.name.substring(0, 8)})</div>
                          <div className="text-base font-black text-amber-300 mt-0.5">{m.odds1xBet?.home?.toFixed(2) ?? '-'}</div>
                          <div className="text-[10px] text-emerald-400 font-semibold">
                            {m.odds1xBet?.home ? `${(100 / m.odds1xBet.home).toFixed(1)}%` : ''}
                          </div>
                        </div>

                        <div className="bg-[#0e1619] border border-emerald-950 hover:border-amber-500/40 rounded-lg py-2 transition">
                          <div className="text-[10px] text-slate-400 uppercase font-medium">X (Draw)</div>
                          <div className="text-base font-black text-amber-300 mt-0.5">{m.odds1xBet?.draw?.toFixed(2) ?? '-'}</div>
                          <div className="text-[10px] text-emerald-400 font-semibold">
                            {m.odds1xBet?.draw ? `${(100 / m.odds1xBet.draw).toFixed(1)}%` : ''}
                          </div>
                        </div>

                        <div className="bg-[#0e1619] border border-emerald-950 hover:border-amber-500/40 rounded-lg py-2 transition">
                          <div className="text-[10px] text-slate-400 uppercase font-medium">2 ({m.teams.away.name.substring(0, 8)})</div>
                          <div className="text-base font-black text-amber-300 mt-0.5">{m.odds1xBet?.away?.toFixed(2) ?? '-'}</div>
                          <div className="text-[10px] text-emerald-400 font-semibold">
                            {m.odds1xBet?.away ? `${(100 / m.odds1xBet.away).toFixed(1)}%` : ''}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic py-1 text-center font-mono">
                        Target bookmaker odds updating automatically from provider feed...
                      </p>
                    )}
                  </div>

                  {/* Lineup Gating Alert Notice with IST Time */}
                  <div className="mt-3.5 bg-gradient-to-r from-amber-950/20 to-emerald-950/10 border border-amber-800/40 rounded-xl p-3 text-xs text-amber-200/90 flex items-start gap-2.5">
                    <span className="text-base leading-none mt-0.5">🔒</span>
                    <div>
                      <span className="font-bold text-amber-300 flex items-center gap-1.5">
                        Awaiting Confirmed Starting Lineups
                      </span>
                      <p className="text-[11px] text-amber-200/80 mt-1 leading-relaxed">
                        Official starting XIs drop ~60m before kickoff. Please check at{' '}
                        <strong className="text-amber-300 font-mono font-extrabold bg-amber-950/80 border border-amber-700/60 px-1.5 py-0.5 rounded shadow-sm">
                          {formatLineupTimeIST(m.lineupExpectedAt)}
                        </strong>{' '}
                        for match analysis after lineups announcement (Monte Carlo & 1xBet EV gates will unlock).
                      </p>
                    </div>
                  </div>
                </div>

                {/* Footer status */}
                <div className="mt-4 pt-3 border-t border-emerald-950/80 flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                    <span className="text-slate-400">Gate: <strong className="text-amber-400">NO-BET (LINEUP_UNCONFIRMED)</strong></span>
                  </div>
                  <span className="text-[10px] text-slate-500">ID: #{m.id}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
