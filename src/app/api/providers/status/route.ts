import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // In a real implementation this would call the Python engine endpoint
    const response = {
      providers: [{
        provider: "api-football",
        authenticated: true,
        reachable: true,
        live_odds_supported: true,
        prematch_supported: true,
        request_limit: 100,
        requests_remaining: 100,
        last_success: new Date().toISOString(),
        last_error: null,
        supported_markets: ["1x2", "double_chance"],
        is_1xbet_confirmed: true
      }]
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
