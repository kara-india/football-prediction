import './globals.css'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'

export const metadata = {
  title: 'Football Intelligence | 1xBet Quantitative Analytics',
  description: 'Production statistical prediction and betting intelligence engine for 1xBet markets'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090c10] text-[#f0f4fc] min-h-screen flex antialiased selection:bg-[#d4af37] selection:text-black">
        {/* Mixpanel Left Navigation Sidebar */}
        <Sidebar />

        {/* Main Content Area (offset by sidebar width) */}
        <div className="flex-1 flex flex-col min-w-0 pl-64">
          {/* Top Sticky Header */}
          <Header />

          {/* Page Body */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-6 sm:px-8 py-8">
            {children}
          </main>

          {/* Mixpanel Minimalist Editorial Footer */}
          <footer className="border-t border-[#1e2638] bg-[#090c10] py-8 text-xs text-[#8a99ad]">
            <div className="max-w-7xl mx-auto px-6 sm:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <p className="text-[#f0f4fc] font-semibold text-xs">
                  1xBet Quantitative Intelligence Engine
                </p>
                <p className="text-[#56657a] font-mono text-[11px]">
                  Dixon-Coles Bivariate Poisson · Path-Dependent Monte Carlo · 15-Gate Validation Filter
                </p>
              </div>
              <div className="flex items-center gap-4 text-[#8a99ad] font-mono text-[11px]">
                <span>
                  Target: <strong className="text-[#d4af37] font-semibold">1xBet Fixed</strong>
                </span>
                <span>·</span>
                <span>
                  Historical: <strong className="text-[#f0f4fc]">football-data.co.uk 5Y</strong>
                </span>
                <span>·</span>
                <span>
                  Quota: <strong className="text-[#10b981]">₹0.00 Exp (100% Free)</strong>
                </span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
