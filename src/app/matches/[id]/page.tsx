'use client'

import React, { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import MatchHeader from '@/components/match/MatchHeader'
import TacticalPitchGrid, { TeamLineupData, PitchPlayer } from '@/components/ui/terminal/TacticalPitchGrid'
import OddsPanel from '@/components/match/OddsPanel'
import MarketTable, { MarketRow } from '@/components/match/MarketTable'
import TerminalCard from '@/components/ui/terminal/TerminalCard'
import { MarketExecutionData } from '@/components/match/TriColumnMatrix'

interface MatchDetail {
  fixture: {
    id: number
    kickoff: string
    venue: string
    status: string
    statusLong: string
    minute: number | null
    referee: string | null
    league: any
    teams: any
    score: any
    events: any[]
    statistics: any[]
    lineups: any[]
  }
  odds1xBet: {
    home: number | null
    draw: number | null
    away: number | null
    over25: number | null
    under25: number | null
  } | null
  oddsUpdatedAt: string | null
  forecast: {
    home: number | null
    draw: number | null
    away: number | null
    winnerName: string | null
    winnerId: number | null
    goalsHome: number | null
    goalsAway: number | null
  } | null
  forecastSource: string | null
  history: Array<{
    id: number
    date: string
    status: string
    homeTeam: string
    awayTeam: string
    homeScore: number | null
    awayScore: number | null
  }>
  generatedAt: string
  championDecision?: {
    model: 'CHAMPION'
    version: string
    action: 'BET' | 'NO_BET'
    confidence: number | null
    selection: string | null
    label: string | null
    market: 'MATCH_1X2' | 'TOTAL_GOALS_2_5' | null
    odds: number | null
    fairOdds: number | null
    modelProbability: number | null
    impliedProbability: number | null
    devigProbability: number | null
    edge: number | null
    expectedValue: number | null
    reason: string
    checkedAt: string
  }
}


function extractTeamStatistic(statistics: any[], teamId: number, names: RegExp[]): number | null {
  const teamBlock = (statistics || []).find((item: any) => Number(item?.team?.id) === Number(teamId))
  const stat = (teamBlock?.statistics || []).find((item: any) =>
    names.some((pattern) => pattern.test(String(item?.type || ''))),
  )
  if (stat?.value === null || stat?.value === undefined) return null
  const numeric = Number(String(stat.value).replace('%', '').trim())
  return Number.isFinite(numeric) ? numeric : null
}

function probability(value: number | null | undefined): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function pct(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value)
    ? `${(value * 100).toFixed(1)}%`
    : '—'
}

function asPlayer(player: any, fallbackId: string): PitchPlayer {
  const rawPosition = String(player?.pos || '').toUpperCase()
  const position =
    rawPosition === 'G' || /GK|GOALKEEPER/.test(rawPosition)
      ? 'G'
      : /D|DEF/.test(rawPosition)
        ? 'D'
        : /M|MID/.test(rawPosition)
          ? 'M'
          : /F|FW|ATT/.test(rawPosition)
            ? 'F'
            : rawPosition || '—'

  return {
    id: player?.id ?? fallbackId,
    name: player?.name || 'Unknown player',
    number: Number(player?.number) || 0,
    position,
  }
}

function teamLineup(lineups: any[], teamId: number, teamName: string): TeamLineupData {
  const block = (lineups || []).find((item: any) => Number(item?.team?.id) === Number(teamId))
  return {
    name: teamName,
    formation: block?.formation || 'TBD',
    starters: (block?.startXI || []).map((item: any, index: number) =>
      asPlayer(item?.player, `starter-${teamId}-${index}`),
    ),
    substitutes: (block?.substitutes || []).map((item: any, index: number) =>
      asPlayer(item?.player, `sub-${teamId}-${index}`),
    ),
    coach: block?.coach?.name || undefined,
  }
}

