import { NextResponse } from 'next/server'
import { fetchApiFootball, extractProviderForecast } from '@/lib/apiFootball'

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  const fixtureId = Number(params.id)
  if (!Number.isInteger(fixtureId) || fixtureId <= 0) {
    return NextResponse.json({ error: 'Invalid fixture id.' }, { status: 400 })
  }

  try {
    const response = await fetchApiFootball(`/predictions?fixture=${fixtureId}`, true)
    return NextResponse.json({
      fixtureId,
      source: 'API-Football provider forecast',
      forecast: extractProviderForecast(response),
      rawAvailable: Boolean(response?.response?.length),
    })
  } catch (error) {
    console.error(`[MATCH PREDICTIONS] Failed for fixture ${fixtureId}`, error)
    return NextResponse.json(
      { fixtureId, source: null, forecast: null, rawAvailable: false },
      { status: 502 },
    )
  }
}
