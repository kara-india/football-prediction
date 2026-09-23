'use client'

import React, { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

export default function Header() {
  const pathname = usePathname()
  const [istTime, setIstTime] = useState<string>('')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setIstTime(
        now.toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true
        }) + ' IST'
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  const getPageTitle = () => {
    switch (pathname) {
      case '/':
        return { section: 'Intelligence', title: 'Match Intelligence Board' }
      case '/predictions':
        return { section: 'Audit Ledger', title: 'Paper Bet Performance Ledger' }
      case '/analytics':
        return { section: 'Analytics', title: 'Performance Analytics' }
      case '/models':
        return { section: 'Governance', title: 'Model Improvement & LIV Telemetry' }
      case '/providers':
        return { section: 'System', title: 'System Status & Quota Protection' }
      default:
        return { section: 'Intelligence', title: 'Match Analysis' }
    }
  }

  const { section, title } = getPageTitle()

  const handleManualSync = () => {
    setRefreshing(true)
    setTimeout(() => {
      setRefreshing(false)
      window.location.reload()
    }, 600)
  }

  return (
    <header className="sticky top-0 z-30 bg-[#090c10]/85 backdrop-blur-xl border-b border-[#1e2638] h-14">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Breadcrumb & Title */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-medium text-[#8a99ad] uppercase tracking-wider">
            {section}
          </span>
          <span className="text-[#56657a]">/</span>
          <h1 className="text-sm font-semibold text-[#f0f4fc] tracking-tight">{title}</h1>
        </div>

        {/* Right Telemetry & Actions */}
        <div className="flex items-center gap-3">
          {/* Live IST Clock */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0e131b] border border-[#1e2638] text-[11px] font-mono text-[#8a99ad]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
            <span>{istTime || 'Loading IST...'}</span>
          </div>

          {/* Quota Telemetry Badge */}
          <Link
            href="/providers"
            className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0e131b] hover:bg-[#131924] border border-[#1e2638] text-[11px] font-mono text-[#f0f4fc] transition-colors"
            title="Click to view API usage and provider status"
          >
            <span className="text-[#d4af37] font-semibold">1xBet</span>
            <span className="text-[#56657a]">·</span>
            <span className="text-[#10b981] font-medium">71 Left</span>
            <span className="text-[9px] px-1 py-0.2 rounded bg-[#10b981]/15 text-[#10b981] font-semibold">
              ₹0.00
            </span>
          </Link>

          {/* Manual Refresh Button */}
          <button
            onClick={handleManualSync}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0e131b] hover:bg-[#131924] border border-[#1e2638] text-[11px] font-mono text-[#8a99ad] hover:text-[#f0f4fc] transition-colors disabled:opacity-50"
            title="Reload match state without automated background polling"
          >
            <svg
              className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#d4af37]' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.75"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span className="hidden sm:inline">{refreshing ? 'Syncing...' : 'Sync'}</span>
          </button>
        </div>
      </div>
    </header>
  )
}
