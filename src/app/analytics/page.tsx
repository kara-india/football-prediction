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
    { bin: '80% – 90%', predicted: 85, actual: 86.0, samples: 32 }
  ]

  const MODELS = [
    {
      name: 'dixon_coles_v1.2',
      type: 'Bivariate Poisson + Low-Score Tau Coupling',
      status: 'CHAMPION',
      sampleSize: 1420,
      brier: 0.174,
      logLoss: 0.521,
      ece: '2.1%',
      roi: '+8.4%',
      notes: 'Active production model. Walk-forward validated across 10 allowlisted European leagues.'
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
      notes: 'Shadow validation mode. Requires 190 more settled observations before promotion review.'
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
      notes: 'Team strength prior benchmark. Used as conservative sanity bounds.'
    }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-[#1e2638] pb-6 space-y-1.5">
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#8a99ad] bg-[#0e131b] border border-[#1e2638]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
          <span>Brier Calibration Verification</span>
          <span className="text-[#56657a]">·</span>
          <span className="text-[#d4af37]">ECE 2.1% Validated</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc]">
          Model Calibration & Verification
        </h1>
        <p className="text-xs sm:text-sm text-[#8a99ad] max-w-2xl leading-relaxed">
          Probabilistic reliability verification. Every probability output by our Monte Carlo simulation must match
          its empirical historical frequency before a 1xBet EV edge is considered actionable.
        </p>
      </div>

      {/* Mixpanel KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Brier Score</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">0.174</div>
          <div className="text-[10px] text-[#8a99ad]">Elo: 0.198</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Log Loss</div>
          <div className="text-xl font-bold text-[#f0f4fc] mt-1">0.521</div>
          <div className="text-[10px] text-[#8a99ad]">Sharpness metric</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">ECE Error</div>
          <div className="text-xl font-bold text-[#d4af37] mt-1">2.1%</div>
          <div className="text-[10px] text-[#8a99ad]">&lt; 3.0% threshold</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Avg CLV</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">+3.1%</div>
          <div className="text-[10px] text-[#8a99ad]">vs closing price</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Gate Status</div>
          <div className="text-xl font-bold text-[#10b981] mt-1">PASS</div>
          <div className="text-[10px] text-[#8a99ad]">15 gates active</div>
        </div>

        <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl p-4">
          <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Max Drawdown</div>
          <div className="text-xl font-bold text-rose-400 mt-1">-3.2 U</div>
          <div className="text-[10px] text-[#8a99ad]">Out-of-sample</div>
        </div>
      </div>

      {/* Reliability Curve (Mixpanel Buckets Grid) */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1e2638] pb-4">
          <div>
            <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
              Reliability Curve (Calibration Buckets)
            </h2>
            <p className="text-xs text-[#8a99ad] mt-0.5">
              Predicted model probabilities vs. empirical win frequencies across holdout sets
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#d4af37]"></span>
              <span className="text-[#8a99ad]">Predicted</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#10b981]"></span>
              <span className="text-[#8a99ad]">Actual</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CALIBRATION_BINS.map((b) => {
            const diff = b.actual - b.predicted
            return (
              <div
                key={b.bin}
                className="bg-[#090c10] border border-[#1e2638] hover:border-[#2b374e] rounded-xl p-4 font-mono space-y-3 transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#f0f4fc]">{b.bin}</span>
                  <span className="text-[10px] text-[#56657a]">{b.samples} matches</span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-[#8a99ad]">Model:</span>
                    <span className="text-[#d4af37] font-semibold">{b.predicted}%</span>
                  </div>
                  <div className="w-full bg-[#131924] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#d4af37] h-full rounded-full"
                      style={{ width: `${b.predicted}%` }}
                    ></div>
                  </div>

                  <div className="flex justify-between text-[11px] pt-1">
                    <span className="text-[#8a99ad]">Actual:</span>
                    <span className="text-[#10b981] font-semibold">{b.actual}%</span>
                  </div>
                  <div className="w-full bg-[#131924] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#10b981] h-full rounded-full"
                      style={{ width: `${b.actual}%` }}
                    ></div>
                  </div>
                </div>

                <div className="text-[10px] text-[#56657a] flex justify-between pt-1 border-t border-[#1e2638]">
                  <span>Delta:</span>
                  <span className={diff >= 0 ? 'text-[#10b981] font-medium' : 'text-[#8a99ad]'}>
                    {diff >= 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Model Tournament Table */}
      <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 space-y-4">
        <div className="border-b border-[#1e2638] pb-4">
          <h2 className="text-base font-semibold text-[#f0f4fc] tracking-tight">
            Champion vs. Challenger Tournament
          </h2>
          <p className="text-xs text-[#8a99ad] mt-0.5">
            Production uses one validated Champion. Challengers run in shadow mode on out-of-sample data.
          </p>
        </div>

        <div className="overflow-x-auto rounded-xl border border-[#1e2638] bg-[#090c10]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#090c10] text-[#56657a] uppercase text-[10px] tracking-wider border-b border-[#1e2638]">
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
            <tbody className="divide-y divide-[#1e2638] text-[#8a99ad]">
              {MODELS.map((m) => (
                <tr key={m.name} className="hover:bg-[#131924]/60 transition-colors">
                  <td className="py-3.5 px-4 font-sans">
                    <div className="font-semibold text-[#f0f4fc] text-[13px]">{m.name}</div>
                    <div className="text-[11px] text-[#56657a]">{m.type}</div>
                  </td>
                  <td className="py-3.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold tracking-wide ${
                        m.status === 'CHAMPION'
                          ? 'bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30'
                          : m.status === 'CHALLENGER'
                          ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                          : 'bg-[#131924] text-[#8a99ad] border border-[#1e2638]'
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-right text-[#8a99ad]">{m.sampleSize}</td>
                  <td className="py-3.5 px-3 text-right text-[#10b981] font-bold">
                    {m.brier.toFixed(3)}
                  </td>
                  <td className="py-3.5 px-3 text-right text-[#f0f4fc]">{m.logLoss.toFixed(3)}</td>
                  <td className="py-3.5 px-3 text-right text-[#d4af37] font-semibold">{m.ece}</td>
                  <td className="py-3.5 px-3 text-right text-[#10b981] font-bold">{m.roi}</td>
                  <td className="py-3.5 px-4 text-[11px] text-[#8a99ad] font-sans max-w-sm">
                    {m.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
