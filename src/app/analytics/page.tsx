'use client'

import React from 'react'

export default function Analytics() {
  const MARKET_PERFORMANCE = [
    {
      market: '1X2 Match Winner',
      samples: 48,
      winRate: '81.2%',
      avgOdds: 1.84,
      roi: '+52.4%',
      status: 'VERIFIED'
    },
    {
      market: 'Goals Over / Under 2.5',
      samples: 36,
      winRate: '77.8%',
      avgOdds: 1.76,
      roi: '+41.2%',
      status: 'VERIFIED'
    },
    {
      market: 'Both Teams To Score (BTTS)',
      samples: 30,
      winRate: '83.3%',
      avgOdds: 1.72,
      roi: '+48.6%',
      status: 'VERIFIED'
    },
    {
      market: 'Double Chance (1X / X2)',
      samples: 24,
      winRate: '87.5%',
      avgOdds: 1.48,
      roi: '+36.8%',
      status: 'VERIFIED'
    }
  ]

  const LEAGUE_BREAKDOWN = [
    { league: 'Premier League', country: 'England', matches: 38, winRate: '84.2%', roi: '+56.4%' },
    { league: 'La Liga', country: 'Spain', matches: 32, winRate: '81.2%', roi: '+44.8%' },
    { league: 'Serie A', country: 'Italy', matches: 28, winRate: '82.1%', roi: '+47.2%' },
    { league: 'Bundesliga', country: 'Germany', matches: 26, winRate: '76.9%', roi: '+38.5%' },
    { league: 'UEFA Champions League', country: 'Europe', matches: 16, winRate: '87.5%', roi: '+64.1%' }
  ]

  const ODDS_TIERS = [
    { range: '1.40 – 1.65', label: 'Conservative Value', count: 42, winRate: '88.1%', roi: '+28.4%' },
    { range: '1.66 – 1.95', label: 'Balanced Edge', count: 54, winRate: '81.5%', roi: '+58.2%' },
    { range: '1.96 – 2.40', label: 'High Yield', count: 28, winRate: '75.0%', roi: '+68.5%' },
    { range: '2.40+', label: 'Underdog Value', count: 14, winRate: '64.3%', roi: '+72.1%' }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-[#1e2638] pb-6 space-y-1.5">
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#8a99ad] bg-[#0e131b] border border-[#1e2638]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
          <span>Verified Market Performance</span>
          <span className="text-[#56657a]">·</span>
          <span className="text-[#d4af37]">1xBet Fixed Closing Prices</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc]">
          Performance Analytics
        </h1>
        <p className="text-xs sm:text-sm text-[#8a99ad] max-w-2xl leading-relaxed">
          Historical win rates, odds distribution, and market profitability across allowlisted European football competitions.
        </p>
      </div>

      {/* Mixpanel Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Overall Accuracy</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">83.3%</div>
          <div className="text-[10px] text-[#8a99ad]">Past 30 days</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Net Yield</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">+3.92 U</div>
          <div className="text-[10px] text-[#8a99ad]">Flat 1.0 stake</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Realized ROI</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">+65.3%</div>
          <div className="text-[10px] text-[#8a99ad]">On settled picks</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Avg Odds</div>
          <div className="text-xl font-bold text-[#d4af37] mt-1">1.82</div>
          <div className="text-[10px] text-[#8a99ad]">1xBet fixed price</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Lineup Lock</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">88.9%</div>
          <div className="text-[10px] text-[#8a99ad]">On confirmed XIs</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Max Drawdown</div>
          <div className="text-xl font-bold text-rose-400 mt-1">-1.00 U</div>
          <div className="text-[10px] text-[#8a99ad]">Controlled risk</div>
        </div>
      </div>

      {/* Performance by Odds Range */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1e2638] pb-4">
          <div>
            <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
              Performance by Odds Range
            </h2>
            <p className="text-xs text-[#8a99ad] mt-0.5">
              Breakdown of verified outcomes across conservative, balanced, and high-yield price brackets
            </p>
          </div>
          <span className="text-xs font-mono text-[#d4af37] bg-[#090c10] border border-[#1e2638] px-3 py-1 rounded-lg">
            1xBet Fixed Odds
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
          {ODDS_TIERS.map((tier) => (
            <div
              key={tier.range}
              className="bg-[#090c10] border border-[#1e2638] hover:border-[#2b374e] rounded-xl p-4 space-y-3 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-[#d4af37]">{tier.range}</span>
                <span className="text-[10px] text-[#56657a]">{tier.count} matches</span>
              </div>

              <div>
                <div className="text-xs font-semibold text-[#f0f4fc]">{tier.label}</div>
              </div>

              <div className="space-y-1.5 pt-1 text-xs">
                <div className="flex justify-between text-[11px]">
                  <span className="text-[#8a99ad]">Win Rate:</span>
                  <span className="text-[#10b981] font-bold">{tier.winRate}</span>
                </div>
                <div className="w-full bg-[#131924] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#10b981] h-full rounded-full"
                    style={{ width: tier.winRate }}
                  ></div>
                </div>

                <div className="flex justify-between text-[11px] pt-1">
                  <span className="text-[#8a99ad]">Yield ROI:</span>
                  <span className="text-[#10b981] font-semibold">{tier.roi}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Market Type Breakdown Table */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-4">
        <div className="border-b border-[#1e2638] pb-4">
          <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
            Market Type Breakdown
          </h2>
          <p className="text-xs text-[#8a99ad] mt-0.5">
            Verified yield across standard betting markets
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-[#1e2638] bg-[#090c10]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#090c10] text-[#56657a] uppercase text-[10px] tracking-wider border-b border-[#1e2638]">
              <tr>
                <th className="py-3 px-4">Market</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Settled Matches</th>
                <th className="py-3 px-3 text-right">Win Rate</th>
                <th className="py-3 px-3 text-right">Avg Odds</th>
                <th className="py-3 px-3 text-right">Realized ROI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2638] text-[#8a99ad]">
              {MARKET_PERFORMANCE.map((m) => (
                <tr key={m.market} className="hover:bg-[#131924]/60 transition-colors">
                  <td className="py-3.5 px-4 font-sans font-semibold text-[#f0f4fc] text-[13px]">
                    {m.market}
                  </td>
                  <td className="py-3.5 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold tracking-wide bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-right text-[#8a99ad]">{m.samples}</td>
                  <td className="py-3.5 px-3 text-right text-[#10b981] font-bold">{m.winRate}</td>
                  <td className="py-3.5 px-3 text-right text-[#d4af37] font-semibold">
                    {m.avgOdds.toFixed(2)}
                  </td>
                  <td className="py-3.5 px-3 text-right text-[#10b981] font-bold">{m.roi}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* League Breakdown Table */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-4">
        <div className="border-b border-[#1e2638] pb-4">
          <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
            League & Competition Accuracy
          </h2>
          <p className="text-xs text-[#8a99ad] mt-0.5">
            Performance audited across top European leagues
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-[#1e2638] bg-[#090c10]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#090c10] text-[#56657a] uppercase text-[10px] tracking-wider border-b border-[#1e2638]">
              <tr>
                <th className="py-3 px-4">Competition</th>
                <th className="py-3 px-3">Region</th>
                <th className="py-3 px-3 text-right">Evaluated Matches</th>
                <th className="py-3 px-3 text-right">Win Rate</th>
                <th className="py-3 px-3 text-right">Realized ROI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2638] text-[#8a99ad]">
              {LEAGUE_BREAKDOWN.map((l) => (
                <tr key={l.league} className="hover:bg-[#131924]/60 transition-colors">
                  <td className="py-3.5 px-4 font-sans font-semibold text-[#f0f4fc] text-[13px]">
                    {l.league}
                  </td>
                  <td className="py-3.5 px-3 text-[#8a99ad]">{l.country}</td>
                  <td className="py-3.5 px-3 text-right text-[#8a99ad]">{l.matches}</td>
                  <td className="py-3.5 px-3 text-right text-[#10b981] font-bold">{l.winRate}</td>
                  <td className="py-3.5 px-3 text-right text-[#10b981] font-bold">{l.roi}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
