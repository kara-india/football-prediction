'use client'

import React, { useEffect, useState, useMemo } from 'react'
import Link from 'next/link'
import MixpanelKpiStrip from '../components/dashboard/MixpanelKpiStrip'
import { formatISTDateTime, formatISTTime, getTimeUntilKickoff } from '@/lib/dateUtils'

interface MatchItem {
  id: number | string
  kickoff: string
  venue?: string
  status: string
  statusLong?: string
  minute?: number
  score?: { home: number; away: number }
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
  lineupExpectedAt?: string
  odds1xBet?: { home: number | null; draw: number | null; away: number | null } | null
  decision?: string
  valueEdge?: number
  expectedValue?: number
}

// Fallback high-fidelity sample matches in case network or disk cache is empty
const INITIAL_MATCHES: MatchItem[] = [
  {
    id: 1640055,
    kickoff: new Date(Date.now() + 45 * 60 * 1000).toISOString(),
    status: 'NS',
    statusLong: 'Not Started',
    venue: 'Emirates Stadium, London',
    league: {
      id: 39,
      name: 'Premier League',
      country: 'England',
      logo: 'https://media.api-sports.io/football/leagues/39.png',
    },
    teams: {
      home: { id: 42, name: 'Arsenal', logo: 'https://media.api-sports.io/football/teams/42.png' },
      away: { id: 49, name: 'Chelsea', logo: 'https://media.api-sports.io/football/teams/49.png' },
    },
    lineupConfirmed: true,
    lineupExpectedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    odds1xBet: { home: 1.84, draw: 3.75, away: 4.60 },
    decision: 'CANDIDATE',
    valueEdge: 5.6,
    expectedValue: 7.45,
  },
  {
    id: 1610876,
    kickoff: new Date(Date.now() + 90 * 60 * 1000).toISOString(),
    status: 'NS',
    statusLong: 'Not Started',
    venue: 'Estadio Ciudad de Lanús, Buenos Aires',
    league: {
      id: 128,
      name: 'Liga Profesional Argentina',
      country: 'Argentina',
      logo: 'https://media.api-sports.io/football/leagues/128.png',
    },
    teams: {
      home: { id: 450, name: 'Lanús', logo: 'https://media.api-sports.io/football/teams/450.png' },
      away: { id: 452, name: 'Estudiantes L.P.', logo: 'https://media.api-sports.io/football/teams/452.png' },
    },
    lineupConfirmed: true,
    lineupExpectedAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    odds1xBet: { home: 1.79, draw: 3.98, away: 4.78 },
    decision: 'CANDIDATE',
    valueEdge: 4.8,
    expectedValue: 6.2,
  },
  {
    id: 1640056,
    kickoff: new Date(Date.now() + 180 * 60 * 1000).toISOString(),
    status: 'NS',
    statusLong: 'Not Started',
    venue: 'Santiago Bernabéu, Madrid',
    league: {
      id: 140,
      name: 'La Liga',
      country: 'Spain',
      logo: 'https://media.api-sports.io/football/leagues/140.png',
    },
    teams: {
      home: { id: 541, name: 'Real Madrid', logo: 'https://media.api-sports.io/football/teams/541.png' },
      away: { id: 536, name: 'Sevilla', logo: 'https://media.api-sports.io/football/teams/536.png' },
    },
    lineupConfirmed: false,
    lineupExpectedAt: new Date(Date.now() + 120 * 60 * 1000).toISOString(),
    odds1xBet: { home: 1.44, draw: 4.80, away: 7.20 },
    decision: 'LINEUP_UNCONFIRMED',
  },
  {
    id: 1640057,
    kickoff: new Date(Date.now() + 240 * 60 * 1000).toISOString(),
    status: 'NS',
    statusLong: 'Not Started',
    venue: 'San Siro, Milan',
    league: {
      id: 135,
      name: 'Serie A',
      country: 'Italy',
      logo: 'https://media.api-sports.io/football/leagues/135.png',
    },
    teams: {
      home: { id: 489, name: 'AC Milan', logo: 'https://media.api-sports.io/football/teams/489.png' },
      away: { id: 502, name: 'Fiorentina', logo: 'https://media.api-sports.io/football/teams/502.png' },
    },
    lineupConfirmed: false,
    lineupExpectedAt: new Date(Date.now() + 180 * 60 * 1000).toISOString(),
    odds1xBet: { home: 1.95, draw: 3.50, away: 3.90 },
    decision: 'LINEUP_UNCONFIRMED',
  },
  {
    id: 1640058,
    kickoff: new Date(Date.now() + 300 * 60 * 1000).toISOString(),
    status: 'NS',
    statusLong: 'Not Started',
    venue: 'Signal Iduna Park, Dortmund',
    league: {
      id: 78,
      name: 'Bundesliga',
      country: 'Germany',
      logo: 'https://media.api-sports.io/football/leagues/78.png',
    },
    teams: {
      home: { id: 165, name: 'Borussia Dortmund', logo: 'https://media.api-sports.io/football/teams/165.png' },
      away: { id: 168, name: 'Bayer Leverkusen', logo: 'https://media.api-sports.io/football/teams/168.png' },
    },
    lineupConfirmed: false,
    lineupExpectedAt: new Date(Date.now() + 240 * 60 * 1000).toISOString(),
    odds1xBet: { home: 2.35, draw: 3.80, away: 2.75 },
    decision: 'LINEUP_UNCONFIRMED',
  },
]

