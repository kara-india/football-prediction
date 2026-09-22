import os
import json

base_dir = r'c:\Users\Karan Jha\antigravity\scratch\football-prediction'

def create_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

# package.json
create_file('package.json', json.dumps({
  "name": "football-prediction",
  "version": "0.1.0",
  "private": True,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "@supabase/ssr": "^0.3.0",
    "@supabase/supabase-js": "^2.43.0",
    "clsx": "^2.1.1",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.378.0",
    "next": "14.2.3",
    "react": "^18",
    "react-dom": "^18",
    "recharts": "^2.12.7",
    "tailwind-merge": "^2.3.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "eslint": "^8",
    "eslint-config-next": "14.2.3",
    "postcss": "^8",
    "tailwindcss": "^3.4.1",
    "typescript": "^5"
  }
}, indent=2))

# next.config.ts
create_file('next.config.ts', '''import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
''')

# tsconfig.json
create_file('tsconfig.json', json.dumps({
  "compilerOptions": {
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
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}, indent=2))

# tailwind.config.ts
create_file('tailwind.config.ts', '''import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
    },
  },
  plugins: [],
};
export default config;
''')

# postcss.config.js
create_file('postcss.config.js', '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''')

# .gitignore
create_file('.gitignore', '''# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local
.env
.env.development.local
.env.test.local
.env.production.local

# python
__pycache__/
*.py[cod]
*.class
venv/
env/
.env
.venv/
dist/
build/
''')

# .env.example
create_file('.env.example', '''NEXT_PUBLIC_SUPABASE_URL=https://qqcxjjkgvqknesrtnwal.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh
SUPABASE_SERVICE_ROLE_KEY=  # server-only, never in NEXT_PUBLIC_
API_FOOTBALL_KEY=  # free tier API-Football key
ODDS_API_KEY=  # free tier odds provider key
NEXT_PUBLIC_APP_URL=http://localhost:3000
PYTHON_ENGINE_URL=http://localhost:8001
''')

# .env.local
create_file('.env.local', '''NEXT_PUBLIC_SUPABASE_URL=https://qqcxjjkgvqknesrtnwal.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh
''')

# src/app/layout.tsx
create_file('src/app/layout.tsx', '''import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Football Prediction Platform",
  description: "AI-powered football predictions",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
''')

# src/app/page.tsx
create_file('src/app/page.tsx', '''import React from 'react';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1>Football Prediction Platform</h1>
    </main>
  );
}
''')

# src/app/globals.css
create_file('src/app/globals.css', '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #ffffff;
  --foreground: #171717;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
}

body {
  color: var(--foreground);
  background: var(--background);
}
''')

# src/lib/supabase/client.ts
create_file('src/lib/supabase/client.ts', '''import { createBrowserClient } from '@supabase/ssr'
import { Database } from './types'

export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  )
}
''')

# src/lib/supabase/server.ts
create_file('src/lib/supabase/server.ts', '''import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { Database } from './types'

