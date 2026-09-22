'use client'

import React, { useEffect, useState } from 'react'

interface LiveMatch {
  id: number
  minute: number
  status: string
  statusLong: string
  score: { home: number; away: number }
  league: { id: number; name: string; country: string; logo: string }
  teams: {
    home: { id: number; name: string; logo: string }
    away: { id: number; name: string; logo: string }
  }
}

export default function LiveMatchSection() {
  const [matches, setMatches] = useState<LiveMatch[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string>('Just now')

  const fetchLive = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/matches/live')
      if (res.ok) {
        const data = await res.json()
        setMatches(data)
        const now = new Date()
        setLastUpdated(
          now.toLocaleTimeString('en-IN', {
            timeZone: 'Asia/Kolkata',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          }) + ' IST'
        )
      }
    } catch {
      // Keep existing state
    } finally {
      setLoading(false)
    }
  }

  // ONLY run on initial component mount — NO background setInterval polling!
  useEffect(() => {
    fetchLive()
  }, [])

  return (
    <section className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-emerald-950/80 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
          </span>
          <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
            Live Matches
          </h2>
          <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
            {matches.length} Active
          </span>
          <span className="text-[11px] font-mono text-emerald-400/90 bg-emerald-950/40 border border-emerald-900/60 px-2 py-0.5 rounded">
            Manual Sync Only (0 Auto-Polling)
          </span>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
            Updated: {lastUpdated}
          </span>
          <button
            onClick={fetchLive}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-300 bg-[#0c1618] hover:bg-[#122023] active:bg-black border border-emerald-800/80 rounded-lg transition disabled:opacity-50 font-mono shadow-sm"
          >
            <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {loading ? 'Checking...' : 'Refresh Live'}
          </button>
        </div>
      </div>

      {loading && matches.length === 0 ? (
        <div className="bg-[#0b1315] border border-emerald-950 rounded-2xl p-6 text-center text-slate-500 text-sm animate-pulse font-mono">
          Scanning live match feeds...
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-gradient-to-b from-[#0c1417] to-[#090f11] border border-emerald-950/90 rounded-2xl p-7 text-center shadow-lg">
          <div className="w-10 h-10 rounded-full bg-[#111c1f] text-emerald-400 flex items-center justify-center mx-auto mb-2 border border-emerald-900/50">
            ✓
          </div>
          <p className="text-sm font-semibold text-slate-300">No live matches currently in play across your allowlisted competitions.</p>
          <p className="text-xs text-slate-500 mt-1 max-w-xl mx-auto">
            Live hazard rates & 1xBet next-goal model distributions activate automatically at kickoff with real-time score-state tracking.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matches.map((m) => (
            <div key={m.id} className="bg-[#0c1417] border border-emerald-950/90 hover:border-amber-500/40 rounded-2xl p-4 shadow-xl transition">
              <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-emerald-950/80 font-mono">
                <span>{m.league.name}</span>
                <span className="font-bold text-emerald-400">{m.minute}' ({m.status})</span>
              </div>
              <div className="grid grid-cols-5 items-center py-4 text-center">
                <div className="col-span-2 text-sm font-bold text-white">{m.teams.home.name}</div>
                <div className="col-span-1 text-2xl font-mono font-extrabold text-amber-300">
                  {m.score.home} - {m.score.away}
                </div>
                <div className="col-span-2 text-sm font-bold text-white">{m.teams.away.name}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
