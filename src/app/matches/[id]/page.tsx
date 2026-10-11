'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

interface Match {
  id: number
  kickoff: string
  status: string
  statusLong?: string
  league: { code?: string; name: string; country?: string }
  teams: { home: { name: string }; away: { name: string } }
  score?: { home: number | null; away: number | null }
}

interface OddsResult {
  bookmaker?: string
  bookmakerKey?: string
  markets?: Array<{ market?: string; selection?: string; line?: number | null; decimalOdds?: number | null; sourceUpdatedAt?: string | null }>
  reason?: string | null
  error?: string
  creditsRemaining?: string | null
  creditsUsed?: string | null
  creditsLastRequest?: string | null
}

interface SyncPayload { fixtures: Match[] }
interface CachedOdds { cachedAt: number; result: OddsResult }

const FIXTURES_KEY = 'football-data-sync-v1'
const oddsKey = (id: string) => `odds-api-match-${id}-v1`
const inFlightOdds = new Map<string, Promise<OddsResult>>()

function readableReason(reason?: string | null) {
  switch (reason) {
    case 'ODDS_NOT_LISTED': return 'No matching event is listed by the odds provider.'
    case 'BOOKMAKER_UNAVAILABLE': return 'The requested 1xBet market is not available for this match.'
    case 'ODDS_API_NOT_CONFIGURED': return 'The Odds API key is not configured on the server.'
    case 'PROVIDER_CACHE_NOT_CONFIGURED': return 'Shared provider caching is not configured on the server, so prices are paused to protect API credits.'
    case 'ODDS_API_AUTH_FAILED': return 'The Odds API did not accept its configured key.'
    default: return 'Prices are currently unavailable for this match.'
  }
}

