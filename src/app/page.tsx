import LiveMatchSection from '../components/dashboard/LiveMatchSection'
import UpcomingMatchSection from '../components/dashboard/UpcomingMatchSection'

export default function Dashboard() {
  return (
    <div className="space-y-10">
      {/* Platform Info Banner - Gold & Green Money Terminal */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-[#0b1416]/90 to-amber-950/20 border border-emerald-900/50 rounded-2xl p-6 sm:p-7 shadow-2xl relative overflow-hidden backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black tracking-wider bg-gradient-to-r from-amber-500/20 to-yellow-500/10 text-amber-300 border border-amber-500/40 shadow-sm font-mono">
                QUANTITATIVE EDGE INTELLIGENCE
              </span>
              <span className="text-[11px] text-emerald-400/90 font-mono flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                1xBet Market Normalized
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-2.5 tracking-tight flex items-center gap-2">
              Match Intelligence Terminal
            </h1>

            <p className="text-sm text-slate-300/90 mt-1.5 max-w-2xl leading-relaxed">
              Real-time match states, 1xBet target odds de-vigging, and path-dependent Monte Carlo simulation.
              Upcoming match predictions activate automatically upon official starting lineup announcement.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 self-start md:self-auto text-xs font-mono">
            <div className="bg-[#080e10]/90 border border-amber-500/30 rounded-xl p-3 text-center shadow-md">
              <div className="text-[10px] text-amber-400/80 uppercase font-semibold">Target Bookmaker</div>
              <div className="text-base font-extrabold text-amber-300 mt-0.5 flex items-center justify-center gap-1">
                <span className="text-xs">⚡</span> 1xBet
              </div>
            </div>

            <div className="bg-[#080e10]/90 border border-emerald-500/30 rounded-xl p-3 text-center shadow-md">
              <div className="text-[10px] text-emerald-400/80 uppercase font-semibold">NO-BET Filter</div>
              <div className="text-base font-extrabold text-emerald-300 mt-0.5">15 Gates</div>
            </div>

            <div className="col-span-2 sm:col-span-1 bg-[#080e10]/90 border border-teal-500/30 rounded-xl p-3 text-center shadow-md">
              <div className="text-[10px] text-teal-400/80 uppercase font-semibold">Simulation Paths</div>
              <div className="text-base font-extrabold text-teal-300 mt-0.5">10k – 500k</div>
            </div>
          </div>
        </div>
      </div>

      {/* 1. Live Matches Section */}
      <LiveMatchSection />

      {/* 2. Upcoming Matches Section */}
      <UpcomingMatchSection />
    </div>
  )
}