export function createClient() {
  const cookieStore = cookies()

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value, ...options })
          } catch (error) {
            // The set method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
        remove(name: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value: '', ...options })
          } catch (error) {
            // The delete method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    }
  )
}
''')

# src/lib/supabase/types.ts
create_file('src/lib/supabase/types.ts', '''export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      competitions: {
        Row: { id: number; name: string; type: string }
        Insert: { id: number; name: string; type: string }
        Update: { id?: number; name?: string; type?: string }
      }
      teams: {
        Row: { id: number; name: string }
        Insert: { id: number; name: string }
        Update: { id?: number; name?: string }
      }
      players: {
        Row: { id: number; name: string }
        Insert: { id: number; name: string }
        Update: { id?: number; name?: string }
      }
      matches: {
        Row: { id: number; home_team_id: number; away_team_id: number; start_time: string }
        Insert: { id: number; home_team_id: number; away_team_id: number; start_time: string }
        Update: { id?: number; home_team_id?: number; away_team_id?: number; start_time?: string }
      }
      lineups: {
        Row: { match_id: number; team_id: number; player_id: number; is_starting: boolean }
        Insert: { match_id: number; team_id: number; player_id: number; is_starting: boolean }
        Update: { match_id?: number; team_id?: number; player_id?: number; is_starting?: boolean }
      }
      match_events: {
        Row: { id: number; match_id: number; type: string; minute: number }
        Insert: { id?: number; match_id: number; type: string; minute: number }
        Update: { id?: number; match_id?: number; type?: string; minute?: number }
      }
      team_snapshots: {
        Row: { id: number; team_id: number; date: string; data: Json }
        Insert: { id?: number; team_id: number; date: string; data: Json }
        Update: { id?: number; team_id?: number; date?: string; data?: Json }
      }
      player_snapshots: {
        Row: { id: number; player_id: number; date: string; data: Json }
        Insert: { id?: number; player_id: number; date: string; data: Json }
        Update: { id?: number; player_id?: number; date?: string; data?: Json }
      }
      odds_providers: {
        Row: { id: number; name: string }
        Insert: { id?: number; name: string }
        Update: { id?: number; name?: string }
      }
      provider_usage: {
        Row: { id: number; provider_id: number; count: number; date: string }
        Insert: { id?: number; provider_id: number; count: number; date: string }
        Update: { id?: number; provider_id?: number; count?: number; date?: string }
      }
      odds_snapshots: {
        Row: { id: number; match_id: number; provider_id: number; data: Json; timestamp: string }
        Insert: { id?: number; match_id: number; provider_id: number; data: Json; timestamp: string }
        Update: { id?: number; match_id?: number; provider_id?: number; data?: Json; timestamp?: string }
      }
      market_definitions: {
        Row: { id: number; name: string }
        Insert: { id?: number; name: string }
        Update: { id?: number; name?: string }
      }
      market_outcomes: {
        Row: { id: number; market_id: number; outcome: string }
        Insert: { id?: number; market_id: number; outcome: string }
        Update: { id?: number; market_id?: number; outcome?: string }
      }
      feature_snapshots: {
        Row: { id: number; match_id: number; features: Json }
        Insert: { id?: number; match_id: number; features: Json }
        Update: { id?: number; match_id?: number; features?: Json }
      }
      model_versions: {
        Row: { id: number; version: string; description: string }
        Insert: { id?: number; version: string; description: string }
        Update: { id?: number; version?: string; description?: string }
      }
      calibration_versions: {
        Row: { id: number; version: string; data: Json }
        Insert: { id?: number; version: string; data: Json }
        Update: { id?: number; version?: string; data?: Json }
      }
      prediction_models: {
        Row: { id: number; name: string }
        Insert: { id?: number; name: string }
        Update: { id?: number; name?: string }
      }
      model_predictions: {
        Row: { id: number; match_id: number; model_id: number; prediction: Json }
        Insert: { id?: number; match_id: number; model_id: number; prediction: Json }
        Update: { id?: number; match_id?: number; model_id?: number; prediction?: Json }
      }
      prediction_results: {
        Row: { id: number; prediction_id: number; result: string }
        Insert: { id?: number; prediction_id: number; result: string }
        Update: { id?: number; prediction_id?: number; result?: string }
      }
      prediction_errors: {
        Row: { id: number; prediction_id: number; error: number }
        Insert: { id?: number; prediction_id: number; error: number }
        Update: { id?: number; prediction_id?: number; error?: number }
      }
      paper_bets: {
        Row: { id: number; match_id: number; amount: number; odds: number }
        Insert: { id?: number; match_id: number; amount: number; odds: number }
        Update: { id?: number; match_id?: number; amount?: number; odds?: number }
      }
      paper_bet_settlements: {
        Row: { id: number; bet_id: number; status: string; profit: number }
        Insert: { id?: number; bet_id: number; status: string; profit: number }
        Update: { id?: number; bet_id?: number; status?: string; profit?: number }
      }
      learning_runs: {
        Row: { id: number; model_id: number; date: string }
        Insert: { id?: number; model_id: number; date: string }
        Update: { id?: number; model_id?: number; date?: string }
      }
      model_metrics: {
        Row: { id: number; run_id: number; metrics: Json }
        Insert: { id?: number; run_id: number; metrics: Json }
        Update: { id?: number; run_id?: number; metrics?: Json }
      }
      calibration_bins: {
        Row: { id: number; calibration_id: number; bin: string; value: number }
        Insert: { id?: number; calibration_id: number; bin: string; value: number }
        Update: { id?: number; calibration_id?: number; bin?: string; value?: number }
      }
      worker_runs: {
        Row: { id: number; worker_name: string; status: string; timestamp: string }
        Insert: { id?: number; worker_name: string; status: string; timestamp: string }
        Update: { id?: number; worker_name?: string; status?: string; timestamp?: string }
      }
      engine_settings: {
        Row: { key: string; value: string }
        Insert: { key: string; value: string }
        Update: { key?: string; value?: string }
      }
    }
  }
}
''')

# src/lib/utils.ts
create_file('src/lib/utils.ts', '''import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
''')

# src/lib/constants.ts
create_file('src/lib/constants.ts', '''export const COMPETITIONS = [
  { name: 'England Premier League', league_id: 39 },
  { name: 'Brazil Serie A', league_id: 71 },
  { name: 'Italy Serie A', league_id: 135 },
  { name: 'Spain La Liga', league_id: 140 },
  { name: 'Germany Bundesliga', league_id: 78 },
  { name: 'France Ligue 1', league_id: 61 },
  { name: 'Portugal Primeira Liga', league_id: 94 },
  { name: 'Netherlands Eredivisie', league_id: 88 },
  { name: 'Argentina Liga Profesional', league_id: 128 },
  { name: 'Belgium First Division A', league_id: 144 },
  { name: 'UEFA Champions League', league_id: 2 },
  { name: 'UEFA Europa League', league_id: 3 },
  { name: 'FIFA World Cup', league_id: 1 },
  { name: 'World Cup Qualifiers', league_ids: [31,32,29,30,33,34] },
  { name: 'UEFA Euro', league_id: 4 },
  { name: 'UEFA Nations League', league_id: 5 },
  { name: 'Copa America', league_id: 9 },
  { name: 'AFCON', league_id: 6 },
  { name: 'AFC Asian Cup', league_id: 7 },
  { name: 'CONCACAF', league_ids: [16,26] },
  { name: 'International Friendlies senior men', league_id: 10 }
];

