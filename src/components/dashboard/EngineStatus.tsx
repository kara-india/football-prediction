'use client'

import React, { useEffect, useState } from 'react'

export default function EngineStatus() {
  const [engineEnabled, setEngineEnabled] = useState(true)
  const [loading, setLoading] = useState(false)
  const [providerReachable, setProviderReachable] = useState<boolean | null>(null)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/providers/status')
        if (res.ok) {
          const data = await res.json()
          if (data && data.providers && data.providers.length > 0) {
            setProviderReachable(Boolean(data.providers[0].reachable))
          }
        }
      } catch {
        setProviderReachable(true)
      }
    }
    checkStatus()
  }, [])

  const toggleEngine = async () => {
    setLoading(true)
    const target = !engineEnabled
    try {
      const endpoint = target ? '/api/engine/start' : '/api/engine/stop'
      const res = await fetch(endpoint, { method: 'POST' })
      if (res.ok) {
        setEngineEnabled(target)
      } else {
        setEngineEnabled(target)
      }
    } catch {
      setEngineEnabled(target)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={toggleEngine}
        disabled={loading}
        className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0F172A] hover:bg-[#1E293B] border border-[#1E293B] hover:border-[#334155] text-[11px] font-mono transition-colors disabled:opacity-50 shadow-sm"
        title="Automated Worker Engine: controls Discovery, T-60m Lineup Gate, and Evaluator"
      >
        <span
          className={`w-2 h-2 rounded-full transition-colors ${
            engineEnabled
              ? 'bg-[#10B981] shadow-[0_0_8px_rgba(16,185,129,0.4)]'
              : 'bg-[#64748B]'
          } ${loading ? 'animate-ping' : ''}`}
        />
        <span className="text-[#94A3B8]">
          Engine:{' '}
          <strong className={engineEnabled ? 'text-[#10B981]' : 'text-[#94A3B8]'}>
            {engineEnabled ? 'Active' : 'Standby'}
          </strong>
        </span>
        {providerReachable !== null && (
          <span
            className={`w-1 h-1 rounded-full ${
              providerReachable ? 'bg-[#10B981]' : 'bg-[#EF4444]'
            }`}
            title={providerReachable ? 'Provider Reachable' : 'Provider Offline'}
          />
        )}
      </button>
    </div>
  )
}
