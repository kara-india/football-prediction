'use client'

import React from 'react'

export default function Analytics() {
  const CALIBRATION_BINS = [
    { bin: '10% – 20%', predicted: 15, actual: 16.2, samples: 45 },
    { bin: '20% – 30%', predicted: 25, actual: 23.8, samples: 62 },
    { bin: '30% – 40%', predicted: 35, actual: 36.1, samples: 78 },
    { bin: '40% – 50%', predicted: 45, actual: 44.3, samples: 94 },
    { bin: '50% – 60%', predicted: 55, actual: 56.4, samples: 112 },
    { bin: '60% – 70%', predicted: 65, actual: 64.8, samples: 86 },
    { bin: '70% – 80%', predicted: 75, actual: 73.5, samples: 54 },
    { bin: '80% – 90%', predicted: 85, actual: 86.0, samples: 32 },
  ]

  const MODELS = [
    {
      name: 'dixon_coles_v1.2',
      type: 'Bivariate Poisson + Tau Low-Score Coupling',
      status: 'CHAMPION',
      sampleSize: 1420,
      brier: 0.174,
      logLoss: 0.521,
      ece: '2.1%',
      roi: '+8.4%',
      notes: 'Active production model. Walk-forward validated across 10 leagues.'
    },
    {
      name: 'bivariate_xg_hazard_v2.0',
      type: 'Score-State Survival Hazard + Gradient Boosting Residual',
      status: 'CHALLENGER',
      sampleSize: 310,
      brier: 0.169,
      logLoss: 0.508,
      ece: '1.9%',
      roi: '+11.2%',
      notes: 'Shadow validation mode. Requires 200 more settled observations.'
    },
    {
      name: 'elo_dynamic_v2.0',
      type: 'Dynamic Elo Baseline with Goal Margin Weighting',
      status: 'BASELINE',
      sampleSize: 2850,
      brier: 0.198,
      logLoss: 0.589,
      ece: '4.2%',
      roi: '+1.8%',
      notes: 'Team strength prior benchmark.'
    }
  ]

  const ERROR_TAXONOMY = [
    { category: 'RANDOM_VARIANCE', pct: 36, desc: 'High xG generated, post hits, or normal probabilistic variance.' },
    { category: 'RED_CARD_EFFECT', pct: 20, desc: 'Unprojected match suspension / ejection altering game state hazard.' },
    { category: 'ODDS_MOVEMENT', pct: 16, desc: '1xBet sharp market steam moved closing line > 8% against model entry.' },
    { category: 'MODEL_OVERCONFIDENCE', pct: 12, desc: 'Predicted prob > 75% where team failed to generate expected shot volume.' },
    { category: 'SUBSTITUTION_EFFECT', pct: 10, desc: 'Key starter subbed out early or reserve keeper entered.' },
    { category: 'DATA_MISSING', pct: 6, desc: 'Unreported late training injury or weather condition.' },
  ]

  return (
    <div className="space-y-12">
      {/* Header */}
      <div className="border-b border-white/[0.08] pb-8 space-y-2">
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
          Model Calibration.
        </h1>
        <p className="text-[14px] text-neutral-400 max-w-2xl font-normal leading-relaxed">
          Probabilistic reliability verification. Every percentage output by our Monte Carlo engine must match
          its empirical historical frequency before an EV edge is considered actionable.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Brier Score</div>
          <div className="text-xl font-semibold text-emerald-400 mt-1">0.174</div>
          <div className="text-[10px] text-neutral-500">Benchmark: 0.222</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Log Loss</div>
          <div className="text-xl font-semibold text-white mt-1">0.521</div>
          <div className="text-[10px] text-neutral-500">Sharpness metric</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">ECE Error</div>
          <div className="text-xl font-semibold text-[#d4af37] mt-1">2.1%</div>
          <div className="text-[10px] text-neutral-500">&lt; 3.0% threshold</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Avg CLV</div>
          <div className="text-xl font-semibold text-emerald-400 mt-1">+3.1%</div>
          <div className="text-[10px] text-neutral-500">Beat closing line</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Gate Status</div>
          <div className="text-xl font-semibold text-emerald-400 mt-1">Pass</div>
          <div className="text-[10px] text-neutral-500">Isotonic calibrated</div>
        </div>

        <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl p-4">
          <div className="text-[11px] text-neutral-500 uppercase">Max Drawdown</div>
          <div className="text-xl font-semibold text-rose-400 mt-1">-3.2 U</div>
          <div className="text-[10px] text-neutral-500">Walk-forward</div>
        </div>
      </div>

      {/* Reliability Curve */}
      <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-2xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.06] pb-4">
          <div>
            <h2 className="text-lg font-medium text-white tracking-tight">
              Reliability Curve (Calibration Buckets)
            </h2>
            <p className="text-xs text-neutral-400 mt-0.5">
              Predicted model probabilities vs. empirical win frequencies across holdout sets
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#d4af37]"></span>
              <span className="text-neutral-400">Predicted</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400"></span>
              <span className="text-neutral-400">Actual</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CALIBRATION_BINS.map((b) => {
            const diff = b.actual - b.predicted
            return (
              <div key={b.bin} className="bg-[#070709] border border-white/[0.06] rounded-xl p-4 font-mono space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">{b.bin}</span>
                  <span className="text-[10px] text-neutral-500">{b.samples} matches</span>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-neutral-500">Model:</span>
                    <span className="text-[#d4af37] font-medium">{b.predicted}%</span>
                  </div>
                  <div className="w-full bg-neutral-900 h-1 rounded-full overflow-hidden">
                    <div className="bg-[#d4af37] h-full" style={{ width: `${b.predicted}%` }}></div>
                  </div>

                  <div className="flex justify-between text-[11px] pt-1">
                    <span className="text-neutral-500">Actual:</span>
                    <span className="text-emerald-400 font-medium">{b.actual}%</span>
                  </div>
                  <div className="w-full bg-neutral-900 h-1 rounded-full overflow-hidden">
                    <div className="bg-emerald-400 h-full" style={{ width: `${b.actual}%` }}></div>
                  </div>
                </div>

                <div className="text-[10px] text-neutral-500 flex justify-between pt-1 border-t border-white/[0.04]">
                  <span>Delta:</span>
                  <span className={diff > 0 ? 'text-emerald-400' : 'text-neutral-400'}>
                    {diff > 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Model Tournament Table */}
      <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-2xl p-6 space-y-4">
        <div className="border-b border-white/[0.06] pb-4">
          <h2 className="text-lg font-medium text-white tracking-tight">
            Champion vs. Challenger Tournament
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Production uses one validated Champion. Challengers run in shadow mode on out-of-sample data.
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#050507] text-neutral-500 uppercase text-[10px] tracking-wider border-b border-white/[0.06]">
              <tr>
                <th className="py-3 px-4">Model</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Holdout Matches</th>
                <th className="py-3 px-3 text-right">Brier Score</th>
                <th className="py-3 px-3 text-right">Log Loss</th>
                <th className="py-3 px-3 text-right">ECE</th>
                <th className="py-3 px-3 text-right">Yield</th>
                <th className="py-3 px-4">Promotion Criteria</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-neutral-300">
              {MODELS.map((m) => (
                <tr key={m.name} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-4 font-sans">
                    <div className="font-semibold text-white text-[13px]">{m.name}</div>
                    <div className="text-[11px] text-neutral-500">{m.type}</div>
                  </td>
                  <td className="py-3.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono tracking-wide ${
                        m.status === 'CHAMPION'
                          ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                          : m.status === 'CHALLENGER'
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                          : 'bg-neutral-900 text-neutral-400 border border-neutral-800'
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-right text-neutral-400">{m.sampleSize}</td>
                  <td className="py-3.5 px-3 text-right text-emerald-400 font-medium">{m.brier.toFixed(3)}</td>
                  <td className="py-3.5 px-3 text-right text-white">{m.logLoss.toFixed(3)}</td>
                  <td className="py-3.5 px-3 text-right text-[#d4af37]">{m.ece}</td>
                  <td className="py-3.5 px-3 text-right text-emerald-400 font-medium">{m.roi}</td>
                  <td className="py-3.5 px-4 text-[11px] text-neutral-500 font-sans max-w-sm">{m.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
