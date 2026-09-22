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
      // Keep state
    } finally {
      setLoading(false)
    }
  }

  // Initial load only - no auto polling
  useEffect(() => {
    fetchLive()
  }, [])

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <h2 className="text-xl font-medium tracking-tight text-white">Live In-Play</h2>
          </div>
          <span className="text-[11px] font-mono text-neutral-400 bg-white/[0.04] border border-white/[0.08] px-2 py-0.5 rounded-full">
            {matches.length} Active
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono text-neutral-500 hidden sm:inline">
            Synced: {lastUpdated}
          </span>
          <button
            onClick={fetchLive}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-[12px] font-medium text-neutral-300 bg-[#0e0e11] hover:bg-[#16161a] hover:text-white border border-white/[0.08] rounded-lg transition-colors disabled:opacity-50 font-mono shadow-sm"
          >
            <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {loading ? 'Updating' : 'Refresh'}
          </button>
        </div>
      </div>

      {loading && matches.length === 0 ? (
        <div className="bg-[#0a0a0c] border border-white/[0.06] rounded-2xl p-6 text-center text-neutral-500 text-xs font-mono">
          Scanning live feeds...
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-2xl p-6 text-center">
          <p className="text-sm font-medium text-neutral-300">No live matches in play across allowlisted competitions.</p>
          <p className="text-xs text-neutral-500 mt-1 max-w-lg mx-auto font-normal">
            Real-time score-state hazard rates and in-play next-goal models activate automatically at kickoff.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matches.map((m) => (
            <div key={m.id} className="bg-[#0c0c0e] border border-white/[0.08] rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between text-xs text-neutral-400 pb-2 border-b border-white/[0.06] font-mono">
                <span>{m.league.name}</span>
                <span className="font-semibold text-emerald-400">{m.minute}' ({m.status})</span>
              </div>
              <div className="grid grid-cols-5 items-center py-4 text-center">
                <div className="col-span-2 text-sm font-semibold text-white">{m.teams.home.name}</div>
                <div className="col-span-1 text-2xl font-mono font-bold text-white">
                  {m.score.home} - {m.score.away}
                </div>
                <div className="col-span-2 text-sm font-semibold text-white">{m.teams.away.name}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
