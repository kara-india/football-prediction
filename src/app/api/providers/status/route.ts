import { NextResponse } from 'next/server'

export async function GET() {
  const apiKey = process.env.API_FOOTBALL_KEY
  if (!apiKey) {
    return NextResponse.json(
      {
        provider: 'api-football',
        authenticated: false,
        reachable: false,
        error: 'API_FOOTBALL_KEY environment variable is not configured.',
      },
      { status: 503 },
    )
  }

  try {
    const response = await fetch('https://v3.football.api-sports.io/status', {
      headers: { 'x-apisports-key': apiKey },
      cache: 'no-store',
    })
    const payload = await response.json()
    const subscription = payload?.response?.subscription ?? {}
    const requests = payload?.response?.requests ?? {}

    if (!response.ok || (payload?.errors && Object.keys(payload.errors).length > 0)) {
      const errorDetail = typeof payload?.errors === 'string'
        ? payload.errors
        : JSON.stringify(payload?.errors || `HTTP ${response.status}`)
      return NextResponse.json(
        {
          provider: 'api-football',
          authenticated: false,
          reachable: true,
          error: errorDetail,
        },
        { status: 502 },
      )
    }

    return NextResponse.json({
      provider: 'api-football',
      authenticated: true,
      reachable: true,
      subscription: {
        plan: subscription.plan ?? null,
        active: subscription.active ?? null,
      },
      requests: {
        current: Number.isFinite(Number(requests.current)) ? Number(requests.current) : null,
        dailyLimit: Number.isFinite(Number(requests.limit_day)) ? Number(requests.limit_day) : null,
      },
      checkedAt: new Date().toISOString(),
    })
  } catch (error) {
    return NextResponse.json(
      {
        provider: 'api-football',
        authenticated: false,
        reachable: false,
        error: error instanceof Error ? error.message : 'Provider status check failed',
      },
      { status: 502 },
    )
  }
}
