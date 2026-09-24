'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface Match {
  id: number
  kickoff: string
  venue?: string
  league: { name: string; country?: string }
  teams: { home: { name: string }; away: { name: string } }
  lineupConfirmed: boolean
  odds1xBet: null
  decision: string
}

export default function MatchdayCommandCenter() {
  const [matches, setMatches] = useState<Match[]>([])
  const [live, setLive] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const [up, lv] = await Promise.all([
        fetch('/api/matches/upcoming', { cache: 'no-store' }),
        fetch('/api/matches/live', { cache: 'no-store' }),
      ])
      const ub = await up.json()
      const lb = await lv.json()
      if (!up.ok) throw new Error(ub?.error || 'Upcoming fixture feed unavailable')
      setMatches(Array.isArray(ub) ? ub : [])
      setLive(Array.isArray(lb) ? lb : [])
    } catch (e: any) {
      setError(e?.message || 'Fixture feed unavailable')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  return <div className="space-y-8">
    <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[#1E293B]">
      <div>
        <div className="text-[11px] font-mono text-[#94A3B8]">LIVE DATA MODE · API-FOOTBALL</div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F8FAFC] mt-2">Match Intelligence Command Center</h1>
        <p className="text-sm text-[#94A3B8] max-w-3xl mt-2">Only verified upstream fixture data is displayed. Bookmaker odds and model decisions remain unavailable until independently verified.</p>
      </div>
      <button onClick={load} disabled={loading} className="px-3.5 py-2 rounded-xl bg-[#0F172A] border border-[#1E293B] text-xs font-mono text-[#F8FAFC] disabled:opacity-50">{loading ? 'Synchronizing…' : 'Sync Fixtures'}</button>
    </section>

    {error && <section className="rounded-xl border border-[#F59E0B]/40 bg-[#0F172A] p-5 text-sm">
      <div className="font-semibold text-[#F8FAFC]">Fixture feed unavailable</div>
      <div className="text-xs text-[#94A3B8] mt-2">{error}</div>
    </section>}

    {live.length > 0 && <section className="space-y-3">
      <h2 className="text-base font-semibold text-[#F8FAFC]">Live Matches ({live.length})</h2>
      <div className="grid md:grid-cols-2 gap-3">{live.map(m => <Link key={m.id} href={`/matches/${m.id}`} className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-4">
        <div className="text-xs text-[#64748B]">{m.league.name}</div><div className="font-semibold text-[#F8FAFC] mt-2">{m.teams.home.name} vs {m.teams.away.name}</div>
      </Link>)}</div>
    </section>}

    <section className="space-y-3">
      <div className="flex justify-between"><h2 className="text-base font-semibold text-[#F8FAFC]">Upcoming Fixtures</h2><span className="text-xs font-mono text-[#64748B]">{matches.length} verified</span></div>
      {matches.length === 0 && !loading ? <div className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-10 text-center">
        <div className="font-semibold text-[#F8FAFC]">No verified upcoming fixtures</div>
        <div className="text-xs text-[#94A3B8] mt-2">This is a real empty state. No sample fixtures or synthetic matches are inserted.</div>
      </div> : <div className="space-y-2">{matches.map(m => <div key={m.id} className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-4 flex items-center justify-between gap-4">
        <div><div className="text-xs text-[#64748B]">{m.league.name} · {new Date(m.kickoff).toLocaleString('en-IN', {timeZone:'Asia/Kolkata'})} IST</div><div className="font-semibold text-[#F8FAFC] mt-1">{m.teams.home.name} vs {m.teams.away.name}</div><div className="text-[11px] text-[#94A3B8] mt-1">Lineup: {m.lineupConfirmed ? 'confirmed' : 'pending'} · Decision: {m.decision}</div></div>
        <Link href={`/matches/${m.id}`} className="text-xs font-mono text-[#F8FAFC] hover:text-[#D4AF37]">Terminal →</Link>
      </div>)}</div>}
    </section>
  </div>
}
