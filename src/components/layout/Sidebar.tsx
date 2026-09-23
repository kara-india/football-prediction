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
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.75"
            d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
          />
        </svg>
      ),
      badge: 'Live',
    },
    {
      name: 'Paper Bet Ledger',
      href: '/predictions',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.75"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      ),
      badge: null,
    },
    {
      name: 'Performance Analytics',
      href: '/analytics',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.75"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      ),
      badge: 'Audited',
    },
    {
      name: 'Models & LIV Telemetry',
      href: '/models',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.75"
            d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
          />
        </svg>
      ),
      badge: 'v1.4',
    },
    {
      name: 'System & Quota',
      href: '/providers',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.75"
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          />
        </svg>
      ),
      badge: '95 Cap',
    },
  ]

  return (
    <aside
      className={`hidden lg:flex fixed top-0 left-0 bottom-0 z-40 bg-[#0B0F17] border-r border-[#1E293B] flex-col justify-between transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Top Workspace Header */}
      <div className="p-3.5 border-b border-[#1E293B]">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#D4AF37] to-[#8A7220] flex items-center justify-center text-black font-extrabold text-xs font-mono shrink-0 shadow-terminal-sm">
              1X
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <div className="text-xs font-bold text-[#F8FAFC] truncate tracking-tight">
                  Football Terminal
                </div>
                <div className="text-[10px] text-[#94A3B8] truncate flex items-center gap-1 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block animate-pulse" />
                  1xBet Fixed Clearing
                </div>
              </div>
            )}
          </Link>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-md text-[#64748B] hover:text-[#F8FAFC] hover:bg-[#1E293B] transition-colors"
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
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        <div>
          {!collapsed && (
            <div className="px-2 pb-2 text-[10px] font-semibold font-mono tracking-wider text-[#64748B] uppercase">
              Terminal Views
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
                      ? 'bg-[#1E293B] text-[#F8FAFC] font-semibold border border-[#334155]'
                      : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#0F172A]'
                  }`}
                  title={collapsed ? item.name : undefined}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span className={isActive ? 'text-[#D4AF37]' : 'text-[#64748B]'}>{item.icon}</span>
                    {!collapsed && <span className="truncate">{item.name}</span>}
                  </div>
                  {!collapsed && item.badge && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
                        item.badge === 'Live'
                          ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 font-semibold'
                          : 'bg-[#0F172A] text-[#94A3B8] border border-[#1E293B]'
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

        {/* Quick Analytical Filters */}
        {!collapsed && (
          <div className="space-y-1">
            <div className="px-2 pb-1 text-[10px] font-semibold font-mono tracking-wider text-[#64748B] uppercase flex items-center justify-between">
              <span>Allowlisted Scope</span>
              <span className="text-[10px] text-[#94A3B8]">10 Leagues</span>
            </div>
            <div className="space-y-0.5 text-xs text-[#94A3B8]">
              <div className="px-2.5 py-1.5 rounded-lg hover:bg-[#0F172A] hover:text-[#F8FAFC] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
                <span className="truncate">Top 5 European Leagues</span>
              </div>
              <div className="px-2.5 py-1.5 rounded-lg hover:bg-[#0F172A] hover:text-[#F8FAFC] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" />
                <span className="truncate">Confirmed Starting XIs</span>
              </div>
              <div className="px-2.5 py-1.5 rounded-lg hover:bg-[#0F172A] hover:text-[#F8FAFC] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0EA5E9]" />
                <span className="truncate">UEFA Club Competitions</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Quota Guard Meter */}
      <div className="p-3 border-t border-[#1E293B] space-y-3">
        {!collapsed ? (
          <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 space-y-2.5 shadow-terminal-sm">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
                <span className="font-semibold text-[#F8FAFC] text-[11px]">Daily Quota Governance</span>
              </div>
              <span className="text-[10px] font-mono text-[#D4AF37] font-semibold">₹0.00 Cost</span>
            </div>

            {/* Meter Bar */}
            <div className="space-y-1">
              <div className="w-full bg-[#0B0F17] rounded-full h-1.5 overflow-hidden border border-[#1E293B]">
                <div
                  className="bg-gradient-to-r from-[#10B981] to-[#D4AF37] h-1.5 rounded-full"
                  style={{ width: '15%' }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-[#94A3B8]">
                <span>0 used today</span>
                <span className="text-[#10B981] font-semibold">95 / 95 cap</span>
              </div>
            </div>

            <div className="text-[10px] text-[#64748B] font-mono pt-1 border-t border-[#1E293B] flex items-center justify-between">
              <span>User Reserve:</span>
              <span className="text-[#F8FAFC] font-medium">50 calls</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="Quota: 95/95 remaining">
            <div className="w-8 h-8 rounded-lg bg-[#0F172A] border border-[#1E293B] flex items-center justify-center text-[10px] font-mono font-bold text-[#10B981]">
              95
            </div>
          </div>
        )}

        {/* Engine Toggle & IST Timezone */}
        {!collapsed && (
          <div className="flex items-center justify-between pt-1">
            <div className="text-[10px] font-mono text-[#64748B] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
              <span>IST (UTC+5:30)</span>
            </div>
            <EngineStatus />
          </div>
        )}
      </div>
    </aside>
  )
}
