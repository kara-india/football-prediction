'use client'

import React from 'react'

export default function MixpanelKpiStrip() {
  return (
    <div className="bg-[#0e131b] border border-[#1e2638] rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between pb-4 border-b border-[#1e2638]/70">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-[#f0f4fc] tracking-tight">Intelligence Overview</h2>
          <span className="text-[10px] font-mono text-[#8a99ad] px-2 py-0.5 rounded-full bg-[#131924] border border-[#1e2638]">
            Today • 1xBet Target
          </span>
        </div>
        <div className="text-[11px] font-mono text-[#56657a] hidden sm:block">
          Next Lineup Drop: <span className="text-[#d4af37] font-medium">22:30 IST</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-5">
        {/* KPI 1: Active Fixtures */}
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-bold tracking-tight text-[#f0f4fc] font-mono">
              24
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
              Active Today
            </span>
          </div>

          <div>
            <div className="text-xs font-medium text-[#f0f4fc]">Allowlisted Fixtures</div>
            <div className="text-[11px] text-[#8a99ad]">10 Top European & Int'l Competitions</div>
          </div>

          {/* SVG Sparkline (Mixpanel style) */}
          <div className="pt-2">
            <svg className="w-full h-10 overflow-visible" viewBox="0 0 200 40">
              <path
                d="M 0 35 Q 30 30, 60 25 T 120 15 T 160 8 L 200 12"
                fill="none"
                stroke="#6366f1"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M 0 35 Q 30 30, 60 25 T 120 15 T 160 8 L 200 12 L 200 40 L 0 40 Z"
                fill="url(#sparkline-indigo)"
                opacity="0.15"
              />
              <defs>
                <linearGradient id="sparkline-indigo" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
            <div className="flex justify-between text-[9px] font-mono text-[#56657a] pt-1">
              <span>18:00 IST</span>
              <span>23:30 IST</span>
            </div>
          </div>
        </div>

        {/* KPI 2: 1xBet Average Signal Edge */}
        <div className="space-y-3 sm:border-l sm:border-[#1e2638] sm:pl-6">
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-bold tracking-tight text-[#10b981] font-mono">
              +5.2%
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#d4af37]/15 text-[#d4af37] border border-[#d4af37]/30">
              De-Vigged
            </span>
          </div>

          <div>
            <div className="text-xs font-medium text-[#f0f4fc]">1xBet Positive EV</div>
            <div className="text-[11px] text-[#8a99ad]">Across 1X2 & Goal Hazard Markets</div>
          </div>

          {/* SVG Sparkline */}
          <div className="pt-2">
            <svg className="w-full h-10 overflow-visible" viewBox="0 0 200 40">
              <path
                d="M 0 32 Q 40 35, 80 22 T 140 18 T 200 6"
                fill="none"
                stroke="#10b981"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M 0 32 Q 40 35, 80 22 T 140 18 T 200 6 L 200 40 L 0 40 Z"
                fill="url(#sparkline-emerald)"
                opacity="0.15"
              />
              <defs>
                <linearGradient id="sparkline-emerald" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
            <div className="flex justify-between text-[9px] font-mono text-[#56657a] pt-1">
              <span>Threshold: +3.0%</span>
              <span>Max: +8.9%</span>
            </div>
          </div>
        </div>

        {/* KPI 3: Lineup Lock Gate */}
        <div className="space-y-3 lg:border-l lg:border-[#1e2638] lg:pl-6">
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-bold tracking-tight text-[#d4af37] font-mono">
              3 <span className="text-lg font-normal text-[#8a99ad]">/ 24</span>
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-amber-400/15 text-amber-300 border border-amber-400/30">
              Gate Protected
            </span>
          </div>

          <div>
            <div className="text-xs font-medium text-[#f0f4fc]">Lineup Verification</div>
            <div className="text-[11px] text-[#8a99ad]">3 Confirmed • 21 Waiting (~60m Drop)</div>
          </div>

          {/* Progress / Step Curve */}
          <div className="pt-2">
            <div className="w-full bg-[#131924] rounded-full h-2 overflow-hidden my-4">
              <div
                className="bg-gradient-to-r from-amber-400 to-[#d4af37] h-2 rounded-full"
                style={{ width: '12.5%' }}
              ></div>
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#56657a]">
              <span>Gate: Active</span>
              <span>Next Scan: 22:30 IST</span>
            </div>
          </div>
        </div>

        {/* KPI 4: Brier Calibration Score */}
        <div className="space-y-3 lg:border-l lg:border-[#1e2638] lg:pl-6">
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-bold tracking-tight text-[#f0f4fc] font-mono">
              0.174
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
              Champion
            </span>
          </div>

          <div>
            <div className="text-xs font-medium text-[#f0f4fc]">Brier Calibration</div>
            <div className="text-[11px] text-[#8a99ad]">Dixon-Coles v1.2 (vs 0.198 Elo)</div>
          </div>

          {/* SVG Sparkline */}
          <div className="pt-2">
            <svg className="w-full h-10 overflow-visible" viewBox="0 0 200 40">
              <path
                d="M 0 10 Q 50 12, 100 18 T 160 28 T 200 32"
                fill="none"
                stroke="#d4af37"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M 0 10 Q 50 12, 100 18 T 160 28 T 200 32 L 200 40 L 0 40 Z"
                fill="url(#sparkline-gold)"
                opacity="0.15"
              />
              <defs>
                <linearGradient id="sparkline-gold" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#d4af37" />
                  <stop offset="100%" stopColor="#d4af37" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
            <div className="flex justify-between text-[9px] font-mono text-[#56657a] pt-1">
              <span>ECE: 2.1%</span>
              <span>LogLoss: 0.521</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
