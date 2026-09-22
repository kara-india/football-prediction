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
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800/80 border border-gray-700/80 text-xs">
        <span className="text-gray-400 font-medium">Background Engine:</span>
        <button
          onClick={toggleEngine}
          disabled={loading}
          className={`flex items-center gap-1.5 font-bold uppercase tracking-wider px-2 py-0.5 rounded text-[10px] transition ${
            engineEnabled
              ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${engineEnabled ? 'bg-emerald-400 animate-pulse' : 'bg-gray-400'}`}></span>
          {engineEnabled ? 'ACTIVE (ON)' : 'STANDBY (OFF)'}
        </button>
      </div>

      <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-orange-950/40 border border-orange-800/60 text-[11px] text-orange-300">
        <span className="w-1.5 h-1.5 rounded-full bg-orange-400"></span>
        <span>Target: <strong>1xBet</strong></span>
      </div>
    </div>
  )
}
