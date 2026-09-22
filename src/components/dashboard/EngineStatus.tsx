'use client'

import React, { useEffect, useState } from 'react'

export default function EngineStatus() {
  const [engineEnabled, setEngineEnabled] = useState(false)
  const [loading, setLoading] = useState(false)

  const toggleEngine = async () => {
    setLoading(true)
    const target = !engineEnabled
    try {
      const endpoint = target ? '/api/engine/start' : '/api/engine/stop'
      const res = await fetch(endpoint, { method: 'POST' })
      if (res.ok) {
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
        className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-[11px] font-mono transition-colors disabled:opacity-50"
      >
        <span
          className={`w-1.5 h-1.5 rounded-full transition-colors ${
            engineEnabled ? 'bg-emerald-400' : 'bg-neutral-600'
          }`}
        ></span>
        <span className="text-neutral-400">
          Engine: <strong className={engineEnabled ? 'text-emerald-400' : 'text-neutral-300'}>
            {engineEnabled ? 'Active' : 'Standby'}
          </strong>
        </span>
      </button>
    </div>
  )
}
