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
    notes: 'Final: 2-1. Pre-match lineup confirmed 4-2-3-1.'
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
    notes: 'Final: 2-0. Expected goals were 2.85 (Variance).'
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
    notes: 'Final: 2-0. Starters confirmed with Mbappe debut.'
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
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide bg-gradient-to-r from-amber-500/20 to-emerald-500/20 text-amber-300 border border-amber-500/40 font-mono">
            AUDITABLE PAPER RECORD
          </span>
          <span className="text-xs text-emerald-400 font-mono">1xBet Fixed Execution Prices</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-1.5 tracking-tight flex items-center gap-2">
          Paper Bet Ledger & Settlement History
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          Every qualifying bet recommendation is automatically logged at the exact 1xBet price available at prediction time.
          All predictions are strictly graded post-match with Brier score, log-loss contribution, and Closing Line Value (CLV).
        </p>
      </div>

      {/* Metrics Summary Strip - Gold & Green */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-[#0b1315] border border-emerald-950/90 rounded-2xl p-4 text-center shadow-lg">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Logged Bets</div>
          <div className="text-2xl font-black text-white mt-1">{SAMPLE_BETS.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">{settled.length} settled</div>
        </div>

        <div className="bg-[#0b1315] border border-emerald-500/30 rounded-2xl p-4 text-center shadow-lg">
          <div className="text-[11px] text-emerald-400 uppercase font-semibold">Win Rate</div>
          <div className="text-2xl font-black text-emerald-300 mt-1">{winRate.toFixed(1)}%</div>
          <div className="text-[10px] text-emerald-500/80 mt-0.5">{won} W / {settled.length - won} L</div>
        </div>

        <div className="bg-[#0b1315] border border-amber-500/30 rounded-2xl p-4 text-center shadow-lg">
          <div className="text-[11px] text-amber-400 uppercase font-semibold">Total P&L</div>
          <div className={`text-2xl font-black mt-1 ${totalPL >= 0 ? 'text-amber-300' : 'text-rose-400'}`}>
            {totalPL >= 0 ? `+${totalPL.toFixed(2)}` : totalPL.toFixed(2)} U
          </div>
          <div className="text-[10px] text-amber-500/70 mt-0.5">1.0 U flat stake</div>
        </div>

        <div className="bg-[#0b1315] border border-emerald-500/30 rounded-2xl p-4 text-center shadow-lg">
          <div className="text-[11px] text-emerald-400 uppercase font-semibold">Realized ROI</div>
          <div className={`text-2xl font-black mt-1 ${roi >= 0 ? 'text-emerald-300' : 'text-rose-400'}`}>
            {roi >= 0 ? `+${roi.toFixed(1)}%` : `${roi.toFixed(1)}%`}
          </div>
          <div className="text-[10px] text-emerald-500/80 mt-0.5">yield / stake</div>
        </div>

        <div className="bg-[#0b1315] border border-emerald-950/90 rounded-2xl p-4 text-center shadow-lg">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Avg CLV</div>
          <div className="text-2xl font-black text-teal-300 mt-1">+{avgCLV.toFixed(1)}%</div>
          <div className="text-[10px] text-slate-500 mt-0.5">beat closing line</div>
        </div>

        <div className="bg-[#0b1315] border border-amber-500/30 rounded-2xl p-4 text-center shadow-lg">
          <div className="text-[11px] text-amber-400 uppercase font-semibold">Target Bookie</div>
          <div className="text-2xl font-black text-amber-300 mt-1 flex items-center justify-center gap-1">
            <span className="text-sm">⚡</span> 1xBet
          </div>
          <div className="text-[10px] text-emerald-400 mt-0.5">● verified feed</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-950/80 pb-3 text-xs font-mono">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400 font-medium mr-1">Market:</span>
          {['ALL', '1X2', 'Over', 'BTTS'].map((m) => (
            <button
              key={m}
              onClick={() => setFilterMarket(m)}
              className={`px-3 py-1 rounded-lg transition font-bold ${
                filterMarket === m
                  ? 'bg-gradient-to-r from-amber-500 to-yellow-600 text-slate-950 shadow-sm'
                  : 'bg-[#10191c] text-slate-300 hover:text-white border border-emerald-950'
              }`}
            >
              {m === 'ALL' ? 'All Markets' : m}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-400 font-medium mr-1">Outcome:</span>
          {['ALL', 'WON', 'LOST', 'OPEN'].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`px-3 py-1 rounded-lg transition font-bold ${
                filterStatus === s
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                  : 'bg-[#10191c] text-slate-300 hover:text-white border border-emerald-950'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-2xl border border-emerald-950/90 bg-[#090f11] shadow-2xl">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#050809] text-slate-400 uppercase text-[10px] font-semibold border-b border-emerald-950">
            <tr>
              <th className="py-3 px-4">Bet ID & Match</th>
              <th className="py-3 px-3">Predicted (IST)</th>
              <th className="py-3 px-3">Market & Pick</th>
              <th className="py-3 px-3 text-right">1xBet Odds</th>
              <th className="py-3 px-3 text-right">Model %</th>
              <th className="py-3 px-3 text-right">Calib %</th>
              <th className="py-3 px-3 text-right">EV %</th>
              <th className="py-3 px-3 text-center">Status</th>
              <th className="py-3 px-3 text-right">P&L (U)</th>
              <th className="py-3 px-4">Settlement Audit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-emerald-950/60 text-slate-200">
            {filtered.map((b) => (
              <tr key={b.id} className="hover:bg-[#0e171a]/80 transition">
                <td className="py-3.5 px-4 font-sans">
                  <div className="font-mono text-[10px] text-amber-400/80 font-bold">{b.id}</div>
                  <div className="font-bold text-white text-sm">{b.match}</div>
                  <div className="text-[11px] text-slate-400">{b.league}</div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-[11px] text-slate-300">
                  {b.predictedAtIST}
                </td>
                <td className="py-3.5 px-3 font-sans">
                  <span className="font-medium text-slate-300">{b.market}</span>
                  <div className="text-[11px] font-extrabold text-amber-300 font-mono">{b.selection}</div>
                </td>
                <td className="py-3.5 px-3 text-right font-black text-amber-300 text-sm">
                  {b.odds.toFixed(2)}
                </td>
                <td className="py-3.5 px-3 text-right text-slate-300">
                  {(b.modelProb * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-right font-bold text-slate-100">
                  {(b.calibProb * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-right font-black text-emerald-400">
                  +{(b.ev * 100).toFixed(1)}%
                </td>
                <td className="py-3.5 px-3 text-center whitespace-nowrap">
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded-lg text-[10px] font-black tracking-wider border ${
                      b.status === 'WON'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-600 shadow-[0_0_8px_rgba(16,185,129,0.25)]'
                        : b.status === 'LOST'
                        ? 'bg-rose-950 text-rose-300 border-rose-800'
                        : 'bg-blue-950 text-blue-300 border-blue-800'
                    }`}
                  >
                    {b.status}
                  </span>
                </td>
                <td
                  className={`py-3.5 px-3 text-right font-black whitespace-nowrap text-sm ${
                    (b.pl || 0) > 0 ? 'text-emerald-400' : (b.pl || 0) < 0 ? 'text-rose-400' : 'text-slate-400'
                  }`}
                >
                  {b.pl !== null ? (b.pl > 0 ? `+${b.pl.toFixed(2)}` : b.pl.toFixed(2)) : '-'}
                </td>
                <td className="py-3.5 px-4 text-[11px] text-slate-400 max-w-xs font-sans">
                  {b.notes}
                  <div className="text-[10px] font-mono text-teal-400 mt-0.5 font-bold">
                    CLV: +{(b.clv * 100).toFixed(1)}%
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
