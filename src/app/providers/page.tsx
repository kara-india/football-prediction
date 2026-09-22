'use client'

import React, { useState } from 'react'

export default function Providers() {
  const [refreshing, setRefreshing] = useState(false)
  const [lastCheck, setLastCheck] = useState('Just now')

  const refreshStatus = () => {
    setRefreshing(true)
    setTimeout(() => {
      setRefreshing(false)
      const now = new Date()
      setLastCheck(
        now.toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }) + ' IST'
      )
    }, 600)
  }

  const FEEDS = [
    {
      name: '1xBet Execution Market Feed',
      category: 'Target Pricing',
      status: 'OPERATIONAL',
      latency: '245 ms',
      quota: 'Direct Fixed Odds Feed',
      statusDetail: '1xBet verified fixed prices',
      markets: ['1X2 Match Winner', 'Double Chance', 'Over/Under 1.5–4.5', 'Both Teams To Score'],
      notes: 'Real-time execution target prices. Predictions strictly match live 1xBet odds with zero substitutes.'
    },
    {
      name: 'Live Match & Lineup Feed',
      category: 'Team Sheets & Events',
      status: 'OPERATIONAL',
      latency: '190 ms',
      quota: 'Direct Official Lineups',
      statusDetail: 'Official starting XI feeds active',
      markets: ['Kickoff Timings', 'Starting XIs', 'Formations', 'Match Events', 'In-Play Scores'],
      notes: 'Monitors official team sheet releases ~60 minutes before kickoff across all allowlisted competitions.'
    },
    {
      name: 'Historical Performance Vault',
      category: 'Reference Dataset',
      status: 'SYNCHRONIZED',
      latency: '1 ms (Fast Cache)',
      quota: '5-Year Verified History',
      statusDetail: '7,230+ European matches active',
      markets: ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'Champions League'],
      notes: 'Offline reference records covering past 5 completed seasons for zero-credit baseline evaluations.'
    },
    {
      name: 'Secure Cloud Storage',
      category: 'Ledger & Auditing',
      status: 'CONNECTED',
      latency: '82 ms',
      quota: 'Cloud Persistence',
      statusDetail: 'Fully encrypted and synchronized',
      markets: ['Paper Bets', 'Audit Trails', 'Performance Ledger', 'User Settings'],
      notes: 'Maintains immutable timestamps and settled prediction records for complete audit transparency.'
    }
  ]

  const QUOTA_RULES = [
    {
      priority: 'P1 (Highest)',
      label: 'On-Demand Match Analysis',
      cost: '1 Credit / click',
      allocation: '50 Credits Reserved strictly for your manual match requests'
    },
    {
      priority: 'P2',
      label: 'Live In-Play Match Updates',
      cost: 'Cached sync',
      allocation: 'Monitors score changes and in-play market adjustments'
    },
    {
      priority: 'P3',
      label: 'Daily Fixture Ingestion',
      cost: '1 Bulk Call / day',
      allocation: 'Scans scheduled matches across 10 allowlisted European leagues'
    },
    {
      priority: 'P4',
      label: 'Historical Benchmark Fitting',
      cost: '0 Credits (Free)',
      allocation: 'Executed entirely offline with zero credit consumption'
    }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-[#1e2638] pb-6">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#8a99ad] bg-[#0e131b] border border-[#1e2638]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
            <span>Zero Cost Ingestion Architecture</span>
            <span className="text-[#56657a]">·</span>
            <span className="text-[#d4af37]">₹0.00 Exp Guaranteed</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc]">
            System Status & Quota Protection
          </h1>
          <p className="text-xs sm:text-sm text-[#8a99ad] max-w-2xl leading-relaxed">
            Feed telemetry, latency monitoring, and daily analysis credit management.
            Ensures you pay ₹0.00 while maintaining real-time 1xBet market precision.
          </p>
        </div>

        <button
          onClick={refreshStatus}
          disabled={refreshing}
          className="inline-flex items-center gap-2 self-start sm:self-auto px-4 py-2 text-xs font-medium text-[#f0f4fc] bg-[#0e131b] hover:bg-[#131924] border border-[#1e2638] rounded-xl transition-colors disabled:opacity-50 font-mono shadow-sm"
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
          <span>{refreshing ? 'Checking' : `Check Telemetry (${lastCheck})`}</span>
        </button>
      </div>

      {/* Credit Status Card */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-4 shadow-sm font-mono">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1e2638] pb-4">
          <div>
            <div className="text-sm font-bold text-[#f0f4fc]">Daily Credit Allowance</div>
            <div className="text-xs text-[#8a99ad]">Zero cost guarantee with hard cap at 95 credits</div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-lg bg-[#10b981]/15 text-[#10b981] font-semibold border border-[#10b981]/30">
              ₹0.00 Incurred
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-2">
          <div className="bg-[#090c10] border border-[#1e2638] rounded-xl p-3.5">
            <div className="text-[10px] text-[#56657a] uppercase">Daily Cap</div>
            <div className="text-xl font-bold text-[#f0f4fc] mt-1">100 Credits</div>
            <div className="text-[10px] text-[#8a99ad]">Free tier allowance</div>
          </div>

          <div className="bg-[#090c10] border border-[#1e2638] rounded-xl p-3.5">
            <div className="text-[10px] text-[#56657a] uppercase">Used Today</div>
            <div className="text-xl font-bold text-[#d4af37] mt-1">29 Credits</div>
            <div className="text-[10px] text-[#8a99ad]">Automated fixtures</div>
          </div>

          <div className="bg-[#090c10] border border-[#1e2638] rounded-xl p-3.5">
            <div className="text-[10px] text-[#56657a] uppercase">Remaining</div>
            <div className="text-xl font-bold text-[#10b981] mt-1">71 Credits</div>
            <div className="text-[10px] text-[#8a99ad]">Available for today</div>
          </div>

          <div className="bg-[#090c10] border border-[#1e2638] rounded-xl p-3.5">
            <div className="text-[10px] text-[#56657a] uppercase">User Reserved</div>
            <div className="text-xl font-bold text-[#10b981] mt-1">50 Credits</div>
            <div className="text-[10px] text-[#8a99ad]">Protected for on-demand</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="pt-2 space-y-1.5">
          <div className="flex justify-between text-xs text-[#8a99ad]">
            <span>29% Used</span>
            <span className="text-[#10b981] font-semibold">71% Available</span>
          </div>
          <div className="w-full bg-[#131924] rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-[#10b981] to-[#d4af37] h-2 rounded-full"
              style={{ width: '29%' }}
            ></div>
          </div>
        </div>
      </div>

      {/* Feed Status Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {FEEDS.map((p) => (
          <div
            key={p.name}
            className="bg-[#0e131b] border border-[#1e2638] hover:border-[#2b374e] rounded-2xl p-6 transition-all duration-200 flex flex-col justify-between shadow-sm"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#1e2638] pb-3">
                <div>
                  <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">{p.name}</h2>
                  <span className="text-[11px] font-mono text-[#8a99ad]">{p.category}</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono text-[#10b981] bg-[#10b981]/15 border border-[#10b981]/30 font-semibold">
                  {p.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#56657a]">Latency</div>
                  <div className="text-xs font-bold text-[#f0f4fc] mt-0.5">{p.latency}</div>
                </div>

                <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#56657a]">Feed State</div>
                  <div className="text-xs font-bold text-[#10b981] mt-0.5">{p.statusDetail}</div>
                </div>
              </div>

              <div className="space-y-1 text-xs">
                <div className="text-[11px] text-[#8a99ad]">Supported Channels:</div>
                <div className="flex flex-wrap gap-1">
                  {p.markets.map((m) => (
                    <span
                      key={m}
                      className="px-2 py-0.5 rounded bg-[#131924] text-[10px] text-[#8a99ad] font-mono border border-[#1e2638]"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <p className="mt-5 pt-3 border-t border-[#1e2638] text-[11px] text-[#8a99ad] leading-relaxed font-sans">
              {p.notes}
            </p>
          </div>
        ))}
      </div>

      {/* Credit Allocation Policy */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-4 shadow-sm">
        <div className="border-b border-[#1e2638] pb-4">
          <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
            Credit Allocation Policy
          </h2>
          <p className="text-xs text-[#8a99ad] mt-0.5">
            Strict allocation hierarchy protecting your 50 reserved user credits
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-[#1e2638] bg-[#090c10]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#090c10] text-[#56657a] uppercase text-[10px] tracking-wider border-b border-[#1e2638]">
              <tr>
                <th className="py-3 px-4">Priority Tier</th>
                <th className="py-3 px-3">Classification</th>
                <th className="py-3 px-3">Credit Cost</th>
                <th className="py-3 px-4">Policy Guarantee</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2638] text-[#8a99ad]">
              {QUOTA_RULES.map((b) => (
                <tr key={b.priority} className="hover:bg-[#131924]/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-[#d4af37] text-sm">{b.priority}</td>
                  <td className="py-3.5 px-3 font-semibold text-[#f0f4fc]">{b.label}</td>
                  <td className="py-3.5 px-3 text-[#10b981] font-bold whitespace-nowrap">{b.cost}</td>
                  <td className="py-3.5 px-4 text-[11px] text-[#8a99ad] font-sans">{b.allocation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
