'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

interface Match { id: number; kickoff: string; status: string; statusLong?: string; league: { name: string; country?: string }; teams: { home: { name: string }; away: { name: string } }; score?: { home: number|null; away: number|null }; odds1xBet: null; decision: string }

export default function MatchPage() {
  const { id } = useParams<{ id: string }>()
  const [match, setMatch] = useState<Match | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`/api/matches/${id}`, { cache: 'no-store' })
      .then(async r => { const b = await r.json(); if (!r.ok) throw new Error(b?.error || 'Match unavailable'); return b })
      .then(setMatch)
      .catch(e => setError(e.message))
  }, [id])

  return <div className="space-y-6">
    <Link href="/" className="text-xs font-mono text-[#94A3B8] hover:text-[#F8FAFC]">← Back to fixtures</Link>
    {error ? <section className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-8 text-center">
      <div className="font-semibold text-[#F8FAFC]">Match data unavailable</div>
      <div className="text-xs text-[#8a99ad] mt-2">{error}</div>
    </section> : !match ? <div className="text-xs text-[#8a99ad]">Loading verified fixture data…</div> :
      <section className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-6 space-y-6">
        <div className="text-xs font-mono text-[#64748B]">{match.league.name}{match.league.country ? ` · ${match.league.country}` : ''}</div>
        <div className="text-2xl font-bold text-[#F8FAFC]">{match.teams.home.name} <span className="text-[#64748B]">vs</span> {match.teams.away.name}</div>
        <div className="text-sm font-mono text-[#D4AF37]">{new Date(match.kickoff).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST</div>
        <div className="text-sm text-[#94A3B8]">Status: {match.statusLong || match.status}</div>
        {match.score && (match.score.home !== null || match.score.away !== null) && <div className="text-xl font-mono text-[#F8FAFC]">{match.score.home ?? 0} – {match.score.away ?? 0}</div>}
        <div className="border-t border-[#1e2638] pt-4 text-xs font-mono text-[#F59E0B]">
          Decision: {match.decision}. 1xBet odds are not displayed because no verified bookmaker price is currently available.
        </div>
      </section>}
  </div>
}
