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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-wide">Upcoming Matches</h2>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-950 text-blue-300 border border-blue-800">
              {matches.length} Scheduled
            </span>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-2 py-0.5 rounded">
              Timings in IST (UTC+5:30)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Strict statistical predictions unlock once official starting lineups are confirmed (~60m before kickoff)
          </p>
        </div>
        <button
          onClick={fetchUpcoming}
          disabled={loading}
          className="inline-flex items-center gap-1.5 self-start sm:self-auto px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 active:bg-slate-900 border border-slate-700 rounded-lg transition disabled:opacity-50"
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
            <div key={i} className="animate-pulse bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
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
        <div className="bg-red-950/40 border border-red-900/50 text-red-300 text-sm p-4 rounded-xl flex items-center justify-between">
          <span>Failed to load upcoming fixtures: {error}</span>
          <button onClick={fetchUpcoming} className="underline hover:text-white text-xs">Retry</button>
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
          <p className="text-sm">No eligible upcoming matches scheduled in your allowlisted competitions in the next 48 hours.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {matches.map((m) => {
            const has1xBet = m.odds1xBet && (m.odds1xBet.home || m.odds1xBet.draw || m.odds1xBet.away)

            return (
              <div
                key={m.id}
                className="bg-slate-900/90 border border-slate-800/90 hover:border-slate-700/80 rounded-xl p-5 shadow-lg shadow-black/40 transition flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: League & IST Countdown */}
                  <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5 mb-3 text-xs">
                    <div className="flex items-center gap-2">
                      {m.league.logo && (
                        <img src={m.league.logo} alt="" className="w-4 h-4 object-contain" />
                      )}
                      <span className="font-semibold text-slate-300">{m.league.name}</span>
                      {m.league.country && (
                        <span className="text-slate-500">· {m.league.country}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <span className="font-mono text-amber-400 font-medium">{getTimeUntil(m.kickoff)}</span>
                      <span>·</span>
                      <span className="font-semibold text-slate-200">{formatKickoffIST(m.kickoff)}</span>
                    </div>
                  </div>

                  {/* Teams Display */}
                  <div className="grid grid-cols-7 items-center py-2 text-center">
                    <div className="col-span-3 flex flex-col items-center gap-1.5">
                      <div className="w-12 h-12 bg-slate-800/80 rounded-full p-2 flex items-center justify-center border border-slate-700/60 shadow">
                        {m.teams.home.logo ? (
                          <img src={m.teams.home.logo} alt={m.teams.home.name} className="w-8 h-8 object-contain" />
                        ) : (
                          <span className="text-sm font-bold text-slate-400">{m.teams.home.name.substring(0, 3)}</span>
                        )}
                      </div>
                      <span className="text-sm font-bold text-white tracking-wide leading-tight">
                        {m.teams.home.name}
                      </span>
                    </div>

                    <div className="col-span-1 flex flex-col items-center">
                      <span className="text-xs uppercase font-extrabold text-slate-500 bg-slate-800/50 px-2 py-0.5 rounded">
                        VS
                      </span>
                    </div>

                    <div className="col-span-3 flex flex-col items-center gap-1.5">
                      <div className="w-12 h-12 bg-slate-800/80 rounded-full p-2 flex items-center justify-center border border-slate-700/60 shadow">
                        {m.teams.away.logo ? (
                          <img src={m.teams.away.logo} alt={m.teams.away.name} className="w-8 h-8 object-contain" />
                        ) : (
                          <span className="text-sm font-bold text-slate-400">{m.teams.away.name.substring(0, 3)}</span>
                        )}
                      </div>
                      <span className="text-sm font-bold text-white tracking-wide leading-tight">
                        {m.teams.away.name}
                      </span>
                    </div>
                  </div>

                  {/* 1xBet Market Bar */}
                  <div className="mt-4 bg-slate-950/70 border border-slate-800 rounded-lg p-2.5">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-orange-500"></span>
                        <span className="font-semibold text-orange-400">1xBet Match Winner Odds</span>
                      </div>
                      {has1xBet ? (
                        <span className="text-[11px] text-emerald-400 font-medium">● 1xBet Feed Active</span>
                      ) : (
                        <span className="text-[11px] text-slate-500">Pending Market Feed</span>
                      )}
                    </div>

                    {has1xBet ? (
                      <div className="grid grid-cols-3 gap-2 text-center text-xs">
                        <div className="bg-slate-900 border border-slate-800 rounded py-1.5">
                          <div className="text-[10px] text-slate-400 uppercase font-medium">1 ({m.teams.home.name})</div>
                          <div className="text-sm font-bold text-white font-mono mt-0.5">{m.odds1xBet?.home?.toFixed(2) ?? '-'}</div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {m.odds1xBet?.home ? `${(100 / m.odds1xBet.home).toFixed(1)}%` : ''}
                          </div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded py-1.5">
                          <div className="text-[10px] text-slate-400 uppercase font-medium">X (Draw)</div>
                          <div className="text-sm font-bold text-white font-mono mt-0.5">{m.odds1xBet?.draw?.toFixed(2) ?? '-'}</div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {m.odds1xBet?.draw ? `${(100 / m.odds1xBet.draw).toFixed(1)}%` : ''}
                          </div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded py-1.5">
                          <div className="text-[10px] text-slate-400 uppercase font-medium">2 ({m.teams.away.name})</div>
                          <div className="text-sm font-bold text-white font-mono mt-0.5">{m.odds1xBet?.away?.toFixed(2) ?? '-'}</div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {m.odds1xBet?.away ? `${(100 / m.odds1xBet.away).toFixed(1)}%` : ''}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic py-1 text-center">
                        Target bookmaker odds updating automatically from provider feed...
                      </p>
                    )}
                  </div>

                  {/* Lineup Gating Alert Notice with IST Time */}
                  <div className="mt-3.5 bg-amber-950/20 border border-amber-900/40 rounded-lg p-2.5 text-xs text-amber-200/90 flex items-start gap-2.5">
                    <span className="text-base leading-none mt-0.5">🔒</span>
                    <div>
                      <span className="font-semibold text-amber-300">Awaiting Confirmed Starting Lineups</span>
                      <p className="text-[11px] text-amber-200/70 mt-0.5 leading-relaxed">
                        Official starting XIs drop ~60m before kickoff. Please check at{' '}
                        <strong className="text-amber-200 underline font-mono font-bold bg-amber-950/60 px-1 py-0.5 rounded">
                          {formatLineupTimeIST(m.lineupExpectedAt)}
                        </strong>{' '}
                        for match analysis after lineups announcement (Monte Carlo & 1xBet EV gates will unlock).
                      </p>
                    </div>
                  </div>
                </div>

                {/* Footer status */}
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                    <span className="text-slate-400">Gate: <strong className="text-amber-400">NO-BET (LINEUP_UNCONFIRMED)</strong></span>
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">ID: #{m.id}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
