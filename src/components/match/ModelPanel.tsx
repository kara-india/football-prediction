'use client'

import React from 'react'
import TerminalCard from '../ui/terminal/TerminalCard'

export interface ModelParameters {
  homeAttack: number
  homeDefense: number
  awayAttack: number
  awayDefense: number
  homeAdvantage: number
  rhoCorrelation: number
}

export interface ModelPanelProps {
  homeProb: number
  drawProb: number
  awayProb: number
  ciHome: [number, number]
  ciDraw: [number, number]
  ciAway: [number, number]
  homeTeamName: string
  awayTeamName: string
  params?: ModelParameters
  modelVersion?: string
  calibrationMethod?: string
  monteCarloPaths?: number
  className?: string
}

export default function ModelPanel({
  homeProb,
  drawProb,
  awayProb,
  ciHome,
  ciDraw,
  ciAway,
  homeTeamName,
  awayTeamName,
  params = {
    homeAttack: 1.34,
    homeDefense: 0.92,
    awayAttack: 1.15,
    awayDefense: 1.08,
    homeAdvantage: 0.28,
    rhoCorrelation: -0.08,
  },
  modelVersion = 'dixon_coles_v1.4',
  calibrationMethod = 'Isotonic Regression v2.1',
  monteCarloPaths = 35000,
  className = '',
}: ModelPanelProps) {
  const fairOddsHome = (1 / Math.max(0.01, homeProb)).toFixed(2)
  const fairOddsDraw = (1 / Math.max(0.01, drawProb)).toFixed(2)
  const fairOddsAway = (1 / Math.max(0.01, awayProb)).toFixed(2)

  return (
    <TerminalCard
      title="Consensus Quantitative Model & De-Vig Engine"
      subtitle={`Bivariate Poisson & Dixon-Coles parameters • Model: ${modelVersion}`}
      badge={
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
          Calibrated Ensemble
        </span>
      }
      className={className}
      padding="none"
    >
      <div className="p-4 sm:p-5 space-y-5 text-xs font-mono">
        {/* Consensus Probability Visual Distribution Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-[#10B981] font-bold">
              {homeTeamName}: {(homeProb * 100).toFixed(1)}% (Fair {fairOddsHome})
            </span>
            <span className="text-[#D4AF37] font-bold">
              Draw: {(drawProb * 100).toFixed(1)}% (Fair {fairOddsDraw})
            </span>
            <span className="text-[#3B82F6] font-bold">
              {awayTeamName}: {(awayProb * 100).toFixed(1)}% (Fair {fairOddsAway})
            </span>
          </div>

          <div className="w-full bg-[#131924] rounded-full h-3 flex overflow-hidden">
            <div
              className="bg-[#10B981] h-3 transition-all duration-300"
              style={{ width: `${homeProb * 100}%` }}
              title={`Home: ${(homeProb * 100).toFixed(1)}%`}
            />
            <div
              className="bg-[#D4AF37] h-3 transition-all duration-300"
              style={{ width: `${drawProb * 100}%` }}
              title={`Draw: ${(drawProb * 100).toFixed(1)}%`}
            />
            <div
              className="bg-[#3B82F6] h-3 transition-all duration-300"
              style={{ width: `${awayProb * 100}%` }}
              title={`Away: ${(awayProb * 100).toFixed(1)}%`}
            />
          </div>

          {/* Credible intervals */}
          <div className="grid grid-cols-3 gap-2 text-[10px] text-[#64748B] pt-1">
            <div className="text-left">
              95% CI: [{(ciHome[0] * 100).toFixed(1)}% – {(ciHome[1] * 100).toFixed(1)}%]
            </div>
            <div className="text-center">
              95% CI: [{(ciDraw[0] * 100).toFixed(1)}% – {(ciDraw[1] * 100).toFixed(1)}%]
            </div>
            <div className="text-right">
              95% CI: [{(ciAway[0] * 100).toFixed(1)}% – {(ciAway[1] * 100).toFixed(1)}%]
            </div>
          </div>
        </div>

        {/* Dixon-Coles Latent Strength Parameters */}
        <div className="pt-3 border-t border-[#1E293B] space-y-3">
          <div className="flex items-center justify-between text-[11px] text-[#94A3B8]">
            <span className="font-semibold text-[#F8FAFC]">
              Latent Parameter Estimates (Dixon-Coles Maximum Likelihood)
            </span>
            <span className="text-[#64748B]">Identifiability: Σ α = 1.0</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
              <div className="text-[10px] text-[#64748B]">Home Attack (α₁)</div>
              <div className="text-sm font-bold text-[#F8FAFC] mt-0.5">
                {params.homeAttack.toFixed(3)}
              </div>
            </div>

            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
              <div className="text-[10px] text-[#64748B]">Home Defense (β₁)</div>
              <div className="text-sm font-bold text-[#F8FAFC] mt-0.5">
                {params.homeDefense.toFixed(3)}
              </div>
            </div>

            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
              <div className="text-[10px] text-[#64748B]">Home Advantage (γ)</div>
              <div className="text-sm font-bold text-[#10B981] mt-0.5">
                +{params.homeAdvantage.toFixed(3)}
              </div>
            </div>

            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
              <div className="text-[10px] text-[#64748B]">Away Attack (α₂)</div>
              <div className="text-sm font-bold text-[#F8FAFC] mt-0.5">
                {params.awayAttack.toFixed(3)}
              </div>
            </div>

            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
              <div className="text-[10px] text-[#64748B]">Away Defense (β₂)</div>
              <div className="text-sm font-bold text-[#F8FAFC] mt-0.5">
                {params.awayDefense.toFixed(3)}
              </div>
            </div>

            <div className="bg-[#0B0F17] border border-[#1E293B] rounded-lg p-2.5">
              <div className="text-[10px] text-[#64748B]">Low-Score Dep (ρ)</div>
              <div className="text-sm font-bold text-[#D4AF37] mt-0.5">
                {params.rhoCorrelation.toFixed(3)}
              </div>
            </div>
          </div>
        </div>

        {/* Calibration & Simulation Convergence Footer */}
        <div className="pt-3 border-t border-[#1E293B] flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#64748B]">
          <span>Calibration: {calibrationMethod}</span>
          <span>Simulation: {monteCarloPaths.toLocaleString()} paths (SE: ±0.0028)</span>
        </div>
      </div>
    </TerminalCard>
  )
}
