'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import EngineStatus from '../dashboard/EngineStatus'

export default function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  const navItems = [
    {
      name: 'Match Intelligence',
      href: '/',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      ),
      badge: 'Live'
    },
    {
      name: 'Paper Bet Ledger',
      href: '/predictions',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      badge: null
    },
    {
      name: 'Performance Analytics',
      href: '/analytics',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      badge: '83% Win'
    },
    {
      name: 'System & Quota',
      href: '/providers',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      badge: '71 Left'
    }
  ]

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-40 bg-[#090c10] border-r border-[#1e2638] flex flex-col justify-between transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Top Workspace Header */}
      <div className="p-3 border-b border-[#1e2638]">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#d4af37] to-[#8a7220] flex items-center justify-center text-black font-extrabold text-xs font-mono shrink-0 shadow-sm">
              1X
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <div className="text-xs font-semibold text-[#f0f4fc] truncate tracking-tight">
                  Football Alpha
                </div>
                <div className="text-[10px] text-[#8a99ad] truncate flex items-center gap-1 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
                  1xBet Fixed Odds
                </div>
              </div>
            )}
          </Link>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-md text-[#56657a] hover:text-[#f0f4fc] hover:bg-[#131924] transition-colors"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg
              className={`w-4 h-4 transition-transform duration-200 ${collapsed ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Mixpanel Style Action Button */}
        {!collapsed && (
          <div className="mt-3">
            <Link
              href="/"
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-gradient-to-r from-[#d4af37] to-[#e6ca65] hover:from-[#c29f2f] hover:to-[#d4af37] text-black font-semibold text-xs transition-all shadow-sm active:scale-[0.98]"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
              </svg>
              <span>Scan 1xBet Fixtures</span>
            </Link>
          </div>
        )}

        {/* Mixpanel Search Bar */}
        {!collapsed && (
          <div className="mt-3 relative">
            <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#0e131b] border border-[#1e2638] text-xs text-[#8a99ad]">
              <svg className="w-3.5 h-3.5 text-[#56657a] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span className="flex-1 text-[11px] truncate">Search matches, leagues...</span>
              <kbd className="px-1.5 py-0.5 text-[9px] font-mono bg-[#131924] border border-[#1e2638] rounded text-[#8a99ad]">⌘K</kbd>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        <div>
          {!collapsed && (
            <div className="px-2 pb-2 text-[10px] font-semibold font-mono tracking-wider text-[#56657a] uppercase">
              Intelligence Boards
            </div>
          )}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-[#182030] text-[#f0f4fc] font-semibold border border-[#2b374e]'
                      : 'text-[#8a99ad] hover:text-[#f0f4fc] hover:bg-[#0e131b]'
                  }`}
                  title={collapsed ? item.name : undefined}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span className={isActive ? 'text-[#d4af37]' : 'text-[#8a99ad]'}>
                      {item.icon}
                    </span>
                    {!collapsed && <span className="truncate">{item.name}</span>}
                  </div>
                  {!collapsed && item.badge && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
                        item.badge === 'Live'
                          ? 'bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30 font-semibold'
                          : 'bg-[#131924] text-[#8a99ad] border border-[#1e2638]'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Mixpanel Saved Boards Section */}
        {!collapsed && (
          <div className="space-y-1">
            <div className="px-2 pb-1 text-[10px] font-semibold font-mono tracking-wider text-[#56657a] uppercase flex items-center justify-between">
              <span>Saved Watchlists</span>
              <span className="text-[10px] text-[#8a99ad]">1xBet</span>
            </div>
            <div className="space-y-0.5 text-xs text-[#8a99ad]">
              <div className="px-2.5 py-1.5 rounded-lg hover:bg-[#0e131b] hover:text-[#f0f4fc] cursor-pointer flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
                <span className="truncate">High EV Signals (&gt;3%)</span>
              </div>
              <div className="px-2.5 py-1.5 rounded-lg hover:bg-[#0e131b] hover:text-[#f0f4fc] cursor-pointer flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#d4af37]"></span>
                <span className="truncate">Lineups Confirmed</span>
              </div>
              <div className="px-2.5 py-1.5 rounded-lg hover:bg-[#0e131b] hover:text-[#f0f4fc] cursor-pointer flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#6366f1]"></span>
                <span className="truncate">Big 5 European Leagues</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Quota Guard Meter (Mixpanel Plan Card Style) */}
      <div className="p-3 border-t border-[#1e2638] space-y-3">
        {!collapsed ? (
          <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-3 space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></div>
                <span className="font-semibold text-[#f0f4fc] text-[11px]">Free Quota Guard</span>
              </div>
              <span className="text-[10px] font-mono text-[#d4af37] font-semibold">₹0.00 Cost</span>
            </div>

            {/* Meter Bar */}
            <div className="space-y-1">
              <div className="w-full bg-[#131924] rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-[#10b981] to-[#d4af37] h-1.5 rounded-full"
                  style={{ width: '29%' }}
                ></div>
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-[#8a99ad]">
                <span>29 used</span>
                <span className="text-[#10b981] font-semibold">71 remaining</span>
              </div>
            </div>

            <div className="text-[10px] text-[#56657a] font-mono pt-1 border-t border-[#1e2638]/60 flex items-center justify-between">
              <span>User Reserve:</span>
              <span className="text-[#f0f4fc] font-medium">50 calls</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="Quota: 29/100 used (71 remaining)">
            <div className="w-8 h-8 rounded-lg bg-[#0e131b] border border-[#1e2638] flex items-center justify-center text-[10px] font-mono font-bold text-[#10b981]">
              71
            </div>
          </div>
        )}

        {/* Engine Toggle & IST Timezone */}
        {!collapsed && (
          <div className="flex items-center justify-between pt-1">
            <div className="text-[10px] font-mono text-[#56657a] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
              <span>IST (UTC+5:30)</span>
            </div>
            <EngineStatus />
          </div>
        )}
      </div>
    </aside>
  )
}
