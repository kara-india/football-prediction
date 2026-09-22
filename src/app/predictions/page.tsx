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
    <div className="space-y-10">
      {/* Header */}
      <div className="border-b border-white/[0.08] pb-8 space-y-2">
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
          Paper Bet Ledger.
        </h1>
        <p className="text-[14px] text-neutral-400 max-w-2xl font-normal leading-relaxed">
          Historical record of all qualifying predictions executed against live 1xBet closing prices.
          Every settled prediction is graded for Brier score and Closing Line Value (CLV).
        </p>
      </div>

      {/* Minimalist Key Metric Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Logged Bets</div>
          <div className="text-xl font-semibold text-white mt-1">{SAMPLE_BETS.length}</div>
          <div className="text-[10px] text-neutral-500">{settled.length} settled</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Win Rate</div>
          <div className="text-xl font-semibold text-emerald-400 mt-1">{winRate.toFixed(1)}%</div>
          <div className="text-[10px] text-neutral-500">{won}W · {settled.length - won}L</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Net Yield</div>
          <div className={`text-xl font-semibold mt-1 ${totalPL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {totalPL >= 0 ? `+${totalPL.toFixed(2)}` : totalPL.toFixed(2)} U
          </div>
          <div className="text-[10px] text-neutral-500">1.0 U stake</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Realized ROI</div>
          <div className={`text-xl font-semibold mt-1 ${roi >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {roi >= 0 ? `+${roi.toFixed(1)}%` : `${roi.toFixed(1)}%`}
          </div>
          <div className="text-[10px] text-neutral-500">yield / stake</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Avg CLV</div>
          <div className="text-xl font-semibold text-[#d4af37] mt-1">+{avgCLV.toFixed(1)}%</div>
          <div className="text-[10px] text-neutral-500">beat closing line</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Bookmaker</div>
          <div className="text-xl font-semibold text-[#d4af37] mt-1">1xBet</div>
          <div className="text-[10px] text-neutral-500">Fixed target</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono border-b border-white/[0.06] pb-3">
        <div className="flex items-center gap-1">
          {['ALL', '1X2', 'Over', 'BTTS'].map((m) => (
            <button
              key={m}
              onClick={() => setFilterMarket(m)}
              className={`px-3 py-1 rounded-md transition-colors ${
                filterMarket === m
                  ? 'bg-white text-black font-semibold'
                  : 'text-neutral-400 hover:text-white'
              }`}
            >
              {m === 'ALL' ? 'All' : m}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1">
          {['ALL', 'WON', 'LOST'].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`px-3 py-1 rounded-md transition-colors ${
                filterStatus === s
                  ? 'bg-neutral-800 text-white font-medium'
                  : 'text-neutral-500 hover:text-neutral-300'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-white/[0.08] bg-[#09090b]">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#050507] text-neutral-500 uppercase text-[10px] tracking-wider border-b border-white/[0.06]">
            <tr>
              <th className="py-3 px-4">Match</th>
              <th className="py-3 px-3">Date (IST)</th>
              <th className="py-3 px-3">Selection</th>
              <th className="py-3 px-3 text-right">Odds</th>
              <th className="py-3 px-3 text-right">Calibrated</th>
              <th className="py-3 px-3 text-right">EV</th>
              <th className="py-3 px-3 text-center">Status</th>
              <th className="py-3 px-3 text-right">P&L</th>
              <th className="py-3 px-4">Settlement Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04] text-neutral-300">
            {filtered.map((b) => (
              <tr key={b.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3.5 px-4 font-sans">
                  <div className="font-semibold text-white text-[13px]">{b.match}</div>
                  <div className="text-[11px] text-neutral-500">{b.league}</div>
                </td>
                <td className="py-3.5 px-3 text-[11px] text-neutral-400 whitespace-nowrap">
                  {b.predictedAtIST}
                </td>
                <td className="py-3.5 px-3">
                  <div className="text-white font-medium">{b.selection}</div>
                  <div className="text-[10px] text-neutral-500">{b.market}</div>
                </td>
                <td className="py-3.5 px-3 text-right font-medium text-[#d4af37]">
                  {b.odds.toFixed(2)}
                </td>
                <td className="py-3.5 px-3 text-right text-neutral-300">
                  {(b.calibProb * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-right text-emerald-400 font-medium">
                  +{(b.ev * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-center whitespace-nowrap">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium tracking-wide ${
                      b.status === 'WON'
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                        : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                    }`}
                  >
                    {b.status}
                  </span>
                </td>
                <td
                  className={`py-3.5 px-3 text-right font-semibold whitespace-nowrap ${
                    (b.pl || 0) > 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {b.pl !== null ? (b.pl > 0 ? `+${b.pl.toFixed(2)}` : b.pl.toFixed(2)) : '—'}
                </td>
                <td className="py-3.5 px-4 text-[11px] text-neutral-500 font-sans max-w-xs">
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