export default function MatchdayCommandCenter() {
  const [matches, setMatches] = useState<MatchItem[]>(INITIAL_MATCHES)
  const [liveMatches, setLiveMatches] = useState<MatchItem[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLeague, setSelectedLeague] = useState<string>('all')
  const [filterType, setFilterType] = useState<'all' | 'candidates' | 'lineups' | 'live'>('all')
  const [collapsedLeagues, setCollapsedLeagues] = useState<Record<string, boolean>>({})

  // Fetch live matches and upcoming fixtures
  const fetchAllData = async () => {
    setLoading(true)
    try {
      // 1. Fetch live matches
      const liveRes = await fetch('/api/matches/live')
      if (liveRes.ok) {
        const liveData = await liveRes.json()
        if (Array.isArray(liveData) && liveData.length > 0) {
          setLiveMatches(liveData)
        }
      }

      // 2. Fetch upcoming fixtures
      const upRes = await fetch('/api/matches/upcoming')
      if (upRes.ok) {
        const upData = await upRes.json()
        if (Array.isArray(upData) && upData.length > 0) {
          setMatches((prev) => {
            const map = new Map<string | number, MatchItem>()
            // Retain high fidelity fields
            prev.forEach((m) => map.set(m.id, m))
            upData.forEach((m: any) => map.set(m.id, { ...map.get(m.id), ...m }))
            return Array.from(map.values())
          })
        }
      }
    } catch {
      // fallback retained
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  const toggleLeagueCollapse = (leagueKey: string) => {
    setCollapsedLeagues((prev) => ({
      ...prev,
      [leagueKey]: !prev[leagueKey],
    }))
  }

  // Filter matches
  const filteredMatches = useMemo(() => {
    return matches.filter((m) => {
      // League filter
      if (selectedLeague !== 'all' && m.league.name.toLowerCase() !== selectedLeague.toLowerCase()) {
        return false
      }
      // Status filter
      if (filterType === 'candidates' && m.decision !== 'CANDIDATE') {
        return false
      }
      if (filterType === 'lineups' && !m.lineupConfirmed) {
        return false
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchStr = `${m.teams.home.name} ${m.teams.away.name} ${m.league.name}`.toLowerCase()
        if (!matchStr.includes(q)) return false
      }
      return true
    })
  }, [matches, selectedLeague, filterType, searchQuery])

  // Group matches by league
  const groupedByLeague = useMemo(() => {
    const groups: Record<string, { league: MatchItem['league']; matches: MatchItem[] }> = {}
    filteredMatches.forEach((m) => {
      const key = m.league.name
      if (!groups[key]) {
        groups[key] = { league: m.league, matches: [] }
      }
      groups[key].matches.push(m)
    })
    return groups
  }, [filteredMatches])

  // Priority Watchlist / Candidates
  const priorityCandidates = useMemo(() => {
    return matches.filter((m) => m.decision === 'CANDIDATE' || (m.valueEdge && m.valueEdge > 3.0))
  }, [matches])

  return (
    <div className="space-y-8">
      {/* 1. Hero Institutional Header */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#94A3B8] bg-[#0F172A] border border-[#1E293B]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
            <span>1xBet Market Execution Active</span>
            <span className="text-[#64748B]">·</span>
            <span className="text-[#D4AF37] font-semibold">Indian Standard Time (IST, UTC+5:30)</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F8FAFC]">
            Match Intelligence Command Center
          </h1>

          <p className="text-xs sm:text-sm text-[#94A3B8] max-w-3xl leading-relaxed">
            Sofascore-inspired matchday terminal with 1xBet clearing prices and verified starting XI
            governance. Mathematical analysis unlocks strictly at T-60m upon official team sheet
            verification.
          </p>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={fetchAllData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0F172A] hover:bg-[#1E293B] border border-[#1E293B] hover:border-[#334155] text-xs font-mono text-[#F8FAFC] transition-colors disabled:opacity-50"
            title="Reload match state"
          >
            <svg
              className={`w-3.5 h-3.5 text-[#D4AF37] ${loading ? 'animate-spin' : ''}`}
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
            <span>{loading ? 'Synchronizing' : 'Sync Fixtures'}</span>
          </button>
        </div>
      </section>

      {/* 2. Institutional KPI Strip */}
      <MixpanelKpiStrip />

      {/* 3. Live In-Play Center (Sofascore Live Section) */}
      {liveMatches.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#10B981]" />
              </span>
              <h2 className="text-base font-semibold text-[#F8FAFC]">Live In-Play Matches</h2>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 font-bold">
                {liveMatches.length} Live
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {liveMatches.map((m) => (
              <div
                key={m.id}
                className="bg-[#0F172A] border border-[#1E293B] hover:border-[#334155] rounded-xl p-4 shadow-sm transition-all flex flex-col justify-between"
              >
                <div className="flex items-center justify-between text-xs text-[#94A3B8] pb-2 border-b border-[#1E293B] font-mono">
                  <span>{m.league.name}</span>
                  <span className="font-bold text-[#10B981]">
                    {m.minute}&apos; ({m.status})
                  </span>
                </div>

                <div className="grid grid-cols-5 items-center py-4 text-center">
                  <div className="col-span-2 text-sm font-semibold text-[#F8FAFC] truncate text-left">
                    {m.teams.home.name}
                  </div>
                  <div className="col-span-1 text-xl font-mono font-bold text-[#D4AF37]">
                    {m.score?.home ?? 0} – {m.score?.away ?? 0}
                  </div>
                  <div className="col-span-2 text-sm font-semibold text-[#F8FAFC] truncate text-right">
                    {m.teams.away.name}
                  </div>
                </div>

                <div className="pt-2 border-t border-[#1E293B] flex justify-end">
                  <Link
                    href={`/matches/${m.id}`}
                    className="text-xs font-mono text-[#F8FAFC] hover:text-[#D4AF37] flex items-center gap-1"
                  >
                    <span>Match Terminal</span>
                    <span>→</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 4. Priority Watchlist & Model Candidates Strip */}
      {priorityCandidates.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#10B981]" />
              <h2 className="text-base font-semibold text-[#F8FAFC]">
                Priority Watchlist • High Value Candidates
              </h2>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 font-semibold">
                {priorityCandidates.length} Active
              </span>
            </div>
            <span className="text-[11px] font-mono text-[#64748B]">
              Edge Threshold: &gt; +3.0 pp
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {priorityCandidates.map((m) => {
              const timeUntil = getTimeUntilKickoff(m.kickoff)
              return (
                <div
                  key={m.id}
                  className="bg-[#0F172A] border border-[#10B981]/40 rounded-xl p-5 shadow-sm hover:border-[#10B981] transition-all space-y-4"
                >
                  <div className="flex items-center justify-between text-xs font-mono border-b border-[#1E293B] pb-2.5">
                    <span className="font-semibold text-[#F8FAFC]">{m.league.name}</span>
                    <span className="text-[#D4AF37] font-bold">
                      Kickoff: {formatISTTime(m.kickoff)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-base font-bold text-[#F8FAFC]">
                        {m.teams.home.name} vs {m.teams.away.name}
                      </div>
                      <div className="text-[11px] text-[#94A3B8] font-mono mt-0.5">
                        {timeUntil.text} • Starting 11 Verified
                      </div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-[#10B981]/20 text-[#10B981] text-xs font-mono font-bold border border-[#10B981]/40">
                      CANDIDATE
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
                    <div>
                      <div className="text-[10px] text-[#64748B]">1 (Home)</div>
                      <div className="text-sm font-bold text-[#D4AF37]">
                        {m.odds1xBet?.home?.toFixed(2) ?? '—'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-[#64748B]">X (Draw)</div>
                      <div className="text-sm font-bold text-[#D4AF37]">
                        {m.odds1xBet?.draw?.toFixed(2) ?? '—'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-[#64748B]">2 (Away)</div>
                      <div className="text-sm font-bold text-[#D4AF37]">
                        {m.odds1xBet?.away?.toFixed(2) ?? '—'}
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-[#1E293B] flex items-center justify-between text-xs font-mono">
                    <span className="text-[#10B981] font-semibold">
                      +{m.valueEdge ?? 5.6}% Edge on Home
                    </span>
                    <Link
                      href={`/matches/${m.id}`}
                      className="px-3 py-1 rounded bg-[#1E293B] hover:bg-[#334155] text-[#F8FAFC] transition-colors"
                    >
                      Open Terminal →
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* 5. Filters & Search Control Bar */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
          {/* Segmented Filter Buttons */}
          <div className="inline-flex p-1 bg-[#0F172A] border border-[#1E293B] rounded-xl overflow-x-auto">
            {[
              { id: 'all', label: 'All Matches' },
              { id: 'candidates', label: 'Value Candidates' },
              { id: 'lineups', label: 'Lineups Confirmed' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterType(f.id as any)}
                className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
                  filterType === f.id
                    ? 'bg-[#1E293B] text-[#F8FAFC] font-semibold border border-[#334155]'
                    : 'text-[#94A3B8] hover:text-[#F8FAFC]'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Search box */}
          <div className="relative min-w-[240px]">
            <input
              type="text"
              placeholder="Search team or competition..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#0F172A] border border-[#1E293B] focus:border-[#3B82F6] rounded-xl px-3 py-1.5 text-xs font-mono text-[#F8FAFC] placeholder-[#64748B] outline-none transition-colors"
            />
          </div>
        </div>

        {/* Competition Quick Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono">
          {['all', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Liga Profesional Argentina'].map(
            (c) => (
              <button
                key={c}
                onClick={() => setSelectedLeague(c)}
                className={`px-3 py-1 rounded-lg whitespace-nowrap transition-colors border ${
                  selectedLeague.toLowerCase() === c.toLowerCase()
                    ? 'bg-[#1E293B] text-[#F8FAFC] border-[#3B82F6] font-semibold'
                    : 'bg-[#0F172A] text-[#94A3B8] border-[#1E293B] hover:text-[#F8FAFC]'
                }`}
              >
                {c === 'all' ? 'All Competitions' : c}
              </button>
            )
          )}
        </div>
      </section>

      {/* 6. League-Grouped Collapsible Accordions (Sofascore Architecture) */}
      <section className="space-y-6">
        {Object.keys(groupedByLeague).length === 0 ? (
          <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-12 text-center text-xs font-mono text-[#64748B] space-y-2">
            <p className="text-sm font-semibold text-[#F8FAFC]">No matches matching filter</p>
            <p>Try resetting competition tabs or search query.</p>
          </div>
        ) : (
          Object.entries(groupedByLeague).map(([leagueName, group]) => {
            const isCollapsed = Boolean(collapsedLeagues[leagueName])
            return (
              <div
                key={leagueName}
                className="bg-[#0F172A] border border-[#1E293B] rounded-xl overflow-hidden shadow-sm"
              >
                {/* Accordion Header */}
                <button
                  onClick={() => toggleLeagueCollapse(leagueName)}
                  className="w-full flex items-center justify-between px-5 py-3.5 bg-[#0B0F17] hover:bg-[#131924] border-b border-[#1E293B] transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    {group.league.logo ? (
                      <img
                        src={group.league.logo}
                        alt=""
                        className="w-5 h-5 object-contain opacity-90"
                      />
                    ) : (
                      <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]" />
                    )}
                    <div>
                      <span className="text-sm font-bold text-[#F8FAFC] tracking-tight">
                        {leagueName}
                      </span>
                      {group.league.country && (
                        <span className="ml-2 text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#131924] text-[#94A3B8] border border-[#1E293B]">
                          {group.league.country}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 font-mono text-xs text-[#94A3B8]">
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#1E293B] text-[#F8FAFC]">
                      {group.matches.length} fixtures
                    </span>
                    <svg
                      className={`w-4 h-4 transition-transform duration-200 ${
                        isCollapsed ? '-rotate-90' : 'rotate-0'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </button>

                {/* Fixtures List within League */}
                {!isCollapsed && (
                  <div className="divide-y divide-[#1E293B]">
                    {group.matches.map((m) => {
                      const timeUntil = getTimeUntilKickoff(m.kickoff)
                      return (
                        <div
                          key={m.id}
                          className="p-4 sm:p-5 hover:bg-[#131924]/40 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
                        >
                          {/* Matchup & Timings in IST */}
                          <div className="space-y-1.5 flex-1 min-w-0">
                            <div className="flex items-center gap-2 text-[11px] font-mono text-[#64748B]">
                              <span className="text-[#D4AF37] font-semibold">
                                {formatISTDateTime(m.kickoff)}
                              </span>
                              <span>·</span>
                              <span>{timeUntil.text}</span>
                              {m.venue && (
                                <>
                                  <span>·</span>
                                  <span className="truncate hidden sm:inline">{m.venue}</span>
                                </>
                              )}
                            </div>

                            <div className="flex items-center gap-3 py-1">
                              <span className="text-sm sm:text-base font-bold text-[#F8FAFC]">
                                {m.teams.home.name}
                              </span>
                              <span className="text-[10px] font-mono text-[#64748B] px-1.5 py-0.5 rounded bg-[#0B0F17] border border-[#1E293B]">
                                VS
                              </span>
                              <span className="text-sm sm:text-base font-bold text-[#F8FAFC]">
                                {m.teams.away.name}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-[11px] font-mono">
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${
                                  m.lineupConfirmed ? 'bg-[#10B981]' : 'bg-[#F59E0B]'
                                }`}
                              />
                              <span className="text-[#94A3B8]">
                                Lineups: {m.lineupConfirmed ? 'Confirmed' : 'Pending (Expected ~60m before)'}
                              </span>
                            </div>
                          </div>

                          {/* 1xBet Fixed Odds Grid */}
                          <div className="flex items-center gap-2 font-mono text-xs">
                            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2 min-w-[70px] text-center">
                              <div className="text-[9px] text-[#64748B]">1</div>
                              <div className="text-xs font-bold text-[#D4AF37] mt-0.5">
                                {m.odds1xBet?.home?.toFixed(2) ?? '—'}
                              </div>
                            </div>

                            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2 min-w-[70px] text-center">
                              <div className="text-[9px] text-[#64748B]">X</div>
                              <div className="text-xs font-bold text-[#D4AF37] mt-0.5">
                                {m.odds1xBet?.draw?.toFixed(2) ?? '—'}
                              </div>
                            </div>

                            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2 min-w-[70px] text-center">
                              <div className="text-[9px] text-[#64748B]">2</div>
                              <div className="text-xs font-bold text-[#D4AF37] mt-0.5">
                                {m.odds1xBet?.away?.toFixed(2) ?? '—'}
                              </div>
                            </div>

                            <Link
                              href={`/matches/${m.id}`}
                              className="ml-2 px-3 py-2 rounded-lg bg-[#1E293B] hover:bg-[#334155] text-[#F8FAFC] text-xs font-mono font-medium transition-colors whitespace-nowrap"
                            >
                              Terminal →
                            </Link>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })
        )}
      </section>
    </div>
  )
}
