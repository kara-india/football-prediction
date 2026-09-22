import './globals.css'
import Link from 'next/link'
import EngineStatus from '../components/dashboard/EngineStatus'

export const metadata = {
  title: 'Football Prediction Terminal | 1xBet Quantitative Intelligence',
  description: 'Production statistical prediction and betting intelligence engine for 1xBet markets'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-black text-[#f5f5f7] min-h-screen flex flex-col font-sans antialiased selection:bg-[#d4af37] selection:text-black">
        {/* Apple-Style Navigation Bar */}
        <header className="sticky top-0 z-50 bg-black/70 backdrop-blur-2xl border-b border-white/[0.08]">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-8">
              {/* Minimalist Monogram Brand */}
              <Link href="/" className="flex items-center gap-2 group">
                <span className="w-6 h-6 rounded-md bg-white text-black font-extrabold text-xs flex items-center justify-center font-mono tracking-tighter shadow-sm">
                  1X
                </span>
                <span className="text-[13px] font-medium tracking-tight text-white group-hover:text-neutral-300 transition-colors">
                  Football Intelligence
                </span>
              </Link>

              {/* Classic Navigation Links */}
              <nav className="hidden md:flex items-center gap-6 text-[13px] font-normal text-neutral-400">
                <Link
                  href="/"
                  className="hover:text-white transition-colors py-1"
                >
                  Matches
                </Link>
                <Link
                  href="/predictions"
                  className="hover:text-white transition-colors py-1"
                >
                  Paper Ledger
                </Link>
                <Link
                  href="/analytics"
                  className="hover:text-white transition-colors py-1"
                >
                  Calibration
                </Link>
                <Link
                  href="/providers"
                  className="hover:text-white transition-colors py-1"
                >
                  Providers
                </Link>
              </nav>
            </div>

            {/* Right Controls */}
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 text-[11px] font-mono text-neutral-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>IST (UTC+5:30)</span>
              </div>
              <EngineStatus />
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-10">
          {children}
        </main>

        {/* Apple/Nike Minimalist Editorial Footer */}
        <footer className="border-t border-white/[0.08] bg-black py-10 text-[12px] text-neutral-500">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <p className="text-neutral-400 font-medium">Quantitative Football Prediction Platform</p>
              <p className="text-neutral-600 font-mono text-[11px]">
                Deterministic mathematical modeling · Dixon-Coles Poisson · Path-Dependent Monte Carlo · 15-Gate Filter
              </p>
            </div>
            <div className="flex items-center gap-5 text-neutral-500 font-mono text-[11px]">
              <span>Target: <span className="text-[#d4af37]">1xBet Only</span></span>
              <span>Data: <span className="text-neutral-400">API-Football</span></span>
              <span>Historical: <span className="text-neutral-400">football-data.co.uk</span></span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
