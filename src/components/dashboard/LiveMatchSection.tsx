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

  const fetchLive = async () => {
    try {
      const res = await fetch('/api/matches/live')
      if (res.ok) {
        const data = await res.json()
        setMatches(data)
      }
    } catch {
      // Keep state
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLive()
    const timer = setInterval(fetchLive, 30000) // Poll every 30s
    return () => clearInterval(timer)
  }, [])

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between border-b border-gray-800 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
          <h2 className="text-xl font-bold text-white tracking-wide">Live Matches</h2>
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-red-950 text-red-300 border border-red-800">
            {matches.length} In Play
          </span>
        </div>
        <span className="text-xs text-gray-500">Auto-refreshing every 30s</span>
      </div>

      {loading && matches.length === 0 ? (
        <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6 text-center text-gray-500 text-sm animate-pulse">
          Checking live match feeds...
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6 text-center">
          <p className="text-sm font-medium text-gray-400">No live matches currently in play across your allowlisted competitions.</p>
          <p className="text-xs text-gray-500 mt-1">Live coverage activates automatically at kickoff with real-time score-state hazard modeling.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matches.map((m) => (
            <div key={m.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-lg hover:border-gray-700 transition">
              <div className="flex items-center justify-between text-xs text-gray-400 pb-2 border-b border-gray-800">
                <span>{m.league.name}</span>
                <span className="font-bold text-red-400">{m.minute}' ({m.status})</span>
              </div>
              <div className="grid grid-cols-5 items-center py-4 text-center">
                <div className="col-span-2 text-sm font-bold text-white">{m.teams.home.name}</div>
                <div className="col-span-1 text-2xl font-mono font-extrabold text-white">
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
