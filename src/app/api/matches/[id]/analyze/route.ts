import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json({
    error: 'ANALYSIS_NOT_AVAILABLE',
    reason: 'The statistical analysis pipeline is not yet connected to a persisted fixture and validated model state. No analysis was fabricated or queued.'
  }, { status: 503, headers: { 'Cache-Control': 'no-store' } })
}
