import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    error: 'PREDICTIONS_NOT_AVAILABLE',
    reason: 'No persisted prediction records are currently exposed by this endpoint.',
    data: []
  }, { status: 503, headers: { 'Cache-Control': 'no-store' } })
}
