'use client'

import React, { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

export default function Header() {
  const pathname = usePathname()
  const [istTime, setIstTime] = useState<string>('')
  const [refreshing, setRefreshing] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setIstTime(
        now.toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
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
        return { section: 'TERMINAL', title: 'Matchday Command Center' }
      case '/predictions':
        return { section: 'AUDIT', title: 'Paper Bet Ledger' }
      case '/analytics':
        return { section: 'ANALYTICS', title: 'Performance Analytics' }
      case '/models':
        return { section: 'RESEARCH', title: 'Models & LIV Telemetry' }
      case '/providers':
        return { section: 'SYSTEM', title: 'Quota Governance & Data Feeds' }
      default:
        return { section: 'TERMINAL', title: 'Match Detail' }
    }
  }

  const { section, title } = getPageTitle()

  const handleManualSync = () => {
    setRefreshing(true)
    setTimeout(() => {
      setRefreshing(false)
      window.location.reload()
    }, 500)
  }

  return (
    <>
      <header className="sticky top-0 z-30 bg-[#0B0F17]/90 backdrop-blur-xl border-b border-[#1E293B] h-14">
        <div className="h-full px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          {/* Left Breadcrumb & Mobile Menu Toggle */}
          <div className="flex items-center gap-3">
            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 rounded-lg text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B] transition-colors"
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            {/* Breadcrumb */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold text-[#D4AF37] uppercase tracking-widest px-2 py-0.5 rounded bg-[#D4AF37]/10 border border-[#D4AF37]/20">
                {section}
              </span>
              <span className="text-[#334155]">/</span>
              <h1 className="text-xs sm:text-sm font-bold text-[#F8FAFC] tracking-tight truncate max-w-[200px] sm:max-w-none">
                {title}
              </h1>
            </div>
          </div>

          {/* Right Telemetry & Actions */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Live IST Clock */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0F172A] border border-[#1E293B] text-[11px] font-mono text-[#94A3B8]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block animate-pulse" />
              <span>{istTime || 'Loading IST...'}</span>
            </div>

            {/* Quota Telemetry Badge */}
            <Link
              href="/providers"
              className="flex items-center gap-2 px-2.5 sm:px-3 py-1 rounded-lg bg-[#0F172A] hover:bg-[#1E293B] border border-[#1E293B] text-[11px] font-mono text-[#F8FAFC] transition-colors"
              title="API-Football Quota Governance: Max 95 calls/day"
            >
              <span className="text-[#D4AF37] font-semibold">1xBet</span>
              <span className="text-[#334155]">·</span>
              <span className="text-[#10B981] font-semibold">95 Cap</span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#10B981]/15 text-[#10B981] font-bold border border-[#10B981]/30 hidden sm:inline">
                ₹0.00 Cost
              </span>
            </Link>

            {/* Manual Sync Button */}
            <button
              onClick={handleManualSync}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-lg bg-[#0F172A] hover:bg-[#1E293B] border border-[#1E293B] text-[11px] font-mono text-[#94A3B8] hover:text-[#F8FAFC] transition-colors disabled:opacity-50"
              title="Refresh state"
            >
              <svg
                className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#D4AF37]' : 'text-[#94A3B8]'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span className="hidden md:inline">{refreshing ? 'Syncing...' : 'Sync'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="fixed top-0 left-0 bottom-0 w-64 bg-[#0B0F17] border-r border-[#1E293B] p-4 flex flex-col justify-between"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#D4AF37] to-[#8A7220] flex items-center justify-center text-black font-extrabold text-xs font-mono">
                    1X
                  </div>
                  <span className="text-xs font-bold text-[#F8FAFC]">Football Terminal</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-lg text-[#64748B] hover:text-[#F8FAFC]"
                >
                  ✕
                </button>
              </div>

              <nav className="space-y-1">
                {[
                  { name: 'Match Intelligence', href: '/' },
                  { name: 'Paper Bet Ledger', href: '/predictions' },
                  { name: 'Performance Analytics', href: '/analytics' },
                  { name: 'Models & LIV Telemetry', href: '/models' },
                  { name: 'System & Quota Protection', href: '/providers' },
                ].map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`block px-3 py-2 rounded-lg text-xs font-mono ${
                      pathname === item.href
                        ? 'bg-[#1E293B] text-[#D4AF37] font-semibold border border-[#334155]'
                        : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#0F172A]'
                    }`}
                  >
                    {item.name}
                  </Link>
                ))}
              </nav>
            </div>

            <div className="pt-3 border-t border-[#1E293B] text-[10px] font-mono text-[#64748B] space-y-1">
              <div>IST: {istTime}</div>
              <div>Single Bookmaker: 1xBet Fixed</div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
