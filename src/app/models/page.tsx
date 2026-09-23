'use client'

import React, { useState } from 'react'
import TerminalCard from '@/components/ui/terminal/TerminalCard'

interface ModelCandidate {
  id: string
  name: string
  type: string
  status: 'ACTIVE_CHAMPION' | 'SHADOW_CHALLENGER' | 'EVALUATING' | 'RETIRED'
  brierScore: number
  logLoss: number
  ecePercent: number // Expected Calibration Error
  clvPercent: number // Closing line value beat %
  paperRoiPercent: number
  sampleMatches: number
  lastTrained: string
  calibrationTransform: string
}

interface LivMetric {
  competition: string
  t48Brier: number
  t60mBrier: number
  brierImprovement: number // percentage
  accuracyGain: number // percentage points
  sampleCount: number
}

interface ErrorCategoryStat {
  code: string
  name: string
  percentage: number
  description: string
  remedyAction: string
}

const MODELS: ModelCandidate[] = [
  {
    id: 'm-champ-v14',
    name: 'dixon_coles_v1.4_isotonic',
    type: 'Bivariate Poisson with low-score rho + Isotonic Calibration',
    status: 'ACTIVE_CHAMPION',
    brierScore: 0.1782,
    logLoss: 0.884,
    ecePercent: 2.1,
    clvPercent: 3.42,
    paperRoiPercent: 8.4,
    sampleMatches: 4280,
    lastTrained: '18 Sep 2026',
    calibrationTransform: 'Isotonic Regression v2.1',
  },
  {
    id: 'm-chal-rl2',
    name: 'poisson_contextual_bandit_v2',
    type: 'Reinforcement Learning Policy with Inverse Propensity Scoring',
    status: 'SHADOW_CHALLENGER',
    brierScore: 0.1769,
    logLoss: 0.879,
    ecePercent: 1.9,
    clvPercent: 3.88,
    paperRoiPercent: 9.8,
    sampleMatches: 1820,
    lastTrained: '22 Sep 2026',
    calibrationTransform: 'Platt Scaling (Calibrated)',
  },
  {
    id: 'm-chal-dnn1',
    name: 'xg_hazard_dnn_v1',
    type: 'Deep Neural Hazard Network with in-play event conditioning',
    status: 'EVALUATING',
    brierScore: 0.1812,
    logLoss: 0.899,
    ecePercent: 2.8,
    clvPercent: 2.65,
    paperRoiPercent: 5.2,
    sampleMatches: 940,
    lastTrained: '20 Sep 2026',
    calibrationTransform: 'Beta Calibration',
  },
  {
    id: 'm-base-p10',
    name: 'uncalibrated_poisson_v1.0',
    type: 'Uncalibrated baseline Poisson without lineup adjustments',
    status: 'RETIRED',
    brierScore: 0.2045,
    logLoss: 0.985,
    ecePercent: 6.4,
    clvPercent: 0.42,
    paperRoiPercent: -3.8,
    sampleMatches: 7230,
    lastTrained: 'Baseline',
    calibrationTransform: 'None (Raw)',
  },
]

const LIV_DATA: LivMetric[] = [
  {
    competition: 'Premier League',
    t48Brier: 0.1942,
    t60mBrier: 0.1764,
    brierImprovement: 9.2,
    accuracyGain: 4.6,
    sampleCount: 380,
  },
  {
    competition: 'UEFA Champions League',
    t48Brier: 0.1985,
    t60mBrier: 0.1741,
    brierImprovement: 12.3,
    accuracyGain: 5.8,
    sampleCount: 125,
  },
  {
    competition: 'La Liga',
    t48Brier: 0.1895,
    t60mBrier: 0.1752,
    brierImprovement: 7.5,
    accuracyGain: 3.9,
    sampleCount: 380,
  },
  {
    competition: 'Serie A',
    t48Brier: 0.1924,
    t60mBrier: 0.1778,
    brierImprovement: 7.6,
    accuracyGain: 3.7,
    sampleCount: 380,
  },
  {
    competition: 'Bundesliga',
    t48Brier: 0.1998,
    t60mBrier: 0.1812,
    brierImprovement: 9.3,
    accuracyGain: 4.8,
    sampleCount: 306,
  },
]

