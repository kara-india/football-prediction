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
      // Fallback local toggle
      setEngineEnabled(target)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#0d1618] border border-emerald-950/80 text-xs font-mono shadow-md">
        <span className="text-slate-400 font-medium">Engine:</span>
        <button
          onClick={toggleEngine}
          disabled={loading}
          className={`flex items-center gap-1.5 font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-lg text-[10px] transition ${
            engineEnabled
              ? 'bg-emerald-950 text-emerald-300 border border-emerald-600 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
              : 'bg-[#182326] text-slate-300 hover:text-white border border-slate-700/60'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${engineEnabled ? 'bg-emerald-400 animate-pulse' : 'bg-slate-400'}`}></span>
          {engineEnabled ? 'ACTIVE (ON)' : 'STANDBY (OFF)'}
        </button>
      </div>

      <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500/10 to-yellow-500/10 border border-amber-500/30 text-[11px] text-amber-300 font-mono shadow-sm">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
        <span>Target: <strong className="text-amber-200 font-bold">1xBet</strong></span>
      </div>
    </div>
  )
}
