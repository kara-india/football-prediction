import LiveMatchSection from '../components/dashboard/LiveMatchSection'
import UpcomingMatchSection from '../components/dashboard/UpcomingMatchSection'

export default function Dashboard() {
  return (
    <div className="space-y-10">
      {/* Platform Info Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-slate-900/50 border border-blue-900/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide bg-blue-500/20 text-blue-300 border border-blue-500/30">
                STATISTICAL INTELLIGENCE
              </span>
              <span className="text-xs text-slate-400 font-mono">1xBet Normalized</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-2 tracking-tight">
              Match Intelligence Board
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time match state, 1xBet target odds de-vigging, and path-dependent Monte Carlo simulations.
              Upcoming match predictions activate automatically upon official starting lineup announcement.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 self-start md:self-auto text-xs font-mono">
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2.5 text-center">
              <div className="text-[10px] text-slate-500 uppercase">Target Bookmaker</div>
              <div className="text-sm font-bold text-orange-400 mt-0.5">1xBet</div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2.5 text-center">
              <div className="text-[10px] text-slate-500 uppercase">NO-BET Filter</div>
              <div className="text-sm font-bold text-emerald-400 mt-0.5">15 Gates</div>
            </div>
            <div className="col-span-2 sm:col-span-1 bg-slate-900/80 border border-slate-800 rounded-lg p-2.5 text-center">
              <div className="text-[10px] text-slate-500 uppercase">Simulation Count</div>
              <div className="text-sm font-bold text-blue-400 mt-0.5">10k – 500k</div>
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
