'use client'

import { useEffect, useState } from 'react'

interface Prediction { id?: string; match?: string; market?: string; selection?: string; status?: string; [key: string]: unknown }

export default function Predictions() {
  const [data, setData] = useState<Prediction[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/predictions', { cache: 'no-store' })
      .then(async r => {
        const body = await r.json()
        if (!r.ok) throw new Error(body?.error || 'Prediction data unavailable')
        return body
      })
      .then(body => setData(Array.isArray(body) ? body : []))
      .catch(e => setError(e.message))
  }, [])

  const empty = !error && Array.isArray(data) && data.length === 0

  return <div className="space-y-8">
    <section className="border-b border-[#1e2638] pb-6">
      <div className="text-[11px] font-mono text-[#94A3B8]">PERSISTED PREDICTIONS</div>
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc] mt-2">Prediction Ledger</h1>
      <p className="text-sm text-[#8a99ad] mt-2">Only persisted, evidence-backed predictions are shown. No sample or paper bets are fabricated.</p>
    </section>
    <section className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-8 text-center">
      {error ? <><div className="text-[#f0f4fc] font-semibold">Prediction data unavailable</div><div className="text-xs text-[#8a99ad] mt-2">{error}</div></>
        : empty ? <><div className="text-[#f0f4fc] font-semibold">No persisted predictions yet</div><div className="text-xs text-[#8a99ad] mt-2">Predictions will appear here after the analysis pipeline produces a validated result.</div></>
        : <div className="text-xs text-[#8a99ad]">Loading persisted predictions…</div>}
    </section>
  </div>
}
