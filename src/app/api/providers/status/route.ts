import { NextResponse } from 'next/server'
import { isProviderCacheConfigured, readProviderMonthlyRequestCount, readProviderQuota } from '@/lib/providerCache'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET() {
  const footballDataConfigured = Boolean(process.env.FOOTBALL_DATA_ORG_TOKEN)
  const oddsApiConfigured = Boolean(process.env.ODDS_API_KEY)
  let oddsQuota = null
  let monthlyRequests = { 'football-data.org': null as number | null, 'the-odds-api': null as number | null }
  if (isProviderCacheConfigured()) {
    const [quota, footballRequests, oddsRequests] = await Promise.allSettled([
      readProviderQuota('the-odds-api'),
      readProviderMonthlyRequestCount('football-data.org'),
      readProviderMonthlyRequestCount('the-odds-api'),
    ])
    if (quota.status === 'fulfilled') oddsQuota = quota.value
    if (footballRequests.status === 'fulfilled') monthlyRequests['football-data.org'] = footballRequests.value
    if (oddsRequests.status === 'fulfilled') monthlyRequests['the-odds-api'] = oddsRequests.value
  }
  return NextResponse.json({
    sharedCacheConfigured: isProviderCacheConfigured(),
    oddsQuota,
    monthlyRequests,
    providers: [{
      provider: 'football-data.org',
      configured: footballDataConfigured,
      reachable: null,
      liveScoresRealtime: false,
      fixtureSupport: footballDataConfigured ? ['competitions available on the account'] : [],
      note: footballDataConfigured
        ? 'Token configured. Free-tier scores may be delayed; reachability is not probed here.'
        : 'FOOTBALL_DATA_ORG_TOKEN is not configured.'
    }, {
      provider: 'the-odds-api',
      configured: oddsApiConfigured,
      reachable: null,
      liveOddsSupported: null,
      prematchSupported: oddsApiConfigured,
      bookmakerConfirmed: false,
      note: oddsApiConfigured
        ? 'Key configured. Quotes are requested only from an eligible match terminal; no bookmaker quote is confirmed until a provider response is received.'
        : 'ODDS_API_KEY is not configured.'
    }]
  }, { headers: { 'Cache-Control': 'no-store' } })
}