export default function MatchPage() {
  const { id } = useParams<{ id: string }>()
  const [match, setMatch] = useState<Match | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [odds, setOdds] = useState<OddsResult | null>(null)
  const [checkingOdds, setCheckingOdds] = useState(false)

  useEffect(() => {
    let cancelled = false
    let found = false
    try {
      const saved = window.localStorage.getItem(FIXTURES_KEY)
      const payload = saved ? JSON.parse(saved) as SyncPayload : null
      const selected = payload?.fixtures?.find(fixture => String(fixture.id) === id)
      if (selected) { found = true; setMatch(selected) }
    } catch (cause) {
      window.localStorage.removeItem(FIXTURES_KEY)
    }
    void fetch('/api/matches/snapshot', { cache: 'no-store' }).then(async response => {
      if (!response.ok) return
      const payload = await response.json() as SyncPayload
      const selected = payload.fixtures?.find(fixture => String(fixture.id) === id)
      if (selected && !cancelled) {
        found = true
        setMatch(selected)
        window.localStorage.setItem(FIXTURES_KEY, JSON.stringify(payload))
      }
    }).catch(() => undefined).finally(() => {
      if (!cancelled && !found) setError('This match is not in the shared fixture snapshot. Return to Match Intelligence and sync fixtures first.')
    })
    return () => { cancelled = true }
  }, [id])

  useEffect(() => {
    if (!match || match.league.code !== 'PL' || !(match.status === 'LIVE' || match.status === 'HT' || (match.status === 'NS' && Date.parse(match.kickoff) > Date.now()))) return
    let cancelled = false
    const cacheId = oddsKey(id)
    const maxAge = ['LIVE', 'HT'].includes(match.status) ? 60_000 : 5 * 60_000

    async function loadOdds() {
      try {
        const cached = window.localStorage.getItem(cacheId)
        if (cached) {
          const parsed = JSON.parse(cached) as CachedOdds
          if (Date.now() - parsed.cachedAt < maxAge) {
            if (!cancelled) setOdds(parsed.result)
            return
          }
        }
      } catch {
        window.localStorage.removeItem(cacheId)
      }

      setCheckingOdds(true)
      try {
        let request = inFlightOdds.get(cacheId)
        if (!request) {
          request = (async () => {
            const response = await fetch(`/api/matches/${id}/odds`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(match),
              cache: 'no-store',
            })
            const result = await response.json() as OddsResult
            if (!response.ok && !result.error) throw new Error('ODDS_REQUEST_FAILED')
            window.localStorage.setItem(cacheId, JSON.stringify({ cachedAt: Date.now(), result } satisfies CachedOdds))
            return result
          })()
          inFlightOdds.set(cacheId, request)
        }
        const result = await request
        if (!cancelled) setOdds(result)
      } catch {
        if (!cancelled) setOdds({ error: 'ODDS_API_UNREACHABLE' })
      } finally {
        inFlightOdds.delete(cacheId)
        if (!cancelled) setCheckingOdds(false)
      }
    }

    void loadOdds()
    return () => { cancelled = true }
  }, [id, match])

  const eligibleForOdds = Boolean(match && match.league.code === 'PL' && (match.status === 'LIVE' || match.status === 'HT' || (match.status === 'NS' && Date.parse(match.kickoff) > Date.now())))

  return <div className="space-y-6">
    <Link href="/" className="text-xs font-mono text-[#94A3B8] hover:text-[#F8FAFC]">← Back to fixtures</Link>
    {error ? <section className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-8 text-center">
      <div className="font-semibold text-[#F8FAFC]">Match data unavailable</div>
      <div className="text-xs text-[#8a99ad] mt-2">{error}</div>
    </section> : !match ? <div className="text-xs text-[#8a99ad]">Loading saved fixture…</div> :
      <section className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-6 space-y-6">
        <div className="text-xs font-mono text-[#64748B]">{match.league.name}{match.league.country ? ` · ${match.league.country}` : ''}</div>
        <div className="text-2xl font-bold text-[#F8FAFC]">{match.teams.home.name} <span className="text-[#64748B]">vs</span> {match.teams.away.name}</div>
        <div className="text-sm font-mono text-[#D4AF37]">{new Date(match.kickoff).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST</div>
        <div className="text-sm text-[#94A3B8]">Status: {match.statusLong || match.status}</div>
        {match.score && (match.score.home !== null || match.score.away !== null) && <div className="text-xl font-mono text-[#F8FAFC]">{match.score.home ?? 0} – {match.score.away ?? 0}</div>}

        <div className="border-t border-[#1e2638] pt-4 space-y-3">
          <h2 className="font-semibold text-[#F8FAFC]">1xBet prices</h2>
          {!eligibleForOdds ? <p className="text-xs text-[#94A3B8]">Prices are checked only for announced Premier League fixtures and live matches.</p>
            : checkingOdds ? <p className="text-xs text-[#D4AF37] animate-pulse">Checking this match’s available markets…</p>
              : odds?.markets?.length ? <>
                <div className="grid sm:grid-cols-2 gap-2">{odds.markets.map((market, index) => <div key={`${market.market}-${market.selection}-${index}`} className="rounded-lg border border-[#1e2638] p-3 flex justify-between gap-3 text-sm">
                  <span className="text-[#94A3B8]">{market.market === 'h2h' ? 'Match result' : market.market === 'totals' ? `Total goals ${market.line ?? ''}` : market.market} · {market.selection}</span>
                  <strong className="font-mono text-[#F8FAFC]">{market.decimalOdds?.toFixed(2) ?? '—'}</strong>
                </div>)}</div>
                <p className="text-[11px] text-[#64748B]">Source: {odds.bookmaker} · prices only; no model decision is available.</p>
              </> : <p className="text-xs text-[#94A3B8]">{readableReason(odds?.reason || odds?.error)}</p>}
          {odds?.creditsLastRequest && <p className="text-[10px] font-mono text-[#64748B]">Odds API usage: {odds.creditsLastRequest} credit(s) · {odds.creditsRemaining ?? 'remaining unknown'} remaining</p>}
        </div>

        <div className="border-t border-[#1e2638] pt-4 text-xs text-[#94A3B8]">
          Starting lineups are not verified, and calibrated model decisions are not available yet.
        </div>
      </section>}
  </div>
}