export const MARKETS = [
  '1X2', 'Over/Under 2.5', 'BTTS'
];

export const NO_BET_REASONS = [
  'Low Liquidity', 'Missing Data', 'Odds Discrepancy', 'High Variance'
];
''')

# src/types/index.ts
create_file('src/types/index.ts', '''export interface Prediction {
  homeWin: number;
  draw: number;
  awayWin: number;
}
''')

# python/requirements.txt
create_file('python/requirements.txt', '''numpy==1.26.4
scipy==1.13.1
pandas==2.2.2
scikit-learn==1.5.0
xgboost==2.0.3
lightgbm==4.3.0
fastapi==0.111.0
uvicorn==0.29.0
httpx==0.27.0
pydantic==2.7.1
supabase==2.5.0
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.6
numba==0.59.1
joblib==1.4.2
''')

# python/setup.py
create_file('python/setup.py', '''from setuptools import setup, find_packages

setup(
    name="football_prediction",
    version="0.1",
    packages=find_packages(),
)
''')

# python directories and __init__.py
directories = [
    'python',
    'python/models',
    'python/simulation',
    'python/calibration',
    'python/workers',
    'python/adapters'
]
for d in directories:
    create_file(f'{d}/__init__.py', '')

# python/config.py
create_file('python/config.py', '''import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
''')

# python/models/elo.py
create_file('python/models/elo.py', '''class EloRating:
    def __init__(self, rating=1500, k_factor=20):
        self.rating = rating
        self.k_factor = k_factor

    def get_home_advantage(self):
        return 50

    def predict(self, home_rating, away_rating, is_home=True):
        rating_diff = home_rating - away_rating
        if is_home:
            rating_diff += self.get_home_advantage()
        expected = 1 / (1 + 10 ** (-rating_diff / 400))
        return expected

    def update(self, actual, expected, margin=1):
        self.rating += self.k_factor * margin * (actual - expected)
        return self.rating
        
    def to_dict(self):
        return {"rating": self.rating, "k_factor": self.k_factor}
        
    @classmethod
    def from_dict(cls, data):
        return cls(rating=data["rating"], k_factor=data["k_factor"])
''')

# docs
create_file('docs/architecture.md', '''# Architecture

- System overview: Next.js frontend, Python prediction engine
- Component diagram: Client -> Next.js API -> Supabase / Python Engine
- Data flow: Sync workers -> Supabase -> Model Training -> Predictions
- Provider abstraction: Interface for Odds and Football APIs
- Model pipeline: Feature engineering -> XGBoost/Elo -> Ensemble
- Monte Carlo approach: Match simulations for complex markets
- Calibration approach: Platt scaling / Isotonic regression
- NO-BET gate: Rules engine to prevent betting on low confidence
- Champion/Challenger: Shadow testing of new models
- Security model: RLS in Supabase, API keys in env
- Database design principles: Snapshotting, immutable event logs
''')
create_file('docs/data-sources.md', '# Data Sources\nAPI-Football, The Odds API\n')
create_file('docs/limitations.md', '# Limitations\nMissing player data for minor leagues.\n')
create_file('README.md', '# Football Prediction\n\n## Setup\n
pm install\n
pm run dev\n')

# create shadcn ui components
create_file('src/components/ui/button.tsx', '''import * as React from "react"
export const Button = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className, ...props }, ref) => (
    <button ref={ref} className={className} {...props} />
  )
)
Button.displayName = "Button"
''')
create_file('src/components/ui/card.tsx', '''import * as React from "react"
export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={className} {...props} />
  )
)
Card.displayName = "Card"
''')
create_file('src/components/ui/badge.tsx', '''import * as React from "react"
export const Badge = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={className} {...props} />
)
''')
create_file('src/components/ui/table.tsx', '''import * as React from "react"
export const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className, ...props }, ref) => (
    <table ref={ref} className={className} {...props} />
  )
)
Table.displayName = "Table"
''')
create_file('src/components/ui/tabs.tsx', '''import * as React from "react"
export const Tabs = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={className} {...props} />
)
''')
create_file('src/components/ui/skeleton.tsx', '''import * as React from "react"
export const Skeleton = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={className} {...props} />
)
''')

# empty api route
create_file('src/app/api/.keep', '')

print("Scaffold complete.")
