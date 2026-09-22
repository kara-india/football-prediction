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

  // Initial load only - no auto polling
  useEffect(() => {
    fetchLive()
  }, [])

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between border-b border-[#1e2638] pb-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10b981] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10b981]"></span>
            </span>
            <h2 className="text-base font-semibold tracking-tight text-[#f0f4fc]">Live In-Play</h2>
          </div>
          <span className="text-[11px] font-mono text-[#8a99ad] bg-[#0e131b] border border-[#1e2638] px-2 py-0.5 rounded-full">
            {matches.length} In-Play
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono text-[#56657a] hidden sm:inline">
            Synced: {lastUpdated}
          </span>
          <button
            onClick={fetchLive}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#8a99ad] hover:text-[#f0f4fc] bg-[#0e131b] hover:bg-[#131924] border border-[#1e2638] rounded-lg transition-colors disabled:opacity-50 font-mono shadow-sm"
          >
            <svg
              className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#d4af37]' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.75"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>{loading ? 'Syncing' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {loading && matches.length === 0 ? (
        <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 text-center text-[#56657a] text-xs font-mono">
          Scanning live feeds...
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 text-center">
          <p className="text-xs font-semibold text-[#f0f4fc]">
            No live matches currently in play across allowlisted competitions.
          </p>
          <p className="text-[11px] text-[#8a99ad] mt-1 max-w-lg mx-auto font-normal">
            Live match tracking and in-play market signals activate automatically at kickoff.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matches.map((m) => (
            <div
              key={m.id}
              className="bg-[#0e131b] border border-[#1e2638] hover:border-[#2b374e] rounded-2xl p-5 shadow-sm transition-all"
            >
              <div className="flex items-center justify-between text-xs text-[#8a99ad] pb-2 border-b border-[#1e2638] font-mono">
                <span>{m.league.name}</span>
                <span className="font-semibold text-[#10b981]">
                  {m.minute}' ({m.status})
                </span>
              </div>
              <div className="grid grid-cols-5 items-center py-4 text-center">
                <div className="col-span-2 text-sm font-semibold text-[#f0f4fc] truncate">
                  {m.teams.home.name}
                </div>
                <div className="col-span-1 text-2xl font-mono font-bold text-[#d4af37]">
                  {m.score.home} - {m.score.away}
                </div>
                <div className="col-span-2 text-sm font-semibold text-[#f0f4fc] truncate">
                  {m.teams.away.name}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
