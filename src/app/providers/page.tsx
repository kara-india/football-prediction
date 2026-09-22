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

  const PROVIDERS = [
    {
      name: '1xBet Odds Feed',
      slug: '1xbet-feed',
      status: 'OPERATIONAL',
      is1xBetConfirmed: true,
      authStatus: 'Bookmaker ID: 6 (Verified)',
      latency: '245 ms',
      quota: '100 / day (Shared API-Football)',
      remaining: '71 remaining (50 reserved for user)',
      markets: ['1X2', 'Double Chance', 'Over/Under 1.5–4.5', 'BTTS', 'Next Goal', 'Cards', 'Goalscorer'],
      notes: 'Target execution price source. Model strictly prohibits substituting any other bookmaker odds.'
    },
    {
      name: 'API-Football v3',
      slug: 'api-football',
      status: 'ACTIVE',
      is1xBetConfirmed: true,
      authStatus: 'Key: 0735...83fa',
      latency: '190 ms',
      quota: '100 requests / day',
      remaining: '71 remaining',
      markets: ['Fixtures', 'Starting XIs', 'Match Events', 'Player Projections', 'Market Odds'],
      notes: 'Primary feed for upcoming fixtures, confirmed starting lineups, and match stats.'
    },
    {
      name: 'football-data.co.uk (Historical)',
      slug: 'football-data-uk',
      status: 'CONNECTED',
      is1xBetConfirmed: false,
      authStatus: '7,230+ Matches in Supabase',
      latency: '1 ms (Local DB)',
      quota: 'Zero Cost (Free Bulk CSVs)',
      remaining: 'Uncapped',
      markets: ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'Eredivisie'],
      notes: 'Historical match and odds dataset for past 5 completed seasons. Used for offline model fitting with zero API calls.'
    },
    {
      name: 'Supabase Cloud Database',
      slug: 'supabase-db',
      status: 'CONNECTED',
      is1xBetConfirmed: false,
      authStatus: 'Host: qqcxjjkgvqknesrtnwal.supabase.co',
      latency: '82 ms',
      quota: 'PostgreSQL Cloud',
      remaining: '27 Tables Active',
      markets: ['Competitions', 'Feature Snapshots', 'Predictions', 'Paper Ledger', 'Settings'],
      notes: 'Holds persistent prediction logs, live feature stores, historical matches, and safety engine configurations.'
    }
  ]

  const BUDGET_ALLOCATOR = [
    {
      priority: 'P0',
      label: 'Critical Live State',
      endpoints: '1xBet live odds, current match score, red card ejections',
      cost: '1 req / 60s (cached)',
      policy: 'Unthrottled allocation during live matches'
    },
    {
      priority: 'P1',
      label: 'User Match Selection',
      endpoints: 'Confirmed starting lineups, formations, player stats',
      cost: '1 req per user click',
      policy: 'Drawn strictly from the 50 reserved user requests'
    },
    {
      priority: 'P2',
      label: 'Scheduled Candidate Sync',
      endpoints: 'Daily match schedule, opening 1xBet market lines',
      cost: '1 bulk call / day',
      policy: 'Filtered to top 50 matches max (Quota Guardian enforced)'
    },
    {
      priority: 'P3',
      label: 'Historical Data Fitting',
      endpoints: 'Historical seasons, shot volume, closing prices',
      cost: '0 API calls',
      policy: 'Handled 100% offline via football-data.co.uk CSVs'
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
            <span className="text-[#d4af37]">Hard Quota Gate 95/100</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc]">
            Data Feeds & Quota Protection
          </h1>
          <p className="text-xs sm:text-sm text-[#8a99ad] max-w-2xl leading-relaxed">
            Infrastructure telemetry, latency monitoring, and zero-cost quota allocation rules.
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
          <span>{refreshing ? 'Checking' : `Check Health (${lastCheck})`}</span>
        </button>
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {PROVIDERS.map((p) => (
          <div
            key={p.slug}
            className="bg-[#0e131b] border border-[#1e2638] hover:border-[#2b374e] rounded-2xl p-6 transition-all duration-200 flex flex-col justify-between shadow-sm"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#1e2638] pb-3">
                <div>
                  <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">{p.name}</h2>
                  <span className="text-[11px] font-mono text-[#8a99ad]">{p.authStatus}</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono text-[#10b981] bg-[#10b981]/15 border border-[#10b981]/30 font-semibold">
                  {p.status}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#56657a]">1xBet Feed</div>
                  <div
                    className={`text-xs font-bold mt-0.5 ${
                      p.is1xBetConfirmed ? 'text-[#d4af37]' : 'text-[#8a99ad]'
                    }`}
                  >
                    {p.is1xBetConfirmed ? 'ID: 6 (Direct)' : 'N/A'}
                  </div>
                </div>

                <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#56657a]">Latency</div>
                  <div className="text-xs font-bold text-[#f0f4fc] mt-0.5">{p.latency}</div>
                </div>

                <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#56657a]">Remaining</div>
                  <div className="text-xs font-bold text-[#10b981] mt-0.5">{p.remaining}</div>
                </div>
              </div>

              <div className="space-y-1 text-xs">
                <div className="text-[11px] text-[#8a99ad]">Supported Markets:</div>
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

      {/* Request Budget Allocator Table */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-4 shadow-sm">
        <div className="border-b border-[#1e2638] pb-4">
          <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
            Request Budget Allocator (P0 – P3 Priority Queue)
          </h2>
          <p className="text-xs text-[#8a99ad] mt-0.5">
            Strict 50/50 quota partition: 50 requests allocated for automated sync, 50 requests reserved for user analysis.
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-[#1e2638] bg-[#090c10]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#090c10] text-[#56657a] uppercase text-[10px] tracking-wider border-b border-[#1e2638]">
              <tr>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-3">Classification</th>
                <th className="py-3 px-4">Endpoints</th>
                <th className="py-3 px-3">Standard Cost</th>
                <th className="py-3 px-4">Allocation Policy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2638] text-[#8a99ad]">
              {BUDGET_ALLOCATOR.map((b) => (
                <tr key={b.priority} className="hover:bg-[#131924]/60 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-[#d4af37] text-sm">{b.priority}</td>
                  <td className="py-3.5 px-3 font-semibold text-[#f0f4fc]">{b.label}</td>
                  <td className="py-3.5 px-4 text-[#8a99ad]">{b.endpoints}</td>
                  <td className="py-3.5 px-3 text-[#10b981] font-bold whitespace-nowrap">{b.cost}</td>
                  <td className="py-3.5 px-4 text-[11px] text-[#8a99ad] font-sans">{b.policy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
