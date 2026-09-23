'use client'

import React from 'react'
import TerminalCard from '../ui/terminal/TerminalCard'
import DataFreshnessBadge from '../ui/terminal/DataFreshnessBadge'

export interface ModelTransparencyData {
  selectionName: string
  marketName: string
  matchIdentifier: string
  rawSimProbability: number
  calibratedProbability: number
  ci95Lower: number
  ci95Upper: number
  monteCarloPaths: number
  standardError: number
  modelVersion: string
  calibrationMethod: string
  targetBookmaker: string
  executionPrice: number | null
  deviggedProbability: number | null
  overround: number | null
  valueEdge: number | null // percentage points (e.g. +5.7)
  expectedValue: number | null // e.g. +16.18%
  decision: 'CANDIDATE' | 'NO_BET'
  noBetReasons: string[]
  stateGeneratedAt?: string
  oddsGeneratedAt?: string
  featureSnapshotId?: string
  gitSha?: string
}

export default function ModelTransparencyCard({
  data,
  className = '',
}: {
  data: ModelTransparencyData
  className?: string
}) {
  const isCandidate = data.decision === 'CANDIDATE'
  const hasOdds = data.executionPrice !== null && data.executionPrice > 0

  return (
    <TerminalCard
      title="Quantitative Prediction Derivation & Provenance"
      subtitle={`Decomposition for ${data.selectionName} (${data.marketName}) • Match ID: ${data.matchIdentifier}`}
      badge={
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
            isCandidate
              ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
              : 'bg-[#64748B]/15 text-[#94A3B8] border border-[#64748B]/30'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isCandidate ? 'bg-[#10B981]' : 'bg-[#64748B]'
            }`}
          />
          {isCandidate ? 'CANDIDATE (PASSED GATES)' : 'NO BET (SAFETY GATE ACTIVE)'}
        </span>
      }
      className={className}
      padding="none"
    >
      <div className="divide-y divide-[#1E293B] text-xs font-mono">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-[#1E293B]">
          {/* Calibrated Probability */}
          <div className="bg-[#0F172A] p-3.5 space-y-1">
            <div className="text-[10px] text-[#64748B] uppercase tracking-wider">
              Calibrated Prob
            </div>
            <div className="text-lg font-bold text-[#F8FAFC]">
              {(data.calibratedProbability * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] text-[#94A3B8]">
              95% CI: [{(data.ci95Lower * 100).toFixed(1)}% – {(data.ci95Upper * 100).toFixed(1)}%]
            </div>
          </div>

          {/* 1xBet Target Price */}
          <div className="bg-[#0F172A] p-3.5 space-y-1">
            <div className="text-[10px] text-[#64748B] uppercase tracking-wider">
              1xBet Target Price
            </div>
            <div className="text-lg font-bold text-[#D4AF37]">
              {hasOdds ? data.executionPrice?.toFixed(2) : 'Unavailable'}
            </div>
            <div className="text-[10px] text-[#94A3B8]">
              {data.deviggedProbability
                ? `De-vig: ${(data.deviggedProbability * 100).toFixed(1)}% (Shin)`
                : 'Abstaining on missing odds'}
            </div>
          </div>

          {/* Value Edge */}
          <div className="bg-[#0F172A] p-3.5 space-y-1">
            <div className="text-[10px] text-[#64748B] uppercase tracking-wider">
              Value Edge (Δp)
            </div>
            <div
              className={`text-lg font-bold ${
                (data.valueEdge || 0) > 0 ? 'text-[#10B981]' : 'text-[#64748B]'
              }`}
            >
              {data.valueEdge !== null
                ? `${data.valueEdge > 0 ? '+' : ''}${data.valueEdge.toFixed(1)} pp`
                : '—'}
            </div>
            <div className="text-[10px] text-[#94A3B8]">
              Gate Threshold: ≥ +3.0 pp
            </div>
          </div>

          {/* Expected Value */}
          <div className="bg-[#0F172A] p-3.5 space-y-1">
            <div className="text-[10px] text-[#64748B] uppercase tracking-wider">
              Expected Value (EV)
            </div>
            <div
              className={`text-lg font-bold ${
                (data.expectedValue || 0) > 0 ? 'text-[#10B981]' : 'text-rose-400'
              }`}
            >
              {data.expectedValue !== null
                ? `${data.expectedValue > 0 ? '+' : ''}${data.expectedValue.toFixed(2)}%`
                : '—'}
            </div>
            <div className="text-[10px] text-[#94A3B8]">
              Formula: (p × odds) − 1.0
            </div>
          </div>
        </div>

        {/* Detailed Breakdown Rows */}
        <div className="p-4 sm:p-5 space-y-3">
          <div className="text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider">
            Mathematical Derivation Parameters
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {/* Simulation Specs */}
            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span>Monte Carlo Paths:</span>
                <span className="font-bold text-[#F8FAFC]">
                  {data.monteCarloPaths.toLocaleString()} simulations
                </span>
              </div>
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span>Standard Error (SE):</span>
                <span className="text-[#10B981]">
                  ±{data.standardError.toFixed(4)} (Threshold: ≤ 0.010)
                </span>
              </div>
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span>Raw Simulation Prob:</span>
                <span className="text-[#F8FAFC]">
                  {(data.rawSimProbability * 100).toFixed(2)}%
                </span>
              </div>
            </div>

            {/* Model & Calibration */}
            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span>Model Version:</span>
                <span className="text-[#F8FAFC] font-semibold">{data.modelVersion}</span>
              </div>
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span>Calibration Transform:</span>
                <span className="text-[#F8FAFC]">{data.calibrationMethod}</span>
              </div>
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span>Market Overround Margin:</span>
                <span className="text-[#D4AF37]">
                  {data.overround ? `${(data.overround * 100).toFixed(2)}%` : '—'}
                </span>
              </div>
            </div>
          </div>

          {/* Failure Codes if NO-BET */}
          {!isCandidate && data.noBetReasons.length > 0 && (
            <div className="mt-3 p-3 rounded-lg bg-[#0B0F17] border border-[#334155] space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#F59E0B]">
                <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <span>Active Safety Abstention Gates ({data.noBetReasons.length}):</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {data.noBetReasons.map((code) => (
                  <span
                    key={code}
                    className="px-2 py-0.5 rounded bg-[#1E293B] text-[10px] font-mono font-semibold text-[#FCD34D] border border-[#78350F]/60"
                  >
                    {code}
                  </span>
                ))}
              </div>
              <p className="text-[11px] text-[#94A3B8] font-sans">
                Predictive engine abstains when model probability does not clear strict edge,
                freshness, or lineup validation gates. Zero forced candidates.
              </p>
            </div>
          )}

          {/* Provenance & Audit Footer */}
          <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-[11px] text-[#64748B]">
            <div className="flex items-center gap-3">
              <span>Data Freshness:</span>
              <DataFreshnessBadge
                timestamp={data.stateGeneratedAt}
                label="State"
                staleThresholdSeconds={120}
              />
              <DataFreshnessBadge
                timestamp={data.oddsGeneratedAt}
                label="Odds"
                staleThresholdSeconds={900}
              />
            </div>
            <div className="flex items-center gap-2">
              {data.gitSha && <span>SHA: {data.gitSha.substring(0, 7)}</span>}
              {data.featureSnapshotId && <span>Snap: {data.featureSnapshotId}</span>}
            </div>
          </div>
        </div>
      </div>
    </TerminalCard>
  )
}
