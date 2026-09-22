import os
import json

def write_file(filepath, content):
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

# 30. src/types/index.ts
types_content = '''
export interface Match {
  id: string;
  competition_id: string;
  home_team_id: string;
  away_team_id: string;
  kickoff_time: string;
  status: string;
  minute?: number;
  home_score?: number;
  away_score?: number;
}

export interface Team {
  id: string;
  name: string;
}

export interface Competition {
  id: string;
  name: string;
}

export interface Player {
  id: string;
  name: string;
}

export interface LiveState {
  possession_home: number;
  possession_away: number;
  shots_home: number;
  shots_away: number;
  shots_on_target_home: number;
  shots_on_target_away: number;
  xg_home: number;
  xg_away: number;
  corners_home: number;
  corners_away: number;
  cards_home: number;
  cards_away: number;
  fouls_home: number;
  fouls_away: number;
}

export interface Lineup {
  match_id: string;
  team_id: string;
  confirmed: boolean;
}

export interface OddsMarket {
  id: string;
  name: string;
}

export interface OddsSnapshot {
  market_id: string;
  selection: string;
  price: number;
  timestamp: string;
}

export interface ModelPrediction {
  id: string;
  match_id: string;
  market_id: string;
  selection: string;
  probability: number;
  model_version: string;
  created_at: string;
}

export interface BetCandidate {
  prediction_id: string;
  ev: number;
  kelly_fraction: number;
  decision: 'HIGH CONFIDENCE CANDIDATE' | 'NO BET';
  no_bet_reason?: string;
}

export interface PredictionResult {
  id: string;
}

export interface PaperBet {
  id: string;
}

export interface ProviderHealth {
  id: string;
  name: string;
  authenticated: boolean;
  reachable: boolean;
  live_support: boolean;
  prematch_support: boolean;
  xbet_confirmed: boolean;
  request_limit: number;
  requests_remaining: number;
  last_success?: string;
  last_error?: string;
  supported_markets: string[];
}

export interface EngineSettings {
  enabled: boolean;
}

export interface WorkerRun {
  id: string;
}

export interface ModelVersion {
  version: string;
  description: string;
}
'''

# package.json
package_json = {
  "name": "football-prediction-frontend",
  "version": "0.1.0",
  "private": True,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@supabase/ssr": "latest",
    "@supabase/supabase-js": "latest",
    "tailwindcss": "^3.3.0",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.3.0"
  }
}

tsconfig_json = {
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": True,
    "skipLibCheck": True,
    "strict": True,
    "noEmit": True,
    "esModuleInterop": True,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": True,
    "isolatedModules": True,
    "jsx": "preserve",
    "incremental": True,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

tailwind_config = '''
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''

# 27. src/lib/supabase/client.ts
client_ts = '''
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  )
}
'''

# 28. src/lib/supabase/server.ts
server_ts = '''
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createServerClientWrapper() {
  const cookieStore = cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!, // Use service role for writes if needed, but not here by default
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: any) {
          try {
            cookieStore.set({ name, value, ...options })
          } catch (error) {}
        },
        remove(name: string, options: any) {
          try {
            cookieStore.set({ name, value: '', ...options })
          } catch (error) {}
        },
      },
    }
  )
}
'''

# 29. src/lib/api.ts
api_ts = '''
export async function fetchLiveMatches() { return [] }
export async function fetchUpcomingMatches() { return [] }
export async function fetchMatch(id: string) { return null }
export async function analyzeMatch(id: string) { return null }
export async function fetchPredictions(filters: any) { return [] }
export async function fetchModels() { return [] }
export async function fetchProviderStatus() { return [] }
export async function toggleEngine(enabled: boolean) { return null }
'''

# 31. src/app/layout.tsx
layout_tsx = '''
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
'''

globals_css = '''
@tailwind base;
@tailwind components;
@tailwind utilities;
'''

page_tsx = '''
import LiveMatchSection from '../components/dashboard/LiveMatchSection'
import UpcomingMatchSection from '../components/dashboard/UpcomingMatchSection'

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <LiveMatchSection />
      <UpcomingMatchSection />
    </div>
  )
}
'''

match_id_page_tsx = '''
import MatchHeader from '../../../components/match/MatchHeader'
import OddsPanel from '../../../components/match/OddsPanel'
import LiveStatePanel from '../../../components/match/LiveStatePanel'
import ModelPanel from '../../../components/match/ModelPanel'
import MarketTable from '../../../components/match/MarketTable'

