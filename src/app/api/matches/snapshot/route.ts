import { NextResponse } from 'next/server'
import { isProviderCacheConfigured, readProviderCache } from '@/lib/providerCache'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET() {
  const headers = { 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0' }
  if (!isProviderCacheConfigured()) return NextResponse.json({ error: 'PROVIDER_CACHE_NOT_CONFIGURED' }, { status: 503, headers })

  const now = new Date()
  const from = now.toISOString().slice(0, 10)
  const to = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  try {
    const cached = await readProviderCache<{ fixtures: unknown[]; syncedAt: string; source: string }>(`fixtures:PL:${from}:${to}`)
    if (!cached) return NextResponse.json({ fixtures: [], syncedAt: null, source: null }, { headers })
    return NextResponse.json({ ...cached.payload, syncedAt: cached.syncedAt, cached: true }, { headers })
  } catch {
    return NextResponse.json({ error: 'PROVIDER_CACHE_UNAVAILABLE' }, { status: 503, headers })
  }
}
