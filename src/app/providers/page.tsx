'use client'

import { useCallback, useEffect, useState } from 'react'

interface ProviderStatus {
  provider: string
  configured: boolean
  reachable: boolean | null
  note: string
  liveScoresRealtime?: boolean
  liveOddsSupported?: boolean | null
  prematchSupported?: boolean
  bookmakerConfirmed?: boolean
}

interface OddsQuota {
  remote_used: number | null
  remote_remaining: number | null
  last_request_cost: number | null
  last_request_at: string
}

interface MonthlyRequests {
  'football-data.org': number | null
  'the-odds-api': number | null
}

function readinessLabel(provider: ProviderStatus): string {
  if (!provider.configured) return 'Needs server key'
  if (provider.reachable === null) return 'Key set · connection not checked'
  return provider.reachable ? 'Connected' : 'Connection unavailable'
}

export default function Providers() {
  const [providers, setProviders] = useState<ProviderStatus[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [sharedCacheConfigured, setSharedCacheConfigured] = useState(false)
  const [oddsQuota, setOddsQuota] = useState<OddsQuota | null>(null)
  const [monthlyRequests, setMonthlyRequests] = useState<MonthlyRequests | null>(null)

  const loadStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/providers/status', { cache: 'no-store' })
      const body = await response.json()
      if (!response.ok) throw new Error(body?.error || 'Provider status unavailable')
      setProviders(Array.isArray(body?.providers) ? body.providers : [])
      setSharedCacheConfigured(Boolean(body?.sharedCacheConfigured))
      setOddsQuota(body?.oddsQuota || null)
      setMonthlyRequests(body?.monthlyRequests || null)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Provider status unavailable')
      setProviders(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void loadStatus() }, [loadStatus])

  return <div className="space-y-8">
    <section className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-[#1e2638] pb-6">
      <div>
        <div className="text-[11px] font-mono text-[#94A3B8]">SERVER-SIDE DATA SOURCES</div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc] mt-2">Data provider status</h1>
        <p className="text-sm text-[#8a99ad] mt-2 max-w-2xl">This page reports whether server keys are configured. A configured key does not prove that a fixture, live update, or bookmaker price is available.</p>
      </div>
      <button onClick={() => void loadStatus()} disabled={loading} className="px-4 py-2 rounded-xl bg-[#0e131b] border border-[#1e2638] text-xs font-mono disabled:opacity-50">
        {loading ? 'Refreshing…' : 'Refresh status'}
      </button>
    </section>

    {error && <section className="rounded-xl border border-amber-500/40 bg-[#0e131b] p-4 text-sm text-[#f0f4fc]">{error}</section>}

    {providers === null && !error ? <div className="rounded-xl border border-[#1e2638] bg-[#0e131b] p-8 text-sm text-[#8a99ad]">Loading provider status…</div> : null}

    {providers?.length === 0 && <div className="rounded-xl border border-[#1e2638] bg-[#0e131b] p-8 text-sm text-[#8a99ad]">No provider status is available.</div>}

    <section className="grid gap-4 md:grid-cols-2">
      {providers?.map(provider => <article key={provider.provider} className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-5 space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-[#f0f4fc]">{provider.provider}</h2>
            <p className="text-xs text-[#8a99ad] mt-1">{provider.note}</p>
          </div>
          <span className={`shrink-0 rounded-full border px-2 py-1 text-[10px] font-mono ${provider.configured ? 'border-emerald-500/30 text-emerald-300 bg-emerald-500/10' : 'border-amber-500/30 text-amber-300 bg-amber-500/10'}`}>
            {readinessLabel(provider)}
          </span>
        </div>
        <dl className="grid grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg bg-[#090c10] p-3"><dt className="text-[#64748B]">Key configured</dt><dd className="mt-1 text-[#f0f4fc]">{provider.configured ? 'Yes' : 'No'}</dd></div>
          <div className="rounded-lg bg-[#090c10] p-3"><dt className="text-[#64748B]">Connection checked</dt><dd className="mt-1 text-[#f0f4fc]">{provider.reachable === null ? 'No' : provider.reachable ? 'Yes' : 'Failed'}</dd></div>
        </dl>
        {provider.provider === 'football-data.org' && <p className="text-xs text-[#8a99ad]">Premier League fixtures are available on the free tier. Free scores can be delayed; this source cannot confirm a starting XI.</p>}
        {provider.provider === 'the-odds-api' && <p className="text-xs text-[#8a99ad]">The adapter requests the EU 1xBet key only. A quote is confirmed only after an actual match response contains that bookmaker and the requested market.</p>}
      </article>)}
    </section>

    <section className="rounded-xl border border-[#1e2638] bg-[#0e131b] p-5 space-y-3">
      <div>
        <h2 className="text-sm font-semibold text-[#f0f4fc]">Shared cache and monthly quota</h2>
        <p className="text-xs text-[#8a99ad] mt-1">Provider snapshots and request counts are shared across browsers. The counters update after an odds request; the app does not poll providers here.</p>
      </div>
      <div className="grid sm:grid-cols-2 xl:grid-cols-5 gap-3 text-xs">
        <div className="rounded-lg bg-[#090c10] p-3"><div className="text-[#64748B]">Shared cache</div><div className="mt-1 text-[#f0f4fc]">{sharedCacheConfigured ? 'Configured' : 'Server key required'}</div></div>
        <div className="rounded-lg bg-[#090c10] p-3"><div className="text-[#64748B]">Football Data requests this month</div><div className="mt-1 text-[#f0f4fc]">{monthlyRequests?.['football-data.org'] ?? 'Not recorded'}</div></div>
        <div className="rounded-lg bg-[#090c10] p-3"><div className="text-[#64748B]">Odds API requests this month</div><div className="mt-1 text-[#f0f4fc]">{monthlyRequests?.['the-odds-api'] ?? 'Not recorded'}</div></div>
        <div className="rounded-lg bg-[#090c10] p-3"><div className="text-[#64748B]">Odds credits used</div><div className="mt-1 text-[#f0f4fc]">{oddsQuota?.remote_used ?? 'Not recorded yet'}</div></div>
        <div className="rounded-lg bg-[#090c10] p-3"><div className="text-[#64748B]">Odds credits remaining</div><div className="mt-1 text-[#f0f4fc]">{oddsQuota?.remote_remaining ?? 'Not recorded yet'}</div></div>
        <div className="rounded-lg bg-[#090c10] p-3"><div className="text-[#64748B]">Last odds request cost</div><div className="mt-1 text-[#f0f4fc]">{oddsQuota?.last_request_cost ?? 'Not recorded yet'}</div></div>
      </div>
      {oddsQuota?.last_request_at && <p className="text-[10px] font-mono text-[#64748B]">Last quota update: {new Date(oddsQuota.last_request_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST</p>}
    </section>

    <section className="rounded-xl border border-[#1e2638] bg-[#0e131b] p-5">
      <h2 className="text-sm font-semibold text-[#f0f4fc]">What is not active yet</h2>
      <p className="text-xs text-[#8a99ad] mt-2">Match analysis, paper-bet decisions, settlement, and self-learning remain unavailable until their model and data gates are implemented. This page does not claim live betting or real-world bet placement.</p>
    </section>
  </div>
}
