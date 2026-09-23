'use client'

import React from 'react'
import TerminalCard from '../ui/terminal/TerminalCard'

export interface MarketRow {
  id: string
  outcome: string
  market: string
  odds1xBet: number | null
  impliedProb: number | null
  deviggedProb: number | null
  modelProb: number
  edge: number | null // percentage points
  ev: number | null // %
  decisionCode: string
  action: 'CANDIDATE' | 'NO_BET'
  stakingAdvisory?: string
}

export interface MarketTableProps {
  rows: MarketRow[]
  className?: string
}

export default function MarketTable({ rows, className = '' }: MarketTableProps) {
  return (
    <TerminalCard
      title="Institutional Market Matrix & Analytical Derivations"
      subtitle="Exhaustive evaluation of all market lines against 1xBet clearing prices with NO-BET taxonomy"
      badge={
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono text-[#D4AF37] bg-[#D4AF37]/10 border border-[#D4AF37]/30 font-semibold">
          1xBet Execution Matrix
        </span>
      }
      className={className}
      padding="none"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#0B0F17] text-[#64748B] uppercase text-[10px] tracking-wider border-b border-[#1E293B]">
            <tr>
              <th className="py-3 px-4">Market Outcome</th>
              <th className="py-3 px-3">Market</th>
              <th className="py-3 px-3 text-right">1xBet Price</th>
              <th className="py-3 px-3 text-right">Implied</th>
              <th className="py-3 px-3 text-right">Fair (Shin)</th>
              <th className="py-3 px-3 text-right">Calibrated</th>
              <th className="py-3 px-3 text-right">Edge (Δp)</th>
              <th className="py-3 px-3 text-right">EV</th>
              <th className="py-3 px-3">Gate Reason Code</th>
              <th className="py-3 px-4 text-center">Decision</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E293B] text-[#94A3B8]">
            {rows.map((r) => {
              const isCandidate = r.action === 'CANDIDATE'
              const hasOdds = r.odds1xBet !== null && r.odds1xBet > 0

              return (
                <tr
                  key={r.id}
                  className={`hover:bg-[#1E293B]/40 transition-colors ${
                    isCandidate ? 'bg-[#10B981]/5' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-semibold text-[#F8FAFC]">
                    {r.outcome}
                  </td>
                  <td className="py-3 px-3 text-[11px] text-[#64748B]">{r.market}</td>
                  <td className="py-3 px-3 text-right font-bold text-[#D4AF37]">
                    {hasOdds ? r.odds1xBet?.toFixed(2) : '—'}
                  </td>
                  <td className="py-3 px-3 text-right text-[#64748B]">
                    {r.impliedProb ? `${(r.impliedProb * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-3 px-3 text-right text-[#F8FAFC]">
                    {r.deviggedProb ? `${(r.deviggedProb * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-3 px-3 text-right font-semibold text-[#F8FAFC]">
                    {(r.modelProb * 100).toFixed(1)}%
                  </td>
                  <td
                    className={`py-3 px-3 text-right font-bold ${
                      (r.edge || 0) > 0 ? 'text-[#10B981]' : 'text-[#64748B]'
                    }`}
                  >
                    {r.edge !== null ? `${r.edge > 0 ? '+' : ''}${r.edge.toFixed(1)} pp` : '—'}
                  </td>
                  <td
                    className={`py-3 px-3 text-right font-bold ${
                      (r.ev || 0) > 0 ? 'text-[#10B981]' : 'text-rose-400'
                    }`}
                  >
                    {r.ev !== null ? `${r.ev > 0 ? '+' : ''}${r.ev.toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-3 px-3 text-[10px]">
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded border ${
                        isCandidate
                          ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30 font-semibold'
                          : 'bg-[#1E293B] text-[#94A3B8] border-[#334155]'
                      }`}
                    >
                      {r.decisionCode}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center whitespace-nowrap">
                    <span
                      className={`inline-block px-2.5 py-1 rounded text-[10px] font-bold tracking-wide border ${
                        isCandidate
                          ? 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/40'
                          : 'bg-[#1E293B] text-[#64748B] border-[#334155]'
                      }`}
                    >
                      {r.action === 'CANDIDATE' ? 'CANDIDATE' : 'NO BET'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="p-3 bg-[#0B0F17] border-t border-[#1E293B] text-[10px] text-[#64748B] flex flex-wrap items-center justify-between gap-2">
        <span>Execution Target: 1xBet Fixed Odds (Bookmaker ID: 6)</span>
        <span>Safety Gate Invariant: Min Edge +3.0 pp • Expected Value &gt; 0</span>
      </div>
    </TerminalCard>
  )
}
