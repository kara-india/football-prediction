import LiveMatchSection from '../components/dashboard/LiveMatchSection'
import UpcomingMatchSection from '../components/dashboard/UpcomingMatchSection'

export default function Dashboard() {
  return (
    <div className="space-y-12">
      {/* Hero Section: Apple/Nike Clean Editorial */}
      <section className="border-b border-white/[0.08] pb-10">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="max-w-2xl space-y-2">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium text-neutral-400 bg-white/[0.04] border border-white/[0.08]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4af37]"></span>
              <span>1xBet Target Execution</span>
              <span className="text-neutral-600">·</span>
              <span className="text-neutral-400">Zero Cost Ingestion</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-[-0.03em] text-white">
              Football Intelligence.
            </h1>

            <p className="text-[15px] sm:text-base text-neutral-400 leading-relaxed font-normal">
              Continuous hazard modeling, 1xBet market de-vigging, and path-dependent Monte Carlo simulations.
              Pre-match probabilities unlock automatically once official starting XIs are verified.
            </p>
          </div>

          {/* Micro Telemetry Bar */}
          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl px-4 py-3 min-w-[120px]">
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider">Bookmaker</div>
              <div className="text-sm font-semibold text-[#d4af37] mt-0.5">1xBet Fixed</div>
            </div>

            <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl px-4 py-3 min-w-[120px]">
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider">Filter Gates</div>
              <div className="text-sm font-semibold text-emerald-400 mt-0.5">15 Enforced</div>
            </div>

            <div className="bg-[#0c0c0e] border border-white/[0.08] rounded-xl px-4 py-3 min-w-[120px]">
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider">Simulations</div>
              <div className="text-sm font-semibold text-white mt-0.5">50,000 / Match</div>
            </div>
          </div>
        </div>
      </section>

      {/* Live Matches Section */}
      <LiveMatchSection />

      {/* Upcoming Matches Section */}
      <UpcomingMatchSection />
    </div>
  )
}
