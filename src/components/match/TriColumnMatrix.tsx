'use client'

import React from 'react'
import DataFreshnessBadge from '../ui/terminal/DataFreshnessBadge'

export interface ModelIntelligenceData {
  selection: string
  calibratedProb: number
  ci95: [number, number]
  rawSimulationCount: number
  simulationStdError: number
  modelVersion: string
  calibrationTransform: string
  decision: 'CANDIDATE' | 'NO_BET'
  stakingAdvisory: string
  noBetCode?: string
}

export interface MarketExecutionData {
  bookmaker: string
  homeOdds: number | null
  drawOdds: number | null
  awayOdds: number | null
  over25Odds?: number | null
  under25Odds?: number | null
  overround: number | null
  targetSelectionOdds: number | null
  impliedProb: number | null
  deviggedProb: number | null
  valueEdge: number | null
  expectedValue: number | null
  oddsFreshnessTimestamp?: string
  status: 'ACTIVE' | 'UNAVAILABLE' | 'SUSPENDED'
}

export interface LiveStateData {
  minute: number
  status: string
  homeScore: number
  awayScore: number
  homeXg: number
  awayXg: number
  homeShots: number
  awayShots: number
  homeShotsOnTarget: number
  awayShotsOnTarget: number
  homeCorners: number
  awayCorners: number
  homeFouls: number
  awayFouls: number
  homeYellowCards: number
  awayYellowCards: number
  homeRedCards: number
  awayRedCards: number
  homePossession?: number
  awayPossession?: number
  stateFreshnessTimestamp?: string
}

export interface TriColumnMatrixProps {
  model: ModelIntelligenceData
  market: MarketExecutionData
  liveState: LiveStateData
  homeTeamName: string
  awayTeamName: string
  className?: string
}

