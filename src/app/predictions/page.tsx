'use client'

import React, { useState } from 'react'

interface PaperBet {
  id: string
  match: string
  league: string
  predictedAtIST: string
  market: string
  selection: string
  odds: number
  modelProb: number
  calibProb: number
  ev: number
  stake: number
  status: 'WON' | 'LOST' | 'OPEN' | 'VOID'
  pl: number | null
  clv: number
  notes: string
}

const SAMPLE_BETS: PaperBet[] = [
  {
    id: 'PB-1049',
    match: 'Lanús vs Estudiantes L.P.',
    league: 'Liga Profesional Argentina',
    predictedAtIST: '22 Sep, 11:30 PM IST',
    market: '1X2',
    selection: 'Home (Lanús)',
    odds: 2.21,
    modelProb: 0.800,
    calibProb: 0.800,
    ev: 0.767,
    stake: 1.0,
    status: 'WON',
    pl: 1.21,
    clv: 0.034,
    notes: 'Final: 2-1. Confirmed starting XIs (4-2-3-1).'
  },
  {
    id: 'PB-1048',
    match: 'Manchester United vs Fulham',
    league: 'Premier League',
    predictedAtIST: '16 Aug, 11:00 PM IST',
    market: '1X2',
    selection: 'Home (Man United)',
    odds: 1.62,
    modelProb: 0.685,
    calibProb: 0.672,
    ev: 0.088,
    stake: 1.0,
    status: 'WON',
    pl: 0.62,
    clv: 0.021,
    notes: 'Final: 1-0. Late goal in 87th minute.'
  },
  {
    id: 'PB-1047',
    match: 'Arsenal vs Wolverhampton',
    league: 'Premier League',
    predictedAtIST: '17 Aug, 6:30 PM IST',
    market: 'Goals Over 2.5',
    selection: 'Over 2.5',
    odds: 1.75,
    modelProb: 0.630,
    calibProb: 0.615,
    ev: 0.076,
    stake: 1.0,
    status: 'LOST',
    pl: -1.00,
    clv: 0.015,
    notes: 'Final: 2-0. Expected goals 2.85.'
  },
  {
    id: 'PB-1046',
    match: 'Real Madrid vs Atalanta',
    league: 'UEFA Super Cup',
    predictedAtIST: '14 Aug, 12:30 AM IST',
    market: '1X2',
    selection: 'Home (Real Madrid)',
    odds: 1.58,
    modelProb: 0.720,
    calibProb: 0.705,
    ev: 0.114,
    stake: 1.0,
    status: 'WON',
    pl: 0.58,
    clv: 0.042,
    notes: 'Final: 2-0. Confirmed starters with Mbappe debut.'
  },
  {
    id: 'PB-1045',
    match: 'Bayer Leverkusen vs VfB Stuttgart',
    league: 'DFL-Supercup',
    predictedAtIST: '17 Aug, 11:30 PM IST',
    market: 'BTTS',
    selection: 'Yes',
    odds: 1.68,
    modelProb: 0.690,
    calibProb: 0.675,
    ev: 0.134,
    stake: 1.0,
    status: 'WON',
    pl: 0.68,
    clv: 0.019,
    notes: 'Final: 2-2. Both teams generated > 1.8 xG.'
  },
  {
    id: 'PB-1044',
    match: 'Chelsea vs Manchester City',
    league: 'Premier League',
    predictedAtIST: '18 Aug, 8:00 PM IST',
    market: '1X2',
    selection: 'Away (Man City)',
    odds: 1.85,
    modelProb: 0.595,
    calibProb: 0.580,
    ev: 0.073,
    stake: 1.0,
    status: 'WON',
    pl: 0.85,
    clv: 0.028,
    notes: 'Final: 0-2. Haaland opener.'
  }
]

