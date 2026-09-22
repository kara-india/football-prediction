import './globals.css'
import Link from 'next/link'
import EngineStatus from '../components/dashboard/EngineStatus'

export const metadata = {
  title: 'Football Intelligence | 1xBet Statistical Platform',
  description: 'Production statistical prediction and betting intelligence engine for 1xBet markets'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans antialiased selection:bg-blue-600 selection:text-white">
        {/* Navigation Bar */}
        <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-extrabold text-base shadow-md shadow-blue-500/20 group-hover:scale-105 transition">
                  ⚽
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-sm tracking-wide text-white group-hover:text-blue-400 transition">
                    FOOTBALL PREDICTION
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono tracking-wider -mt-0.5">
                    1xBet Intelligence Engine
                  </span>
                </div>
              </Link>

              <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-800 text-xs font-medium">
                <Link
                  href="/"
                  className="px-3 py-1.5 rounded-md text-white bg-slate-800/80 hover:bg-slate-800 transition"
                >
                  Live & Upcoming
                </Link>
                <Link
                  href="/predictions"
                  className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
                >
                  Paper Ledger
                </Link>
                <Link
                  href="/analytics"
                  className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
                >
                  Model Calibration
                </Link>
                <Link
                  href="/providers"
                  className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/50 transition"
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
        <footer className="border-t border-slate-900 bg-slate-950 py-6 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
            <div>
              <p className="font-medium text-slate-400">Personal Football Prediction & Betting Intelligence System</p>
              <p className="text-[11px] text-slate-600 mt-0.5">Strictly reproducible numerical probabilities · No LLM hallucinations · 15-Gate NO-BET filter</p>
            </div>
            <div className="flex items-center gap-4 text-[11px]">
              <span>Target: <strong className="text-orange-400">1xBet</strong></span>
              <span>Data: <strong className="text-slate-400">API-Football v3</strong></span>
              <span>Backend: <strong className="text-emerald-400">Supabase</strong></span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