export default function TriColumnMatrix({
  model,
  market,
  liveState,
  homeTeamName,
  awayTeamName,
  className = '',
}: TriColumnMatrixProps) {
  const isLive = ['1H', '2H', 'HT', 'ET', 'LIVE'].includes(liveState.status)
  const isCandidate = model.decision === 'CANDIDATE'
  const hasOdds = market.status === 'ACTIVE' && market.targetSelectionOdds !== null

  return (
    <div
      className={`bg-[#0F172A] border border-[#1E293B] rounded-xl overflow-hidden shadow-sm ${className}`}
    >
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[#0B0F17] border-b border-[#1E293B] text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#3B82F6]" />
          <span className="font-semibold text-[#F8FAFC]">
            Institutional Tri-Column Intelligence Matrix
          </span>
          <span className="text-[#64748B]">·</span>
          <span className="text-[#94A3B8]">Sofascore Architecture</span>
        </div>

        <div className="flex items-center gap-3">
          <DataFreshnessBadge
            timestamp={liveState.stateFreshnessTimestamp}
            label="Live State"
            staleThresholdSeconds={120}
          />
          <DataFreshnessBadge
            timestamp={market.oddsFreshnessTimestamp}
            label="1xBet Odds"
            staleThresholdSeconds={900}
          />
        </div>
      </div>

      {/* Tri-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-[#1E293B] text-xs font-mono">
        {/* COLUMN 1: MODEL INTELLIGENCE */}
        <div className="p-4 sm:p-5 flex flex-col justify-between space-y-4 bg-[#0F172A]">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#10B981]" />
                <span className="font-semibold text-xs text-[#F8FAFC] uppercase tracking-wider">
                  1. Model Intelligence
                </span>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                  isCandidate
                    ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30'
                    : 'bg-[#64748B]/15 text-[#94A3B8] border-[#64748B]/30'
                }`}
              >
                {model.decision}
              </span>
            </div>

            <div className="space-y-2.5">
              <div className="flex justify-between items-baseline">
                <span className="text-[#94A3B8]">Target Selection:</span>
                <span className="font-semibold text-[#F8FAFC] text-right">
                  {model.selection}
                </span>
              </div>

              <div className="flex justify-between items-baseline">
                <span className="text-[#94A3B8]">Calibrated Win Prob:</span>
                <span className="font-bold text-sm text-[#F8FAFC]">
                  {(model.calibratedProb * 100).toFixed(1)}%
                </span>
              </div>

              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-[#64748B]">95% Credible Interval:</span>
                <span className="text-[#94A3B8]">
                  [{(model.ci95[0] * 100).toFixed(1)}% – {(model.ci95[1] * 100).toFixed(1)}%]
                </span>
              </div>

              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-[#64748B]">Monte Carlo Paths:</span>
                <span className="text-[#F8FAFC]">
                  {model.rawSimulationCount.toLocaleString()} paths
                </span>
              </div>

              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-[#64748B]">Simulation Error:</span>
                <span className="text-[#10B981]">
                  ±{model.simulationStdError.toFixed(4)}
                </span>
              </div>

              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-[#64748B]">Model Architecture:</span>
                <span className="text-[#94A3B8]">{model.modelVersion}</span>
              </div>

              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-[#64748B]">Calibration Type:</span>
                <span className="text-[#94A3B8]">{model.calibrationTransform}</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#1E293B] space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#64748B]">Staking Advisory:</span>
              <span className="font-bold text-[#F8FAFC]">{model.stakingAdvisory}</span>
            </div>
            {model.noBetCode && !isCandidate && (
              <div className="text-[10px] text-[#F59E0B] bg-[#1E293B]/60 px-2 py-1 rounded border border-[#78350F]/40 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
                <span>Gate Code: {model.noBetCode}</span>
              </div>
            )}
          </div>
        </div>

        {/* COLUMN 2: 1xBET EXECUTION MARKET */}
        <div className="p-4 sm:p-5 flex flex-col justify-between space-y-4 bg-[#0B0F17]/50">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#D4AF37]" />
                <span className="font-semibold text-xs text-[#F8FAFC] uppercase tracking-wider">
                  2. 1xBet Market (Execution)
                </span>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  hasOdds
                    ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30 font-semibold'
                    : 'bg-[#64748B]/15 text-[#94A3B8] border-[#64748B]/30'
                }`}
              >
                {market.status === 'ACTIVE' ? 'Verified Feed' : 'Odds Unavailable'}
              </span>
            </div>

            {hasOdds ? (
              <div className="space-y-2.5">
                {/* 1X2 Odds row */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 rounded bg-[#0F172A] border border-[#1E293B]">
                    <div className="text-[10px] text-[#64748B]">1 (Home)</div>
                    <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                      {market.homeOdds?.toFixed(2) ?? '—'}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-[#0F172A] border border-[#1E293B]">
                    <div className="text-[10px] text-[#64748B]">X (Draw)</div>
                    <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                      {market.drawOdds?.toFixed(2) ?? '—'}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-[#0F172A] border border-[#1E293B]">
                    <div className="text-[10px] text-[#64748B]">2 (Away)</div>
                    <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                      {market.awayOdds?.toFixed(2) ?? '—'}
                    </div>
                  </div>
                </div>

                <div className="flex justify-between items-baseline pt-2">
                  <span className="text-[#94A3B8]">Target Execution Price:</span>
                  <span className="font-bold text-sm text-[#D4AF37]">
                    {market.targetSelectionOdds?.toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between items-baseline text-[11px]">
                  <span className="text-[#64748B]">Implied Probability:</span>
                  <span className="text-[#94A3B8]">
                    {market.impliedProb ? `${(market.impliedProb * 100).toFixed(1)}%` : '—'}
                  </span>
                </div>

                <div className="flex justify-between items-baseline text-[11px]">
                  <span className="text-[#64748B]">Fair Prob (Shin De-vig):</span>
                  <span className="text-[#F8FAFC]">
                    {market.deviggedProb ? `${(market.deviggedProb * 100).toFixed(1)}%` : '—'}
                  </span>
                </div>

                <div className="flex justify-between items-baseline text-[11px]">
                  <span className="text-[#64748B]">Market Overround:</span>
                  <span className="text-[#94A3B8]">
                    {market.overround ? `${(market.overround * 100).toFixed(1)}%` : '—'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-[#0F172A] border border-[#1E293B] text-center space-y-1">
                <div className="text-xs font-semibold text-[#F8FAFC]">
                  1xBet Prices Currently Unavailable
                </div>
                <p className="text-[11px] text-[#64748B] font-sans">
                  No clearing price found for execution. Model engine abstains until active odds are
                  synced.
                </p>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-[#1E293B] space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#64748B]">Value Edge (vs Shin):</span>
              <span
                className={`font-bold ${
                  (market.valueEdge || 0) > 0 ? 'text-[#10B981]' : 'text-[#64748B]'
                }`}
              >
                {market.valueEdge !== null
                  ? `${market.valueEdge > 0 ? '+' : ''}${market.valueEdge.toFixed(1)} pp`
                  : '—'}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#64748B]">Expected Value (EV):</span>
              <span
                className={`font-bold ${
                  (market.expectedValue || 0) > 0 ? 'text-[#10B981]' : 'text-rose-400'
                }`}
              >
                {market.expectedValue !== null
                  ? `${market.expectedValue > 0 ? '+' : ''}${market.expectedValue.toFixed(1)}%`
                  : '—'}
              </span>
            </div>
          </div>
        </div>

        {/* COLUMN 3: LIVE MATCH STATE */}
        <div className="p-4 sm:p-5 flex flex-col justify-between space-y-4 bg-[#0F172A]">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isLive ? 'bg-[#10B981] animate-pulse' : 'bg-[#64748B]'
                  }`}
                />
                <span className="font-semibold text-xs text-[#F8FAFC] uppercase tracking-wider">
                  3. In-Play Match State
                </span>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                  isLive
                    ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30'
                    : 'bg-[#1E293B] text-[#94A3B8] border-[#334155]'
                }`}
              >
                {isLive ? `Live ${liveState.minute}'` : liveState.status}
              </span>
            </div>

            {/* Scoreboard */}
            <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1E293B] flex items-center justify-between text-center">
              <div className="flex-1 truncate text-left">
                <div className="text-xs font-semibold text-[#F8FAFC] truncate">{homeTeamName}</div>
                <div className="text-[10px] text-[#64748B]">Home</div>
              </div>
              <div className="px-3 text-xl font-bold text-[#D4AF37]">
                {liveState.homeScore} – {liveState.awayScore}
              </div>
              <div className="flex-1 truncate text-right">
                <div className="text-xs font-semibold text-[#F8FAFC] truncate">{awayTeamName}</div>
                <div className="text-[10px] text-[#64748B]">Away</div>
              </div>
            </div>

            {/* In-play match metrics */}
            <div className="space-y-2 text-xs">
              {/* xG Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[11px] text-[#94A3B8]">
                  <span>xG: {liveState.homeXg.toFixed(2)}</span>
                  <span className="text-[#64748B] text-[10px]">Expected Goals</span>
                  <span>xG: {liveState.awayXg.toFixed(2)}</span>
                </div>
                <div className="w-full bg-[#131924] rounded-full h-1.5 flex overflow-hidden">
                  <div
                    className="bg-[#10B981] h-1.5"
                    style={{
                      width: `${
                        (liveState.homeXg /
                          Math.max(0.01, liveState.homeXg + liveState.awayXg)) *
                        100
                      }%`,
                    }}
                  />
                  <div
                    className="bg-[#3B82F6] h-1.5"
                    style={{
                      width: `${
                        (liveState.awayXg /
                          Math.max(0.01, liveState.homeXg + liveState.awayXg)) *
                        100
                      }%`,
                    }}
                  />
                </div>
              </div>

              {/* Shots (On Target) */}
              <div className="flex justify-between items-center text-[11px] pt-1">
                <span className="text-[#F8FAFC]">
                  {liveState.homeShots} ({liveState.homeShotsOnTarget})
                </span>
                <span className="text-[#64748B]">Shots (On Target)</span>
                <span className="text-[#F8FAFC]">
                  {liveState.awayShots} ({liveState.awayShotsOnTarget})
                </span>
              </div>

              {/* Corners */}
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-[#F8FAFC]">{liveState.homeCorners}</span>
                <span className="text-[#64748B]">Corners</span>
                <span className="text-[#F8FAFC]">{liveState.awayCorners}</span>
              </div>

              {/* Disciplinary Cards */}
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-[#F59E0B]">
                  {liveState.homeYellowCards}Y {liveState.homeRedCards > 0 ? `· ${liveState.homeRedCards}R` : ''}
                </span>
                <span className="text-[#64748B]">Cards (Y/R)</span>
                <span className="text-[#F59E0B]">
                  {liveState.awayYellowCards}Y {liveState.awayRedCards > 0 ? `· ${liveState.awayRedCards}R` : ''}
                </span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#1E293B] text-[10px] text-[#64748B] flex items-center justify-between">
            <span>State Synchronizer: Active</span>
            <span>API-Football In-Play Feed</span>
          </div>
        </div>
      </div>
    </div>
  )
}
