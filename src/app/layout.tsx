import './globals.css'
import Link from 'next/link'
import EngineStatus from '../components/dashboard/EngineStatus'

export const metadata = {
  title: 'Football Intelligence | 1xBet Quantitative Betting Terminal',
  description: 'Production statistical prediction and betting intelligence engine for 1xBet markets'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080d0e] text-slate-100 min-h-screen flex flex-col font-sans antialiased selection:bg-emerald-500 selection:text-black">
        {/* Top Financial Ticker Bar */}
        <div className="bg-[#050809] border-b border-emerald-950/60 text-[11px] font-mono py-1.5 px-4 sm:px-8 text-slate-400 flex items-center justify-between overflow-x-auto whitespace-nowrap">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              QUANT ENGINE ONLINE
            </span>
            <span className="text-slate-600">|</span>
            <span>Target: <strong className="text-amber-400 font-bold">1xBet Normalized</strong></span>
            <span className="text-slate-600">|</span>
            <span>Timezone: <strong className="text-slate-300">IST (UTC+5:30)</strong></span>
            <span className="text-slate-600">|</span>
            <span>API Quota Guard: <strong className="text-emerald-400">71 Remaining (50 Reserved for User)</strong></span>
          </div>

          <div className="hidden md:flex items-center gap-3 text-slate-400">
            <span>Model: <strong className="text-amber-300">Dixon-Coles v1.2</strong></span>
            <span>Sims: <strong className="text-emerald-400">50k Paths</strong></span>
          </div>
        </div>

        {/* Navigation Bar */}
        <header className="border-b border-emerald-950/80 bg-[#0b1214]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              {/* Gold & Emerald Logo */}
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 via-emerald-500 to-teal-700 flex items-center justify-center text-slate-950 font-black text-lg shadow-md shadow-emerald-500/20 group-hover:scale-105 transition border border-amber-300/40">
                  ⚡
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-sm tracking-wider text-white group-hover:text-amber-300 transition">
                      FOOTBALL QUANT
                    </span>
                    <span className="text-[10px] bg-gradient-to-r from-amber-400 to-emerald-400 bg-clip-text text-transparent font-black font-mono">
                      v2.0
                    </span>
                  </div>
                  <span className="text-[10px] text-emerald-400/80 font-mono tracking-wider -mt-0.5">
                    1xBet Intelligence Platform
                  </span>
                </div>
              </Link>

              {/* Navigation Links */}
              <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-emerald-950/60 text-xs font-medium">
                <Link
                  href="/"
                  className="px-3 py-1.5 rounded-lg text-emerald-300 bg-emerald-950/50 border border-emerald-800/60 hover:bg-emerald-900/60 transition shadow-sm font-semibold"
                >
                  Live & Upcoming
                </Link>
                <Link
                  href="/predictions"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-amber-300 hover:bg-emerald-950/30 border border-transparent hover:border-amber-500/30 transition"
                >
                  Paper Ledger
                </Link>
                <Link
                  href="/analytics"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-emerald-300 hover:bg-emerald-950/30 border border-transparent hover:border-emerald-500/30 transition"
                >
                  Model Calibration
                </Link>
                <Link
                  href="/providers"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-amber-300 hover:bg-emerald-950/30 border border-transparent hover:border-amber-500/30 transition"
                >
                  Providers & Health
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <EngineStatus />
            </div>
          </div>
        </header>

        {/* Main Content Container */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Global Footer */}
        <footer className="border-t border-emerald-950/60 bg-[#050809] py-6 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
            <div>
              <p className="font-semibold text-slate-300 flex items-center gap-1.5 justify-center sm:justify-start">
                <span className="text-amber-400">★</span> Quantitative 1xBet Football Intelligence System
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                Reproducible mathematical probabilities · Dixon-Coles Poisson + Path-Dependent Monte Carlo · 15 Strict NO-BET Gates
              </p>
            </div>
            <div className="flex items-center gap-4 text-[11px] font-mono">
              <span className="text-slate-400">Execution: <strong className="text-amber-400">1xBet Fixed</strong></span>
              <span className="text-slate-400">Database: <strong className="text-emerald-400">Supabase Cloud</strong></span>
              <span className="text-slate-400">Historical: <strong className="text-emerald-400">football-data.co.uk</strong></span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
