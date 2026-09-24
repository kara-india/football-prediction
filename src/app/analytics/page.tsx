'use client'

import { useEffect, useState } from 'react'

export default function Analytics() {
  const [data, setData] = useState<unknown[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/predictions', { cache: 'no-store' })
      .then(async r => { const b = await r.json(); if (!r.ok) throw new Error(b?.error || 'Analytics data unavailable'); return b })
      .then(b => setData(Array.isArray(b) ? b : []))
      .catch(e => setError(e.message))
  }, [])

  return <div className="space-y-8">
    <section className="border-b border-[#1e2638] pb-6">
      <div className="text-[11px] font-mono text-[#94A3B8]">OBSERVED PERFORMANCE</div>
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc] mt-2">Performance Analytics</h1>
      <p className="text-sm text-[#8a99ad] mt-2">Metrics are displayed only when calculated from persisted prediction and settlement records.</p>
    </section>
    <section className="rounded-2xl border border-[#1e2638] bg-[#0e131b] p-8 text-center">
      {error ? <><div className="text-[#f0f4fc] font-semibold">Analytics unavailable</div><div className="text-xs text-[#8a99ad] mt-2">{error}</div></>
        : data?.length === 0 ? <><div className="text-[#f0f4fc] font-semibold">Insufficient persisted data</div><div className="text-xs text-[#8a99ad] mt-2">ROI, accuracy, Brier score and CLV will appear only after real predictions are settled.</div></>
        : <div className="text-xs text-[#8a99ad]">Loading observed performance…</div>}
    </section>
  </div>
}
