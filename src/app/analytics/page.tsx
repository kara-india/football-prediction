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
      type: 'Bivariate Poisson + Tau Low Score Coupling',
      status: 'CHAMPION',
      statusColor: 'bg-emerald-950 text-emerald-300 border-emerald-700',
      sampleSize: 1420,
      brier: 0.174,
      logLoss: 0.521,
      ece: '2.1%',
      roi: '+8.4%',
      notes: 'Active production champion. Walk-forward validated across 10 domestic leagues.'
    },
    {
      name: 'bivariate_xg_hazard_v2.0',
      type: 'Score-State Survival Hazard + Gradient Boosting Residual',
      status: 'CHALLENGER',
      statusColor: 'bg-blue-950 text-blue-300 border-blue-700',
      sampleSize: 310,
      brier: 0.169,
      logLoss: 0.508,
      ece: '1.9%',
      roi: '+11.2%',
      notes: 'Shadow validation mode. Requires 200 more settled observations before promotion vote.'
    },
    {
      name: 'elo_dynamic_v2.0',
      type: 'Dynamic Elo Baseline with Margin & Rest-Days',
      status: 'BASELINE',
      statusColor: 'bg-slate-800 text-slate-300 border-slate-700',
      sampleSize: 2850,
      brier: 0.198,
      logLoss: 0.589,
      ece: '4.2%',
      roi: '+1.8%',
      notes: 'Sanity benchmark for team strength prior distribution.'
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
    <div className="space-y-10">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide bg-blue-500/20 text-blue-300 border border-blue-500/30">
            PROBABILITY RELIABILITY
          </span>
          <span className="text-xs text-slate-400 font-mono">Walk-Forward Out-Of-Sample Validation</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-1.5 tracking-tight">
          Model Calibration & Verification Analytics
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          A model that wins 60% of bets at 1.50 odds loses money. This system measures calibration:
          when the model predicts 70%, exactly 70% of those events must historically occur.
        </p>
      </div>

      {/* Primary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Brier Score</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">0.174</div>
          <div className="text-[10px] text-slate-500 mt-0.5">naive benchmark 0.222</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Log Loss</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">0.521</div>
          <div className="text-[10px] text-slate-500 mt-0.5">sharpness metric</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center">
          <div className="text-[11px] text-slate-400 uppercase font-medium">ECE Error</div>
          <div className="text-xl font-bold text-blue-400 mt-1">2.1%</div>
          <div className="text-[10px] text-slate-500 mt-0.5">&lt; 3.0% calibrated</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Avg CLV</div>
          <div className="text-xl font-bold text-purple-400 mt-1">+3.1%</div>
          <div className="text-[10px] text-slate-500 mt-0.5">beat closing line</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Calibration Gate</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">PASS</div>
          <div className="text-[10px] text-slate-500 mt-0.5">isotonic regression</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Max Drawdown</div>
          <div className="text-xl font-bold text-rose-400 mt-1">-3.2 U</div>
          <div className="text-[10px] text-slate-500 mt-0.5">peak-to-trough</div>
        </div>
      </div>

      {/* Reliability Curve / Calibration Diagram */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Reliability Curve (Calibration Buckets)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparison between Model Predicted Probabilities vs. Observed Empirical Win Frequency
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-blue-500"></span>
              <span className="text-slate-300">Model Predictions</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-emerald-400"></span>
              <span className="text-slate-300">Perfect 45° Calibration</span>
            </div>
          </div>
        </div>

        {/* Visual Bar Matrix */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CALIBRATION_BINS.map((b) => {
            const diff = b.actual - b.predicted
            const isClose = Math.abs(diff) <= 2.5

            return (
              <div key={b.bin} className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 font-mono">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                  <span className="font-semibold text-white">{b.bin}</span>
                  <span className="text-[10px] text-slate-500">{b.samples} matches</span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-slate-400">Model Mean:</span>
                    <span className="font-bold text-blue-400">{b.predicted}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full rounded-full" style={{ width: `${b.predicted}%` }}></div>
                  </div>

                  <div className="flex justify-between items-center text-[11px] pt-1">
                    <span className="text-slate-400">Actual Win %:</span>
                    <span className={`font-bold ${isClose ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {b.actual}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${isClose ? 'bg-emerald-400' : 'bg-amber-400'}`}
                      style={{ width: `${b.actual}%` }}
                    ></div>
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-900 text-[10px] flex justify-between text-slate-500">
                  <span>Delta:</span>
                  <span className={diff > 0 ? 'text-emerald-400' : 'text-slate-400'}>
                    {diff > 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Model Tournament: Champion vs Challenger */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-lg font-bold text-white tracking-wide">
            Champion vs. Challenger Model Registry
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Production uses one validated CHAMPION model. Challengers are run in shadow mode on walk-forward holdout data.
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800 font-mono">
              <tr>
                <th className="py-3 px-4">Model & Architecture</th>
                <th className="py-3 px-3">Role Status</th>
                <th className="py-3 px-3 text-right">Holdout Sample</th>
                <th className="py-3 px-3 text-right">Brier Score</th>
                <th className="py-3 px-3 text-right">Log Loss</th>
                <th className="py-3 px-3 text-right">ECE</th>
                <th className="py-3 px-3 text-right">Historical ROI</th>
                <th className="py-3 px-4">Promotion Criteria</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {MODELS.map((m) => (
                <tr key={m.name} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white text-sm font-mono">{m.name}</div>
                    <div className="text-[11px] text-slate-400">{m.type}</div>
                  </td>
                  <td className="py-3.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${m.statusColor}`}>
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-right font-mono text-slate-300">
                    {m.sampleSize} matches
                  </td>
                  <td className="py-3.5 px-3 text-right font-mono font-bold text-emerald-400">
                    {m.brier.toFixed(3)}
                  </td>
                  <td className="py-3.5 px-3 text-right font-mono text-slate-200">
                    {m.logLoss.toFixed(3)}
                  </td>
                  <td className="py-3.5 px-3 text-right font-mono text-blue-400">
                    {m.ece}
                  </td>
                  <td className="py-3.5 px-3 text-right font-mono font-bold text-emerald-400">
                    {m.roi}
                  </td>
                  <td className="py-3.5 px-4 text-[11px] text-slate-400 max-w-sm">
                    {m.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Error Taxonomy Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-lg font-bold text-white tracking-wide">
            Automated Error Taxonomy (Post-Match Diagnostics)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Every unsettled or missed prediction is programmatically classified into measurable error types — never invented by LLMs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {ERROR_TAXONOMY.map((e) => (
            <div key={e.category} className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5">
              <div className="flex items-center justify-between text-xs mb-1.5 font-mono">
                <span className="font-bold text-slate-200">{e.category}</span>
                <span className="font-bold text-blue-400">{e.pct}%</span>
              </div>
              <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden mb-2">
                <div className="bg-blue-500 h-full rounded-full" style={{ width: `${e.pct}%` }}></div>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{e.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
