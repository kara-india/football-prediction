import { NextResponse } from 'next/server'
import { fetchFootball, formatFixture } from '@/lib/feed'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params
  if (!/^\d+$/.test(id)) return NextResponse.json({ error: 'INVALID_FIXTURE_ID' }, { status: 400 })

  const result = await fetchFootball(`/fixtures?id=${id}`, true)
  if (!result.ok) return NextResponse.json({ error: result.reason || 'MATCH_UNAVAILABLE' }, { status: result.status || 502 })
  const fixture = (result.data as any[])[0]
  if (!fixture) return NextResponse.json({ error: 'FIXTURE_NOT_FOUND' }, { status: 404 })

  return NextResponse.json(formatFixture(fixture), {
    headers: { 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0' }
  })
}
