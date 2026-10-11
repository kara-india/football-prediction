'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

interface Match {
  id: number
  kickoff: string
  venue?: string
  status: string
  statusLong?: string
  league: { id: number; code: string; name: string; country?: string }
  teams: { home: { name: string }; away: { name: string } }
  lineupConfirmed: boolean
  odds1xBet: null
  decision: string
}

interface SyncPayload { fixtures: Match[]; syncedAt: string; source: string; cached?: boolean }

const STORAGE_KEY = 'football-data-sync-v1'

export default function MatchdayCommandCenter() {
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [syncedAt, setSyncedAt] = useState<string | null>(null)
  const [sharedCache, setSharedCache] = useState(false)

  const syncFixtures = useCallback(async (onFinished?: () => void) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/matches/sync', { method: 'POST', cache: 'no-store' })
      const body = await response.json()
      if (!response.ok) throw new Error(body?.error || 'Fixture feed unavailable')
      const payload = body as SyncPayload
      const fixtures = Array.isArray(payload.fixtures) ? payload.fixtures : []
      setMatches(fixtures)
      setSyncedAt(payload.syncedAt)
      setSharedCache(true)
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Fixture feed unavailable')
    } finally {
      setLoading(false)
      onFinished?.()
    }
  }, [])

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const payload = JSON.parse(saved) as SyncPayload
        if (Array.isArray(payload.fixtures)) setMatches(payload.fixtures)
        if (payload.syncedAt) setSyncedAt(payload.syncedAt)
      }
    } catch {
      window.localStorage.removeItem(STORAGE_KEY)
    }
    void fetch('/api/matches/snapshot', { cache: 'no-store' }).then(async response => {
      if (!response.ok) return
      const payload = await response.json() as SyncPayload
      if (!Array.isArray(payload.fixtures) || !payload.syncedAt) return
      setMatches(payload.fixtures)
      setSyncedAt(payload.syncedAt)
      setSharedCache(true)
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    }).catch(() => undefined)
    const syncHandler = (event: Event) => {
      const onFinished = (event as CustomEvent<{ onFinished?: () => void }>).detail?.onFinished
      void syncFixtures(onFinished)
    }
    window.addEventListener('football-fixtures-sync', syncHandler)
    return () => window.removeEventListener('football-fixtures-sync', syncHandler)
  }, [syncFixtures])

  const live = matches.filter(match => ['LIVE', 'HT'].includes(match.status))
  const upcoming = matches.filter(match => !['LIVE', 'HT'].includes(match.status))

  return <div className="space-y-8">
    <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[#1E293B]">
      <div>
        <div className="text-[11px] font-mono text-[#94A3B8]">FIXTURE SOURCE · FOOTBALL-DATA.ORG</div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F8FAFC] mt-2">Match Intelligence Command Center</h1>
        <p className="text-sm text-[#94A3B8] max-w-3xl mt-2">Fixture data is requested only when you choose Sync Fixtures. Open a match terminal to check its available 1xBet prices.</p>
        {syncedAt && <p className="text-[11px] font-mono text-[#64748B] mt-2">Last sync: {new Date(syncedAt).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST · {sharedCache ? 'shared cache' : 'saved in this browser'}</p>}
      </div>
      <button onClick={() => void syncFixtures()} disabled={loading} className="px-3.5 py-2 rounded-xl bg-[#0F172A] border border-[#1E293B] text-xs font-mono text-[#F8FAFC] disabled:opacity-50">{loading ? 'Syncing fixtures…' : 'Sync Fixtures'}</button>
    </section>

    {error && <section className="rounded-xl border border-[#F59E0B]/40 bg-[#0F172A] p-5 text-sm">
      <div className="font-semibold text-[#F8FAFC]">Fixture sync unavailable</div>
      <div className="text-xs text-[#94A3B8] mt-2">{error}</div>
    </section>}

    {live.length > 0 && <section className="space-y-3">
      <h2 className="text-base font-semibold text-[#F8FAFC]">Matches in progress ({live.length})</h2>
      <div className="grid md:grid-cols-2 gap-3">{live.map(match => <Link key={match.id} href={`/matches/${match.id}`} className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-4">
        <div className="text-xs text-[#64748B]">{match.league.name} · LIVE</div><div className="font-semibold text-[#F8FAFC] mt-2">{match.teams.home.name} vs {match.teams.away.name}</div>
      </Link>)}</div>
    </section>}

    <section className="space-y-3">
      <div className="flex justify-between"><h2 className="text-base font-semibold text-[#F8FAFC]">Upcoming Fixtures</h2><span className="text-xs font-mono text-[#64748B]">{upcoming.length} synced</span></div>
      {matches.length === 0 ? <div className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-10 text-center">
        <div className="font-semibold text-[#F8FAFC]">{loading ? 'Syncing verified fixtures…' : 'No fixtures loaded'}</div>
        <div className="text-xs text-[#94A3B8] mt-2">Choose Sync Fixtures to request the latest Premier League schedule.</div>
      </div> : upcoming.length === 0 ? <div className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-10 text-center text-sm text-[#94A3B8]">No upcoming fixtures in the last sync.</div> : <div className="space-y-2">{upcoming.map(match => <div key={match.id} className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-4 flex items-center justify-between gap-4">
        <div><div className="text-xs text-[#64748B]">{match.league.name} · {new Date(match.kickoff).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST</div><div className="font-semibold text-[#F8FAFC] mt-1">{match.teams.home.name} vs {match.teams.away.name}</div><div className="text-[11px] text-[#94A3B8] mt-1">Starting lineups: not verified · Analysis: not available</div></div>
        <Link href={`/matches/${match.id}`} className="text-xs font-mono text-[#F8FAFC] hover:text-[#D4AF37]">Terminal →</Link>
      </div>)}</div>}
    </section>
  </div>
}
