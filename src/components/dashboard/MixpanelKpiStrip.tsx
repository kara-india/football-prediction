'use client'

import React from 'react'

export default function MixpanelKpiStrip() {
  return (
    <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl p-5 sm:p-6 shadow-terminal-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1E293B] gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
          <h2 className="text-xs sm:text-sm font-bold text-[#F8FAFC] tracking-tight uppercase font-mono">
            Platform Operational Telemetry
          </h2>
          <span className="text-[10px] font-mono text-[#94A3B8] px-2 py-0.5 rounded-full bg-[#1E293B] border border-[#334155]">
            1xBet Fixed Clearing
          </span>
        </div>
        <div className="text-[11px] font-mono text-[#64748B]">
          Clock: <span className="text-[#D4AF37] font-semibold">IST (UTC+5:30)</span> • Single Bookmaker Policy
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6 pt-5">
        {/* Metric 1: Competition Scope */}
        <div className="space-y-2.5">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F8FAFC] font-mono">
              10
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
              Allowlisted
            </span>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#F8FAFC]">Tier-1 Competition Scope</div>
            <div className="text-[11px] text-[#94A3B8] font-mono mt-0.5">Top 5 European + UEFA + CONMEBOL</div>
          </div>
          <div className="text-[10px] text-[#64748B] font-mono pt-1 border-t border-[#1E293B]">
            Youth, women &amp; reserves strictly filtered
          </div>
        </div>

        {/* Metric 2: Lineup Governance Lock */}
        <div className="space-y-2.5 sm:border-l sm:border-[#1E293B] sm:pl-6">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#D4AF37] font-mono">
              T-60m
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#D4AF37]/15 text-[#D4AF37] border border-[#D4AF37]/30">
              Gatekeeper
            </span>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#F8FAFC]">Starting XI Verification</div>
            <div className="text-[11px] text-[#94A3B8] font-mono mt-0.5">Strict 11 vs 11 Team Sheet Validation</div>
          </div>
          <div className="text-[10px] text-[#64748B] font-mono pt-1 border-t border-[#1E293B]">
            Mathematical forecast unlocked on team drop
          </div>
        </div>

        {/* Metric 3: Simulation Precision */}
        <div className="space-y-2.5 lg:border-l lg:border-[#1E293B] lg:pl-6">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#0EA5E9] font-mono">
              10,000
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#0EA5E9]/15 text-[#0EA5E9] border border-[#0EA5E9]/30">
              Monte Carlo
            </span>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#F8FAFC]">Path-Dependent Simulation</div>
            <div className="text-[11px] text-[#94A3B8] font-mono mt-0.5">Vectorized Matrix • Competing Hazards</div>
          </div>
          <div className="text-[10px] text-[#64748B] font-mono pt-1 border-t border-[#1E293B]">
            SE &le; &plusmn;0.004 empirical stopping rule
          </div>
        </div>

        {/* Metric 4: Zero-Cost Quota Governance */}
        <div className="space-y-2.5 lg:border-l lg:border-[#1E293B] lg:pl-6">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#10B981] font-mono">
              ₹0.00
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
              Cost Invariant
            </span>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#F8FAFC]">API Quota Protection</div>
            <div className="text-[11px] text-[#94A3B8] font-mono mt-0.5">95 Daily Cap (50 User / 45 Worker)</div>
          </div>
          <div className="text-[10px] text-[#64748B] font-mono pt-1 border-t border-[#1E293B]">
            Zero-cost external budget enforced
          </div>
        </div>
      </div>
    </div>
  )
}
