import LiveMatchSection from '../components/dashboard/LiveMatchSection'
import UpcomingMatchSection from '../components/dashboard/UpcomingMatchSection'
import MixpanelKpiStrip from '../components/dashboard/MixpanelKpiStrip'

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Mixpanel Style Hero Greeting & System Context */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-2 border-b border-[#1e2638]">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-[#8a99ad] bg-[#0e131b] border border-[#1e2638]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
            <span>1xBet Execution Engine Active</span>
            <span className="text-[#56657a]">·</span>
            <span className="text-[#d4af37]">Strict ₹0.00 Cost Guarantee</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#f0f4fc]">
            Match Intelligence Board
          </h1>

          <p className="text-xs sm:text-sm text-[#8a99ad] max-w-2xl leading-relaxed">
            Continuous hazard modeling, 1xBet market de-vigging, and path-dependent Monte Carlo simulations.
            Mathematical probabilities unlock once official starting lineups drop (~60m before kickoff).
          </p>
        </div>

        {/* Quick Micro Badges */}
        <div className="flex items-center gap-2.5 font-mono text-xs shrink-0">
          <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl px-3.5 py-2.5 min-w-[110px]">
            <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Bookmaker</div>
            <div className="text-xs font-bold text-[#d4af37] mt-0.5">1xBet Fixed</div>
          </div>

          <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl px-3.5 py-2.5 min-w-[110px]">
            <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Lineup Gate</div>
            <div className="text-xs font-bold text-[#10b981] mt-0.5">15 Enforced</div>
          </div>

          <div className="bg-[#0e131b] border border-[#1e2638] rounded-xl px-3.5 py-2.5 min-w-[110px]">
            <div className="text-[10px] text-[#56657a] uppercase tracking-wider">Simulations</div>
            <div className="text-xs font-bold text-[#f0f4fc] mt-0.5">50,000 / Match</div>
          </div>
        </div>
      </section>

      {/* Mixpanel 4-KPI Metric Strip with Sparklines */}
      <MixpanelKpiStrip />

      {/* Live Matches Section */}
      <LiveMatchSection />

      {/* Upcoming Matches Section with Filter Chips & Odds Grid */}
      <UpcomingMatchSection />
    </div>
  )
}
