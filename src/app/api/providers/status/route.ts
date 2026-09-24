import { NextResponse } from 'next/server'

export async function GET() {
  const configured = Boolean(process.env.API_FOOTBALL_KEY)
  return NextResponse.json({
    providers: [{
      provider: 'api-football',
      configured,
      reachable: null,
      live_odds_supported: null,
      prematch_supported: configured,
      is_1xbet_confirmed: false,
      note: configured
        ? 'Credentials are configured. Reachability is not probed by this status endpoint to avoid consuming quota.'
        : 'API_FOOTBALL_KEY is not configured.'
    }]
  }, { headers: { 'Cache-Control': 'no-store' } })
}