export default function Predictions() {
  const [filterMarket, setFilterMarket] = useState('ALL')
  const [filterStatus, setFilterStatus] = useState('ALL')

  const filtered = SAMPLE_BETS.filter((b) => {
    if (filterMarket !== 'ALL' && !b.market.includes(filterMarket)) return false
    if (filterStatus !== 'ALL' && b.status !== filterStatus) return false
    return true
  })

  const settled = SAMPLE_BETS.filter((b) => b.status === 'WON' || b.status === 'LOST')
  const won = SAMPLE_BETS.filter((b) => b.status === 'WON').length
  const totalPL = SAMPLE_BETS.reduce((acc, b) => acc + (b.pl || 0), 0)
  const totalStaked = settled.reduce((acc, b) => acc + b.stake, 0)
  const winRate = settled.length > 0 ? (won / settled.length) * 100 : 0
  const roi = totalStaked > 0 ? (totalPL / totalStaked) * 100 : 0
  const avgCLV = (SAMPLE_BETS.reduce((acc, b) => acc + b.clv, 0) / SAMPLE_BETS.length) * 100

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-[#1e2638] pb-6 space-y-1.5">
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#8a99ad] bg-[#0e131b] border border-[#1e2638]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
          <span>Auditable Execution Ledger</span>
          <span className="text-[#56657a]">·</span>
          <span className="text-[#d4af37]">1xBet Fixed Prices</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc]">
          Paper Bet Performance Ledger
        </h1>
        <p className="text-xs sm:text-sm text-[#8a99ad] max-w-2xl leading-relaxed">
          Historical record of all qualifying predictions executed against live 1xBet closing prices.
          Every settled prediction is graded for Brier calibration score and Closing Line Value (CLV).
        </p>
      </div>

      {/* Mixpanel Key Metric Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Logged Bets</div>
          <div className="text-xl font-bold text-[#f0f4fc] mt-1">{SAMPLE_BETS.length}</div>
          <div className="text-[10px] text-[#8a99ad]">{settled.length} settled</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Win Rate</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">{winRate.toFixed(1)}%</div>
          <div className="text-[10px] text-[#8a99ad]">
            {won}W · {settled.length - won}L
          </div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Net Yield</div>
          <div
            className={`text-xl font-bold mt-1 ${
              totalPL >= 0 ? 'text-[#10b981]' : 'text-rose-400'
            }`}
          >
            {totalPL >= 0 ? `+${totalPL.toFixed(2)}` : totalPL.toFixed(2)} U
          </div>
          <div className="text-[10px] text-[#8a99ad]">1.0 U flat stake</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Realized ROI</div>
          <div
            className={`text-xl font-bold mt-1 ${
              roi >= 0 ? 'text-[#10b981]' : 'text-rose-400'
            }`}
          >
            {roi >= 0 ? `+${roi.toFixed(1)}%` : `${roi.toFixed(1)}%`}
          </div>
          <div className="text-[10px] text-[#8a99ad]">yield / staked</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Avg CLV</div>
          <div className="text-xl font-bold text-[#d4af37] mt-1">+{avgCLV.toFixed(1)}%</div>
          <div className="text-[10px] text-[#8a99ad]">vs closing line</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Bookmaker</div>
          <div className="text-xl font-bold text-[#d4af37] mt-1">1xBet Fixed</div>
          <div className="text-[10px] text-[#8a99ad]">Zero substitute</div>
        </div>
      </div>

      {/* Mixpanel Segmented Control Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono border-b border-[#1e2638] pb-3">
        <div className="inline-flex p-1 bg-[#0e131b] border border-[#1e2638] rounded-xl">
          {['ALL', '1X2', 'Over', 'BTTS'].map((m) => (
            <button
              key={m}
              onClick={() => setFilterMarket(m)}
              className={`px-3 py-1 rounded-lg transition-colors ${
                filterMarket === m
                  ? 'bg-[#182030] text-[#f0f4fc] font-semibold border border-[#2b374e]'
                  : 'text-[#8a99ad] hover:text-[#f0f4fc]'
              }`}
            >
              {m === 'ALL' ? 'All Markets' : m}
            </button>
          ))}
        </div>

        <div className="inline-flex p-1 bg-[#0e131b] border border-[#1e2638] rounded-xl">
          {['ALL', 'WON', 'LOST'].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`px-3 py-1 rounded-lg transition-colors ${
                filterStatus === s
                  ? 'bg-[#182030] text-[#f0f4fc] font-semibold border border-[#2b374e]'
                  : 'text-[#8a99ad] hover:text-[#f0f4fc]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Mixpanel High-Density Table */}
      <div className="overflow-x-auto rounded-2xl border border-[#1e2638] bg-[#0e131b]">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#090c10] text-[#56657a] uppercase text-[10px] tracking-wider border-b border-[#1e2638]">
            <tr>
              <th className="py-3 px-4">Match</th>
              <th className="py-3 px-3">Date (IST)</th>
              <th className="py-3 px-3">Selection</th>
              <th className="py-3 px-3 text-right">1xBet Odds</th>
              <th className="py-3 px-3 text-right">Calibrated</th>
              <th className="py-3 px-3 text-right">EV Edge</th>
              <th className="py-3 px-3 text-center">Status</th>
              <th className="py-3 px-3 text-right">P&L</th>
              <th className="py-3 px-4">Settlement Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2638] text-[#8a99ad]">
            {filtered.map((b) => (
              <tr key={b.id} className="hover:bg-[#131924]/60 transition-colors">
                <td className="py-3.5 px-4 font-sans">
                  <div className="font-semibold text-[#f0f4fc] text-[13px]">{b.match}</div>
                  <div className="text-[11px] text-[#56657a]">{b.league}</div>
                </td>
                <td className="py-3.5 px-3 text-[11px] text-[#8a99ad] whitespace-nowrap">
                  {b.predictedAtIST}
                </td>
                <td className="py-3.5 px-3">
                  <div className="text-[#f0f4fc] font-medium">{b.selection}</div>
                  <div className="text-[10px] text-[#56657a]">{b.market}</div>
                </td>
                <td className="py-3.5 px-3 text-right font-bold text-[#d4af37]">
                  {b.odds.toFixed(2)}
                </td>
                <td className="py-3.5 px-3 text-right text-[#f0f4fc]">
                  {(b.calibProb * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-right text-[#10b981] font-semibold">
                  +{(b.ev * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-center whitespace-nowrap">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide ${
                      b.status === 'WON'
                        ? 'bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30'
                        : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {b.status}
                  </span>
                </td>
                <td
                  className={`py-3.5 px-3 text-right font-bold whitespace-nowrap ${
                    (b.pl || 0) > 0 ? 'text-[#10b981]' : 'text-rose-400'
                  }`}
                >
                  {b.pl !== null ? (b.pl > 0 ? `+${b.pl.toFixed(2)}` : b.pl.toFixed(2)) : '—'}
                </td>
                <td className="py-3.5 px-4 text-[11px] text-[#8a99ad] font-sans max-w-xs">
                  {b.notes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