export default function MatchIntelligence({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <MatchHeader matchId={params.id} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <LiveStatePanel />
        <OddsPanel />
      </div>
      <ModelPanel />
      <MarketTable />
    </div>
  )
}
'''

predictions_page_tsx = '''
export default function Predictions() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Prediction History</h1>
      <div>Table Placeholder</div>
    </div>
  )
}
'''

analytics_page_tsx = '''
import MetricsSummary from '../../components/analytics/MetricsSummary'
import CalibrationChart from '../../components/analytics/CalibrationChart'
import PLChart from '../../components/analytics/PLChart'

export default function Analytics() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Learning Dashboard</h1>
      <MetricsSummary />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CalibrationChart />
        <PLChart />
      </div>
    </div>
  )
}
'''

providers_page_tsx = '''
export default function Providers() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Provider Health</h1>
      <div>Providers Placeholder</div>
    </div>
  )
}
'''

components = {
  "src/components/dashboard/MatchCard.tsx": "export default function MatchCard() { return <div>MatchCard</div> }",
  "src/components/dashboard/EngineStatus.tsx": "export default function EngineStatus() { return <div>Engine: ON</div> }",
  "src/components/dashboard/LiveMatchSection.tsx": "export default function LiveMatchSection() { return <div>Live Matches</div> }",
  "src/components/dashboard/UpcomingMatchSection.tsx": "export default function UpcomingMatchSection() { return <div>Upcoming Matches</div> }",
  "src/components/match/MatchHeader.tsx": "export default function MatchHeader({ matchId }: { matchId: string }) { return <div>Match Header {matchId}</div> }",
  "src/components/match/OddsPanel.tsx": "export default function OddsPanel() { return <div>Odds Panel</div> }",
  "src/components/match/LiveStatePanel.tsx": "export default function LiveStatePanel() { return <div>Live State</div> }",
  "src/components/match/ModelPanel.tsx": "export default function ModelPanel() { return <div>Model Panel</div> }",
  "src/components/match/MarketTable.tsx": "export default function MarketTable() { return <div>Market Table</div> }",
  "src/components/analytics/CalibrationChart.tsx": "export default function CalibrationChart() { return <div>Calibration</div> }",
  "src/components/analytics/PLChart.tsx": "export default function PLChart() { return <div>P&L Chart</div> }",
  "src/components/analytics/MetricsSummary.tsx": "export default function MetricsSummary() { return <div>Metrics</div> }",
  "src/components/common/DataFreshnessIndicator.tsx": "export default function DataFreshnessIndicator() { return <div>Freshness</div> }",
  "src/components/common/DecisionBadge.tsx": "export default function DecisionBadge() { return <div>Decision</div> }",
}

api_routes = {
  "src/app/api/matches/live/route.ts": "import { NextResponse } from 'next/server'; export async function GET() { return NextResponse.json([]) }",
  "src/app/api/matches/upcoming/route.ts": "import { NextResponse } from 'next/server'; export async function GET() { return NextResponse.json([]) }",
  "src/app/api/matches/[id]/route.ts": "import { NextResponse } from 'next/server'; export async function GET() { return NextResponse.json({}) }",
  "src/app/api/matches/[id]/analyze/route.ts": "import { NextResponse } from 'next/server'; export async function POST() { return NextResponse.json({status: 'queued'}) }",
  "src/app/api/matches/[id]/predictions/route.ts": "import { NextResponse } from 'next/server'; export async function GET() { return NextResponse.json([]) }",
  "src/app/api/predictions/route.ts": "import { NextResponse } from 'next/server'; export async function GET() { return NextResponse.json([]) }",
  "src/app/api/models/route.ts": "import { NextResponse } from 'next/server'; export async function GET() { return NextResponse.json([]) }",
}

write_file('package.json', json.dumps(package_json, indent=2))
write_file('tsconfig.json', json.dumps(tsconfig_json, indent=2))
write_file('tailwind.config.js', tailwind_config)
write_file('src/types/index.ts', types_content)
write_file('src/lib/supabase/client.ts', client_ts)
write_file('src/lib/supabase/server.ts', server_ts)
write_file('src/lib/api.ts', api_ts)
write_file('src/app/layout.tsx', layout_tsx)
write_file('src/app/globals.css', globals_css)
write_file('src/app/page.tsx', page_tsx)
write_file('src/app/matches/[id]/page.tsx', match_id_page_tsx)
write_file('src/app/predictions/page.tsx', predictions_page_tsx)
write_file('src/app/analytics/page.tsx', analytics_page_tsx)
write_file('src/app/providers/page.tsx', providers_page_tsx)

for path, content in components.items():
    write_file(path, content)

for path, content in api_routes.items():
    write_file(path, content)

print('Done creating files')
