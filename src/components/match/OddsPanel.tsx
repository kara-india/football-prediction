'use client'

import React from 'react'
import TerminalCard from '../ui/terminal/TerminalCard'
import DataFreshnessBadge from '../ui/terminal/DataFreshnessBadge'
import { MarketExecutionData } from './TriColumnMatrix'

export interface OddsPanelProps {
  market?: MarketExecutionData
  className?: string
}

export default function OddsPanel({ market, className = '' }: OddsPanelProps) {
  const hasOdds = market && market.status === 'ACTIVE' && market.homeOdds !== null

  return (
    <TerminalCard
      title="1xBet Target Market & Pricing"
      subtitle="Execution clearing prices with Shin margin de-vigging and overround metrics"
      badge={
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
            hasOdds
              ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
              : 'bg-[#64748B]/15 text-[#94A3B8] border border-[#64748B]/30'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${hasOdds ? 'bg-[#10B981]' : 'bg-[#64748B]'}`} />
          {hasOdds ? '1xBet Verified Feed' : '1xBet Odds Unavailable'}
        </span>
      }
      actions={
        <DataFreshnessBadge
          timestamp={market?.oddsFreshnessTimestamp}
          label="Odds"
          staleThresholdSeconds={900}
        />
      }
      className={className}
      padding="none"
    >
      <div className="p-4 sm:p-5 space-y-4 text-xs font-mono">
        {hasOdds ? (
          <>
            {/* 1X2 Match Winner Grid */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-[#94A3B8]">
                <span className="font-semibold text-[#F8FAFC]">1X2 Match Result</span>
                <span className="text-[#64748B]">Overround: {market.overround !== null ? `${(market.overround * 100).toFixed(1)}%` : '—'}</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-[#0B0F17] border border-[#1E293B] hover:border-[#D4AF37]/50 rounded-lg p-2.5 transition-colors">
                  <div className="text-[10px] text-[#64748B]">1 (Home)</div>
                  <div className="text-base font-bold text-[#D4AF37] mt-0.5">
                    {market.homeOdds?.toFixed(2) ?? '—'}
                  </div>
                  <div className="text-[10px] text-[#94A3B8] mt-0.5">
                    {market.homeOdds ? `${(100 / market.homeOdds).toFixed(1)}% Implied` : '—'}
                  </div>
                </div>

                <div className="bg-[#0B0F17] border border-[#1E293B] hover:border-[#D4AF37]/50 rounded-lg p-2.5 transition-colors">
                  <div className="text-[10px] text-[#64748B]">X (Draw)</div>
                  <div className="text-base font-bold text-[#D4AF37] mt-0.5">
                    {market.drawOdds?.toFixed(2) ?? '—'}
                  </div>
                  <div className="text-[10px] text-[#94A3B8] mt-0.5">
                    {market.drawOdds ? `${(100 / market.drawOdds).toFixed(1)}% Implied` : '—'}
                  </div>
                </div>

                <div className="bg-[#0B0F17] border border-[#1E293B] hover:border-[#D4AF37]/50 rounded-lg p-2.5 transition-colors">
                  <div className="text-[10px] text-[#64748B]">2 (Away)</div>
                  <div className="text-base font-bold text-[#D4AF37] mt-0.5">
                    {market.awayOdds?.toFixed(2) ?? '—'}
                  </div>
                  <div className="text-[10px] text-[#94A3B8] mt-0.5">
                    {market.awayOdds ? `${(100 / market.awayOdds).toFixed(1)}% Implied` : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Over / Under Goals */}
            <div className="pt-2 border-t border-[#1E293B] space-y-2">
              <div className="text-[11px] font-semibold text-[#F8FAFC]">
                Alternative Markets (Total Goals 2.5)
              </div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#64748B]">Over 2.5 Goals</div>
                  <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                    {market.over25Odds?.toFixed(2) ?? '—'}
                  </div>
                </div>
                <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
                  <div className="text-[10px] text-[#64748B]">Under 2.5 Goals</div>
                  <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                    {market.under25Odds?.toFixed(2) ?? '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* De-vigged Shin Fair Metrics */}
            <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1E293B] space-y-1 text-[11px]">
              <div className="text-[#94A3B8] font-semibold">Shin De-Vigging Methodology</div>
              <p className="text-[#64748B] text-[10px] leading-relaxed font-sans">
                Removes bookmaker overround by estimating the proportion of insider/informed action (z parameter), yielding unbiased fair market probabilities.
              </p>
            </div>
          </>
        ) : (
          <div className="p-8 text-center text-xs font-mono text-[#64748B] space-y-2">
            <p className="text-[#F8FAFC] font-semibold">1xBet Fixed Odds Unavailable</p>
            <p className="max-w-md mx-auto text-[11px]">
              No active clearing prices detected. In accordance with zero-fake-data policy, no synthetic odds are displayed.
            </p>
          </div>
        )}
      </div>
    </TerminalCard>
  )
}