const ERROR_TAXONOMY: ErrorCategoryStat[] = [
  {
    code: 'RANDOM_VARIANCE',
    name: 'Unavoidable Random Variance',
    percentage: 34,
    description: 'Expected stochastic outcomes within calibrated probabilistic boundaries (e.g. 70% event failing 30% of the time).',
    remedyAction: 'Preserve model priors; verify Brier calibration remains unskewed.',
  },
  {
    code: 'TEAM_STRENGTH_MISS',
    name: 'Team Strength Under/Over-Estimation',
    percentage: 14,
    description: 'EWMA team attack/defense ratings lagged sudden tactical or psychological form shift.',
    remedyAction: 'Increase decay discount parameter λ in EWMA weight computation.',
  },
  {
    code: 'TACTICAL_MISMATCH',
    name: 'Managerial & Formation Tactical Asymmetry',
    percentage: 12,
    description: 'Direct head-to-head structural matchup (e.g. high-press 4-3-3 against low-block 5-4-1).',
    remedyAction: 'Incorporate formation matchup coefficient in bivariate Poisson lambda.',
  },
  {
    code: 'PLAYER_PROJECTION_ERROR',
    name: 'Key Player Performance Deviation',
    percentage: 10,
    description: 'Specific starter performed drastically outside 95% minutes/contribution projection.',
    remedyAction: 'Refine player availability and injury return discount factor.',
  },
  {
    code: 'LIVE_STATE_ERROR',
    name: 'In-Play Hazard State Latency',
    percentage: 9,
    description: 'In-play probability update delayed by upstream provider socket latency > 30s.',
    remedyAction: 'Automated circuit breaker attached to `stale_state` threshold.',
  },
  {
    code: 'ODDS_STALENESS',
    name: 'Market Price Drift / Stale Tick',
    percentage: 6,
    description: '1xBet price shifted after snapshot without timely refresh.',
    remedyAction: 'Enforce pre-match odds staleness timeout to strictly 900 seconds.',
  },
  {
    code: 'LINEUP_MISASSESSMENT',
    name: 'Late Team Sheet / Positional Role Shift',
    percentage: 5,
    description: 'Starter lined up in uncharacteristic inverted position or late warmup injury.',
    remedyAction: 'T-60m Lineup Gate re-simulation with official verified sheet.',
  },
  {
    code: 'CALIBRATION_ERROR',
    name: 'Bin Reliability Residual',
    percentage: 4,
    description: 'Residual error in extreme odds brackets (> 5.0 or < 1.30).',
    remedyAction: 'Re-fit Isotonic Regression curve with minimum bin mass constraint.',
  },
  {
    code: 'SOURCE_CONFLICT',
    name: 'Provider Discrepancy',
    percentage: 3,
    description: 'Mismatch between event reporting sources (e.g. shot vs pass classification).',
    remedyAction: 'Canonical normalizer rejects unconfirmed conflicting records.',
  },
  {
    code: 'DATA_MISSING',
    name: 'Upstream Incomplete Telemetry',
    percentage: 2,
    description: 'Missing xG or tracking metrics for secondary cup competitions.',
    remedyAction: 'Immediate NO-BET abstention on `DATA_MISSING`.',
  },
  {
    code: 'PARAMETER_DRIFT',
    name: 'Non-Stationary League Dynamics',
    percentage: 1,
    description: 'Rule changes or macro changes (e.g. extended added time mandates).',
    remedyAction: 'Walk-forward rolling training window with seasonal boundary adjustment.',
  },
]