function statLabel(value: any): string {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

export default function MatchIntelligencePage({ params }: { params: { id: string } }) {
  const matchId = params.id
  const [detail, setDetail] = useState<MatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDetail = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/matches/${encodeURIComponent(matchId)}`, { cache: 'no-store' })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload?.error || 'Match detail unavailable')
      }
      setDetail(payload)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Match detail unavailable')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDetail()
  }, [matchId])

  const fixture = detail?.fixture
  const home = fixture?.teams?.home
  const away = fixture?.teams?.away
  const forecast = detail?.forecast
  const odds = detail?.odds1xBet
  const champion = detail?.championDecision
  const lineups = fixture?.lineups ?? []

  const lineupConfirmed = useMemo(
    () =>
      Boolean(
        lineups.length >= 2 &&
        lineups.every((item: any) => (item?.startXI || []).length === 11),
      ),
    [lineups],
  )

  const homeLineup = fixture && home
    ? teamLineup(lineups, Number(home.id), home.name)
    : { name: 'Home', starters: [], substitutes: [], formation: 'TBD' }

  const awayLineup = fixture && away
    ? teamLineup(lineups, Number(away.id), away.name)
    : { name: 'Away', starters: [], substitutes: [], formation: 'TBD' }

  const homeProb = probability(forecast?.home)
  const drawProb = probability(forecast?.draw)
  const awayProb = probability(forecast?.away)

  const marketData: MarketExecutionData = {
    bookmaker: '1xBet',
    homeOdds: odds?.home ?? null,
    drawOdds: odds?.draw ?? null,
    awayOdds: odds?.away ?? null,
    over25Odds: odds?.over25 ?? null,
    under25Odds: odds?.under25 ?? null,
    overround:
      odds?.home && odds?.draw && odds?.away
        ? 1 / odds.home + 1 / odds.draw + 1 / odds.away - 1
        : null,
    targetSelectionOdds: null,
    impliedProb: null,
    deviggedProb: null,
    valueEdge: null,
    expectedValue: null,
    oddsFreshnessTimestamp: detail?.oddsUpdatedAt || undefined,
    status: odds ? 'ACTIVE' : 'UNAVAILABLE',
  }

  const markets: MarketRow[] = useMemo(() => {
    const rows: MarketRow[] = []
    const values = [
      { id: 'home', label: '1 (' + (home?.name || 'Home') + ')', selection: '1', odds: odds?.home, model: homeProb },
      { id: 'draw', label: 'X (Draw)', selection: 'X', odds: odds?.draw, model: drawProb },
      { id: 'away', label: '2 (' + (away?.name || 'Away') + ')', selection: '2', odds: odds?.away, model: awayProb },
    ]

    for (const item of values) {
      const championMatch = champion?.market === 'MATCH_1X2' && champion.selection === item.selection
      const model = championMatch && champion.modelProbability !== null ? champion.modelProbability : item.model
      const implied = item.odds && item.odds > 1 ? 1 / item.odds : null
      const edge = championMatch && champion.edge !== null
        ? champion.edge * 100
        : implied !== null && Number.isFinite(model) ? (model - implied) * 100 : null
      const ev = championMatch && champion.expectedValue !== null
        ? champion.expectedValue * 100
        : item.odds && Number.isFinite(model) ? (model * item.odds - 1) * 100 : null
      rows.push({
        id: '1x2-' + item.id,
        outcome: item.label,
        market: '1X2 Match Winner',
        odds1xBet: item.odds ?? null,
        impliedProb: implied,
        deviggedProb: championMatch ? champion.devigProbability : null,
        modelProb: model,
        edge,
        ev,
        decisionCode: championMatch ? 'CHAMPION_BET' : 'NO_BET',
        action: championMatch ? 'CANDIDATE' : 'NO_BET',
      })
    }

    const totals = [
      { id: 'over25', label: 'Over 2.5 Goals', selection: 'OVER', odds: odds?.over25 },
      { id: 'under25', label: 'Under 2.5 Goals', selection: 'UNDER', odds: odds?.under25 },
    ]
    for (const item of totals) {
      const championMatch = champion?.market === 'TOTAL_GOALS_2_5' && champion.selection === item.selection
      const model = championMatch && champion.modelProbability !== null ? champion.modelProbability : 0
      const implied = item.odds && item.odds > 1 ? 1 / item.odds : null
      rows.push({
        id: 'ou-' + item.id,
        outcome: item.label,
        market: 'Total Goals 2.5',
        odds1xBet: item.odds ?? null,
        impliedProb: implied,
        deviggedProb: championMatch ? champion.devigProbability : null,
        modelProb: model,
        edge: championMatch && champion.edge !== null ? champion.edge * 100 : null,
        ev: championMatch && champion.expectedValue !== null ? champion.expectedValue * 100 : null,
        decisionCode: championMatch ? 'CHAMPION_BET' : 'NO_BET',
        action: championMatch ? 'CANDIDATE' : 'NO_BET',
      })
    }

    return rows
  }, [away?.name, awayProb, champion, drawProb, home?.name, homeProb, odds?.away, odds?.draw, odds?.home, odds?.over25, odds?.under25])

  const matchStats = useMemo(() => {
    if (!fixture || !home || !away) return []

    const stats = fixture.statistics || []
    const definitions = [
      ['Ball Possession', [/ball possession/i]],
      ['Total Shots', [/total shots/i]],
      ['Shots on Target', [/shots on goal|shots on target/i]],
      ['Corner Kicks', [/corner kicks|corners/i]],
      ['Fouls', [/fouls/i]],
      ['Yellow Cards', [/yellow cards/i]],
      ['Red Cards', [/red cards/i]],
      ['Expected Goals', [/expected goals|xg/i]],
    ]

    return definitions.map(([label, patterns]) => ({
      label: String(label),
      home: extractTeamStatistic(stats, Number(home.id), patterns as RegExp[]),
      away: extractTeamStatistic(stats, Number(away.id), patterns as RegExp[]),
    }))
  }, [fixture, home, away])

  if (loading) {
    return (
      <TerminalCard title="Match Terminal" subtitle={`Loading fixture ${matchId}`}>
        <div className="p-12 text-center text-sm font-mono text-[#94A3B8]">Synchronizing match state…</div>
      </TerminalCard>
    )
  }

  if (error || !fixture || !home || !away) {
    return (
      <TerminalCard title="Match Terminal" subtitle={`Fixture ${matchId}`}>
        <div className="p-10 text-center space-y-3">
          <div className="text-[#F8FAFC] font-semibold">Match data unavailable</div>
          <div className="text-xs font-mono text-[#94A3B8]">{error || 'No fixture data returned.'}</div>
          <button
            onClick={loadDetail}
            className="px-3 py-2 rounded-lg bg-[#1E293B] text-xs font-mono text-[#F8FAFC]"
          >
            Retry
          </button>
        </div>
      </TerminalCard>
    )
  }

  const live = ['1H', '2H', 'HT', 'ET', 'LIVE'].includes(fixture.status)
  const isFinished = ['FT', 'AET', 'PEN'].includes(fixture.status)

  return (
    <div className="space-y-6">
      <MatchHeader
        matchId={matchId}
        homeTeam={{ name: home.name, logo: home.logo, score: fixture.score?.home ?? undefined }}
        awayTeam={{ name: away.name, logo: away.logo, score: fixture.score?.away ?? undefined }}
        competition={{
          name: fixture.league?.name || 'Competition',
          country: fixture.league?.country,
          logo: fixture.league?.logo,
          round: fixture.league?.round,
        }}
        status={fixture.status}
        minute={fixture.minute ?? undefined}
        kickoffUtc={fixture.kickoff}
        venue={fixture.venue}
        referee={fixture.referee || 'Not supplied by provider'}
        onRefresh={loadDetail}
      />

      <TerminalCard
        title="CHAMPION — Live Bet Decision"
        subtitle="Authoritative decision layer: only real, fresh 1xBet prices that clear the confidence and value gates are actionable."
        badge={
          <span className={champion?.action === 'BET' ? 'px-2 py-0.5 rounded border text-[10px] font-mono font-bold border-[#10B981]/40 bg-[#10B981]/15 text-[#10B981]' : 'px-2 py-0.5 rounded border text-[10px] font-mono font-bold border-[#64748B]/40 bg-[#64748B]/10 text-[#94A3B8]'}>
            {champion?.action === 'BET' ? 'BET' : 'NO BET'}
          </span>
        }
        padding="none"
      >
        <div className="p-5">
          {champion?.action === 'BET' ? (
            <div className="rounded-xl border border-[#10B981]/30 bg-[#10B981]/5 p-5">
              <div className="text-[10px] uppercase tracking-widest text-[#64748B] font-mono">Optimal live market</div>
              <div className="text-2xl sm:text-3xl font-black text-[#F8FAFC] mt-2">{champion.label}</div>
              <div className="flex flex-wrap items-center gap-3 mt-3 font-mono">
                <span className="text-[#D4AF37] font-bold text-lg">1xBet {champion.odds?.toFixed(2)}</span>
                <span className="text-[#10B981] font-bold">{champion.confidence !== null ? (champion.confidence * 100).toFixed(1) + '% confidence' : '—'}</span>
                <span className="text-[#10B981]">EV {champion.expectedValue !== null ? (champion.expectedValue >= 0 ? '+' : '') + (champion.expectedValue * 100).toFixed(1) + '%' : '—'}</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 text-[10px] font-mono">
                <div className="bg-[#0B0F17] rounded-lg p-2"><div className="text-[#64748B]">Model</div><div className="text-[#F8FAFC] font-bold">{champion.modelProbability !== null ? (champion.modelProbability * 100).toFixed(1) + '%' : '—'}</div></div>
                <div className="bg-[#0B0F17] rounded-lg p-2"><div className="text-[#64748B]">Fair odds</div><div className="text-[#F8FAFC] font-bold">{champion.fairOdds?.toFixed(2) ?? '—'}</div></div>
                <div className="bg-[#0B0F17] rounded-lg p-2"><div className="text-[#64748B]">Edge</div><div className="text-[#10B981] font-bold">{champion.edge !== null ? '+' + (champion.edge * 100).toFixed(1) + 'pp' : '—'}</div></div>
                <div className="bg-[#0B0F17] rounded-lg p-2"><div className="text-[#64748B]">Gate</div><div className="text-[#10B981] font-bold">PASSED</div></div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-[#334155] bg-[#0B0F17] p-6 text-center font-mono">
              <div className="text-xl font-black text-[#F8FAFC]">NO BET</div>
              <div className="text-xs text-[#94A3B8] mt-2">Champion found no live 1xBet market that clears its confidence, freshness and value gates.</div>
              <div className="text-[10px] text-[#64748B] mt-3">Reason: {champion?.reason || 'DECISION_UNAVAILABLE'}</div>
            </div>
          )}
        </div>
      </TerminalCard>
      <div className="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-6">
        <TerminalCard
          title="Forecast — Available Before Lineups"
          subtitle={detail?.forecastSource || 'Provider forecast unavailable'}
          badge={
            <span className="px-2 py-0.5 rounded border border-[#334155] bg-[#1E293B] text-[10px] font-mono text-[#F8FAFC]">
              {lineupConfirmed ? 'LINEUP-REFINED VIEW' : 'PRE-LINEUP FORECAST'}
            </span>
          }
          padding="none"
        >
          <div className="p-5 space-y-5">
            {forecast ? (
              <>
                <div className="grid grid-cols-3 gap-3 text-center font-mono">
                  {[
                    [home.name, homeProb],
                    ['Draw', drawProb],
                    [away.name, awayProb],
                  ].map(([label, value]) => (
                    <div key={String(label)} className="rounded-lg border border-[#1E293B] bg-[#0B0F17] p-4">
                      <div className="text-[10px] text-[#64748B] truncate">{String(label)}</div>
                      <div className="text-xl font-bold text-[#F8FAFC] mt-1">{pct(Number(value))}</div>
                    </div>
                  ))}
                </div>

                <div className="rounded-lg border border-[#1E293B] bg-[#0B0F17] p-4 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[#64748B]">Forecast winner</span>
                    <span className="font-semibold text-[#D4AF37]">{forecast.winnerName || 'Unspecified'}</span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-[#64748B]">Estimated score</span>
                    <span className="text-[#F8FAFC]">
                      {forecast.goalsHome ?? '—'} – {forecast.goalsAway ?? '—'}
                    </span>
                  </div>
                  <div className="mt-3 pt-3 border-t border-[#1E293B] text-[10px] text-[#64748B]">
                    This is a provider forecast until the internal statistically validated model is served from the model registry.
                    Official lineups refine the forecast; they do not gate forecast availability.
                  </div>
                </div>
              </>
            ) : (
              <div className="p-8 text-center font-mono text-xs text-[#64748B]">
                No provider forecast returned for this fixture.
              </div>
            )}
          </div>
        </TerminalCard>

        <OddsPanel market={marketData} />
      </div>

      <TerminalCard
        title="1xBet Market Matrix"
        subtitle="Real upstream prices are shown when supplied; forecast-vs-market arithmetic is informational until the internal model registry is active."
        padding="none"
      >
        <MarketTable rows={markets} />
      </TerminalCard>

      <TerminalCard
        title="Current Match Statistics"
        subtitle={live ? 'Live statistics from the fixture feed' : isFinished ? 'Final match statistics from the fixture feed' : 'Available match statistics from the provider'}
        padding="none"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0B0F17] text-[10px] uppercase tracking-wider text-[#64748B] border-b border-[#1E293B]">
              <tr>
                <th className="py-3 px-4">Metric</th>
                <th className="py-3 px-4 text-right">{home.name}</th>
                <th className="py-3 px-4 text-right">{away.name}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E293B]">
              {matchStats.map((row) => (
                <tr key={row.label}>
                  <td className="py-2.5 px-4 text-[#94A3B8]">{row.label}</td>
                  <td className="py-2.5 px-4 text-right text-[#F8FAFC]">{statLabel(row.home)}</td>
                  <td className="py-2.5 px-4 text-right text-[#F8FAFC]">{statLabel(row.away)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </TerminalCard>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <TacticalPitchGrid
          homeTeam={homeLineup}
          awayTeam={awayLineup}
          lineupConfirmed={lineupConfirmed}
          lineupExpectedAt={new Date(new Date(fixture.kickoff).getTime() - 60 * 60 * 1000).toISOString()}
        />

        <TerminalCard
          title="Match Events"
          subtitle="Provider event feed for the selected fixture"
          padding="none"
        >
          <div className="divide-y divide-[#1E293B]">
            {fixture.events?.length ? (
              fixture.events.map((event: any, index: number) => (
                <div key={`event-${index}`} className="p-3.5 flex items-center justify-between gap-4 text-xs font-mono">
                  <div className="text-[#D4AF37] w-12">{event.time?.elapsed ? `${event.time.elapsed}'` : '—'}</div>
                  <div className="flex-1">
                    <div className="text-[#F8FAFC]">{event.detail || event.type || 'Match event'}</div>
                    <div className="text-[10px] text-[#64748B] mt-0.5">
                      {event.team?.name || 'Team'}{event.player?.name ? ` • ${event.player.name}` : ''}
                    </div>
                  </div>
                  <div className="text-[#94A3B8]">{event.comments || ''}</div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-xs font-mono text-[#64748B]">No events returned.</div>
            )}
          </div>
        </TerminalCard>
      </div>

      <TerminalCard
        title="Head-to-Head History"
        subtitle={`Latest provider H2H records for ${home.name} vs ${away.name}`}
        padding="none"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0B0F17] text-[10px] uppercase tracking-wider text-[#64748B] border-b border-[#1E293B]">
              <tr>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Home</th>
                <th className="py-3 px-4">Score</th>
                <th className="py-3 px-4">Away</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E293B]">
              {detail?.history?.length ? (
                detail.history.map((match) => (
                  <tr key={match.id}>
                    <td className="py-2.5 px-4 text-[#64748B]">{new Date(match.date).toLocaleDateString('en-IN')}</td>
                    <td className="py-2.5 px-4 text-[#F8FAFC]">{match.homeTeam}</td>
                    <td className="py-2.5 px-4 text-[#D4AF37] font-bold">
                      {match.homeScore ?? '—'} – {match.awayScore ?? '—'}
                    </td>
                    <td className="py-2.5 px-4 text-[#F8FAFC]">{match.awayTeam}</td>
                    <td className="py-2.5 px-4 text-[#64748B]">{match.status}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-[#64748B]">No H2H history returned.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </TerminalCard>

      <div className="flex items-center justify-between text-[10px] font-mono text-[#64748B]">
        <Link href="/" className="hover:text-[#F8FAFC]">← Back to Matchday Command Center</Link>
        <span>Fixture {fixture.id} • Synchronized {new Date(detail?.generatedAt || Date.now()).toLocaleTimeString('en-IN')}</span>
      </div>
    </div>
  )
}
