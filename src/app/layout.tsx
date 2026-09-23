import './globals.css'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'

export const metadata = {
  title: 'Football Intelligence Terminal | 1xBet Quantitative Engine',
  description: 'Institutional pre-match and in-play market intelligence with verified lineup governance',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B0F17] text-[#F8FAFC] min-h-screen flex antialiased selection:bg-[#D4AF37] selection:text-black">
        {/* Left Navigation Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 lg:pl-64 pl-0 transition-all duration-200">
          {/* Top Sticky Header */}
          <Header />

          {/* Page Body */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            {children}
          </main>

          {/* Minimalist Institutional Terminal Footer */}
          <footer className="border-t border-[#1E293B] bg-[#0B0F17] py-6 text-xs text-[#94A3B8]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <p className="text-[#F8FAFC] font-semibold text-xs tracking-tight">
                  Football Intelligence Terminal
                </p>
                <p className="text-[#64748B] font-mono text-[11px]">
                  Prequential Monte Carlo simulation • 1xBet fixed clearing prices • Starting XI verification
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-[#94A3B8] font-mono text-[11px]">
                <span>
                  Clearing: <strong className="text-[#D4AF37] font-semibold">1xBet Fixed</strong>
                </span>
                <span className="text-[#334155]">·</span>
                <span>
                  Clock: <strong className="text-[#F8FAFC]">IST (UTC+5:30)</strong>
                </span>
                <span className="text-[#334155]">·</span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block animate-pulse" />
                  <span className="text-[#10B981] font-medium">Operational</span>
                </span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