export default function ModelsPage() {
  const [activeTab, setActiveTab] = useState<'matrix' | 'liv' | 'taxonomy' | 'abstention'>('matrix')

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#94A3B8] bg-[#0F172A] border border-[#1E293B]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
            <span>Active Champion: dixon_coles_v1.4_isotonic</span>
            <span className="text-[#64748B]">·</span>
            <span className="text-[#D4AF37]">Continual Learning Governance</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F8FAFC]">
            Model Improvement & Quantitative Telemetry
          </h1>

          <p className="text-xs sm:text-sm text-[#94A3B8] max-w-3xl leading-relaxed">
            Live Champion vs Challenger comparison matrix, Lineup Information Value (LIV) telemetry,
            and canonical 11-category causal error decomposition. Strict statistical governance with
            zero lookahead leakage.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl px-3.5 py-2.5">
            <div className="text-[10px] text-[#64748B] uppercase">Out-Of-Sample Brier</div>
            <div className="text-base font-bold text-[#10B981] mt-0.5">0.1782</div>
          </div>
          <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl px-3.5 py-2.5">
            <div className="text-[10px] text-[#64748B] uppercase">Mean CLV Beat</div>
            <div className="text-base font-bold text-[#D4AF37] mt-0.5">+3.42%</div>
          </div>
        </div>
      </section>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto p-1 rounded-xl bg-[#0B0F17] border border-[#1E293B] text-xs font-mono">
        {[
          { key: 'matrix', label: 'Champion vs Challenger Matrix' },
          { key: 'liv', label: 'Lineup Information Value (LIV)' },
          { key: 'taxonomy', label: 'Causal Error Taxonomy (11 Categories)' },
          { key: 'abstention', label: 'Gate Abstention Audit' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
              activeTab === tab.key
                ? 'bg-[#1E293B] text-[#F8FAFC] font-semibold border border-[#334155]'
                : 'text-[#94A3B8] hover:text-[#F8FAFC]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: Champion vs Challenger Matrix */}
      {activeTab === 'matrix' && (
        <section className="space-y-6">
          <TerminalCard
            title="Out-Of-Sample Walk-Forward Evaluation Matrix"
            subtitle="Rolling 36-month validation on 10 allowlisted European competitions against 1xBet closing prices"
            badge={
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono text-[#10B981] bg-[#10B981]/15 border border-[#10B981]/30 font-semibold">
                Walk-Forward Verified
              </span>
            }
            padding="none"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0B0F17] text-[#64748B] uppercase text-[10px] tracking-wider border-b border-[#1E293B]">
                  <tr>
                    <th className="py-3.5 px-4">Model Version</th>
                    <th className="py-3.5 px-3">Architecture Description</th>
                    <th className="py-3.5 px-3 text-center">Status</th>
                    <th className="py-3.5 px-3 text-right">Brier Score</th>
                    <th className="py-3.5 px-3 text-right">Log Loss</th>
                    <th className="py-3.5 px-3 text-right">ECE Error</th>
                    <th className="py-3.5 px-3 text-right">CLV Edge</th>
                    <th className="py-3.5 px-3 text-right">Paper ROI</th>
                    <th className="py-3.5 px-4 text-right">Test Matches</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E293B] text-[#94A3B8]">
                  {MODELS.map((m) => {
                    const isChampion = m.status === 'ACTIVE_CHAMPION'
                    const isShadow = m.status === 'SHADOW_CHALLENGER'
                    return (
                      <tr
                        key={m.id}
                        className={`hover:bg-[#1E293B]/40 transition-colors ${
                          isChampion ? 'bg-[#10B981]/5' : ''
                        }`}
                      >
                        <td className="py-4 px-4 font-bold text-[#F8FAFC]">
                          <div className="flex items-center gap-2">
                            {isChampion && <span className="w-2 h-2 rounded-full bg-[#10B981]" />}
                            <span>{m.name}</span>
                          </div>
                          <div className="text-[10px] text-[#64748B] mt-0.5 font-normal">
                            Cal: {m.calibrationTransform}
                          </div>
                        </td>
                        <td className="py-4 px-3 text-[11px] max-w-xs">{m.type}</td>
                        <td className="py-4 px-3 text-center whitespace-nowrap">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              isChampion
                                ? 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/40'
                                : isShadow
                                ? 'bg-[#3B82F6]/20 text-[#3B82F6] border-[#3B82F6]/40'
                                : m.status === 'EVALUATING'
                                ? 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/40'
                                : 'bg-[#1E293B] text-[#64748B] border-[#334155]'
                            }`}
                          >
                            {m.status.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="py-4 px-3 text-right font-bold text-[#F8FAFC]">
                          {m.brierScore.toFixed(4)}
                        </td>
                        <td className="py-4 px-3 text-right">{m.logLoss.toFixed(3)}</td>
                        <td className="py-4 px-3 text-right text-[#10B981]">
                          {m.ecePercent.toFixed(1)}%
                        </td>
                        <td className="py-4 px-3 text-right font-bold text-[#D4AF37]">
                          +{m.clvPercent.toFixed(2)}%
                        </td>
                        <td
                          className={`py-4 px-3 text-right font-bold ${
                            m.paperRoiPercent >= 0 ? 'text-[#10B981]' : 'text-rose-400'
                          }`}
                        >
                          {m.paperRoiPercent >= 0 ? `+${m.paperRoiPercent.toFixed(1)}%` : `${m.paperRoiPercent.toFixed(1)}%`}
                        </td>
                        <td className="py-4 px-4 text-right text-[#64748B]">
                          {m.sampleMatches.toLocaleString()}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className="p-4 bg-[#0B0F17] border-t border-[#1E293B] text-[11px] text-[#64748B] flex flex-wrap items-center justify-between gap-3 font-mono">
              <span>Champion Promotion Rule: Challenger must achieve Brier Δ &lt; -0.002 and positive CLV across ≥ 1,500 out-of-sample matches.</span>
              <span>All evaluations tested with flat 1.0 unit stake.</span>
            </div>
          </TerminalCard>
        </section>
      )}

      {/* TAB 2: Lineup Information Value (LIV) Telemetry */}
      {activeTab === 'liv' && (
        <section className="space-y-6">
          <TerminalCard
            title="Lineup Information Value (LIV) Telemetry"
            subtitle="Empirical information gain demonstrated before lineups (T-48h) vs after verified starting 11 sheets (T-60m)"
            badge={
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono text-[#D4AF37] bg-[#D4AF37]/10 border border-[#D4AF37]/30 font-semibold">
                Lineup Gate Justification
              </span>
            }
            padding="none"
          >
            <div className="p-5 border-b border-[#1E293B] space-y-2 text-xs font-mono">
              <p className="text-[#F8FAFC] font-semibold text-sm">
                Why Predictions Strictly Unlock at T-60m:
              </p>
              <p className="text-[#94A3B8] leading-relaxed font-sans max-w-3xl">
                Across 1,571 analyzed European senior fixtures, official team sheets introduce an
                average <strong>+4.5 percentage points accuracy improvement</strong> and reduce
                forecast Brier error by <strong>8.8%</strong>. Early forecasts prior to team sheets
                suffer from uncompensated variance due to rotation, tactical resting, and bench
                demotions.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0B0F17] text-[#64748B] uppercase text-[10px] tracking-wider border-b border-[#1E293B]">
                  <tr>
                    <th className="py-3 px-4">Competition</th>
                    <th className="py-3 px-3 text-right">T-48h Early Brier</th>
                    <th className="py-3 px-3 text-right">T-60m Lineup Brier</th>
                    <th className="py-3 px-3 text-right">Brier Error Reduction</th>
                    <th className="py-3 px-3 text-right">Hit Rate Gain</th>
                    <th className="py-3 px-4 text-right">Sample Fixtures</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E293B] text-[#94A3B8]">
                  {LIV_DATA.map((row) => (
                    <tr key={row.competition} className="hover:bg-[#1E293B]/40 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#F8FAFC]">{row.competition}</td>
                      <td className="py-3.5 px-3 text-right text-[#64748B]">{row.t48Brier.toFixed(4)}</td>
                      <td className="py-3.5 px-3 text-right font-bold text-[#10B981]">
                        {row.t60mBrier.toFixed(4)}
                      </td>
                      <td className="py-3.5 px-3 text-right font-bold text-[#10B981]">
                        -{row.brierImprovement.toFixed(1)}%
                      </td>
                      <td className="py-3.5 px-3 text-right font-bold text-[#D4AF37]">
                        +{row.accuracyGain.toFixed(1)} pp
                      </td>
                      <td className="py-3.5 px-4 text-right text-[#64748B]">
                        {row.sampleCount} matches
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TerminalCard>
        </section>
      )}

      {/* TAB 3: Causal Error Taxonomy */}
      {activeTab === 'taxonomy' && (
        <section className="space-y-6">
          <TerminalCard
            title="Canonical 11-Category Causal Error Taxonomy"
            subtitle="Automated post-settlement classification decomposing predictive discrepancies into root causes"
            badge={
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono text-[#3B82F6] bg-[#3B82F6]/10 border border-[#3B82F6]/30 font-semibold">
                Error Attribution
              </span>
            }
            padding="md"
          >
            <div className="space-y-5">
              {ERROR_TAXONOMY.map((item) => (
                <div
                  key={item.code}
                  className="bg-[#0B0F17] border border-[#1E293B] rounded-xl p-4 space-y-2 text-xs font-mono"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-[#131924] text-[11px] font-bold text-[#F8FAFC]">
                        {item.code}
                      </span>
                      <span className="font-semibold text-sm text-[#F8FAFC]">{item.name}</span>
                    </div>
                    <span className="text-sm font-bold text-[#D4AF37]">{item.percentage}% of Errors</span>
                  </div>

                  {/* Percentage bar */}
                  <div className="w-full bg-[#131924] rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-[#D4AF37] to-[#10B981] h-1.5 rounded-full"
                      style={{ width: `${item.percentage * 2.5}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-[#94A3B8] font-sans leading-relaxed pt-1">
                    {item.description}
                  </p>

                  <div className="pt-2 border-t border-[#1E293B] text-[11px] text-[#10B981]">
                    <strong>Algorithmic Mitigation:</strong> {item.remedyAction}
                  </div>
                </div>
              ))}
            </div>
          </TerminalCard>
        </section>
      )}

      {/* TAB 4: Gate Abstention Audit */}
      {activeTab === 'abstention' && (
        <section className="space-y-6">
          <TerminalCard
            title="NO-BET Safety Gate Preservation Audit"
            subtitle="Capital and variance preserved by systematic abstention on low-edge or unconfirmed fixtures"
            padding="md"
          >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono mb-6">
              <div className="bg-[#0B0F17] border border-[#1E293B] rounded-xl p-4 space-y-1">
                <div className="text-[10px] text-[#64748B] uppercase">Total Evaluated Fixtures</div>
                <div className="text-2xl font-bold text-[#F8FAFC]">4,280</div>
                <div className="text-[10px] text-[#94A3B8]">Across 10 allowlisted leagues</div>
              </div>

              <div className="bg-[#0B0F17] border border-[#1E293B] rounded-xl p-4 space-y-1">
                <div className="text-[10px] text-[#64748B] uppercase">NO-BET Abstentions</div>
                <div className="text-2xl font-bold text-[#F59E0B]">3,892 (90.9%)</div>
                <div className="text-[10px] text-[#94A3B8]">Filtered by strict safety gates</div>
              </div>

              <div className="bg-[#0B0F17] border border-[#1E293B] rounded-xl p-4 space-y-1">
                <div className="text-[10px] text-[#64748B] uppercase">Candidates Dispatched</div>
                <div className="text-2xl font-bold text-[#10B981]">388 (9.1%)</div>
                <div className="text-[10px] text-[#94A3B8]">Met min edge &gt; 3.0 pp + confirmed starters</div>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-[#0B0F17] border border-[#1E293B] space-y-3 text-xs font-mono">
              <div className="font-semibold text-sm text-[#F8FAFC]">
                Institutional Abstention Philosophy
              </div>
              <p className="text-[11px] text-[#94A3B8] font-sans leading-relaxed">
                The platform abstains from 91% of available match lines. Unlike retail prediction
                services that force predictions on every game, our quantitative engine only acts
                when genuine market clearing inefficiencies exceed the bookmaker overround and model
                standard error. Abstaining on unconfirmed lineups prevents negative EV drag.
              </p>
            </div>
          </TerminalCard>
        </section>
      )}
    </div>
  )
}
