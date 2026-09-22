import './globals.css'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'

export const metadata = {
  title: 'Football Intelligence | 1xBet Market Terminal',
  description: 'Pre-match and in-play market intelligence for 1xBet fixtures'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090c10] text-[#f0f4fc] min-h-screen flex antialiased selection:bg-[#d4af37] selection:text-black">
        {/* Left Navigation Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 pl-64">
          {/* Top Sticky Header */}
          <Header />

          {/* Page Body */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-6 sm:px-8 py-8">
            {children}
          </main>

          {/* Minimalist Editorial Footer */}
          <footer className="border-t border-[#1e2638] bg-[#090c10] py-6 text-xs text-[#8a99ad]">
            <div className="max-w-7xl mx-auto px-6 sm:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <p className="text-[#f0f4fc] font-semibold text-xs">
                  Football Intelligence Terminal
                </p>
                <p className="text-[#56657a] font-mono text-[11px]">
                  Real-time market evaluation and verified lineup intelligence
                </p>
              </div>
              <div className="flex items-center gap-4 text-[#8a99ad] font-mono text-[11px]">
                <span>
                  Market: <strong className="text-[#d4af37] font-semibold">1xBet Fixed Odds</strong>
                </span>
                <span>·</span>
                <span>
                  Timings: <strong className="text-[#f0f4fc]">IST (UTC+5:30)</strong>
                </span>
                <span>·</span>
                <span>
                  Status: <strong className="text-[#10b981]">Active</strong>
                </span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
