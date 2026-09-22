import './globals.css'
import Link from 'next/link'
import EngineStatus from '../components/dashboard/EngineStatus'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-900 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 p-4">
          <div className="flex justify-between items-center max-w-7xl mx-auto">
            <div className="space-x-4">
              <Link href="/">Home</Link>
              <Link href="/predictions">Predictions</Link>
              <Link href="/analytics">Analytics</Link>
              <Link href="/providers">Providers</Link>
            </div>
            <EngineStatus />
          </div>
        </nav>
        <main className="max-w-7xl mx-auto p-4">{children}</main>
      </body>
    </html>
  )
}
