'use client'

import React, { useState } from 'react'

export interface PitchPlayer {
  id: number | string
  name: string
  number: number
  position: 'G' | 'D' | 'M' | 'F' | string
  rating?: number
  isCaptain?: boolean
}

export interface TeamLineupData {
  name: string
  logo?: string
  formation?: string // e.g. "4-3-3", "4-2-3-1"
  starters: PitchPlayer[]
  substitutes?: PitchPlayer[]
  coach?: string
}

export interface TacticalPitchGridProps {
  homeTeam: TeamLineupData
  awayTeam: TeamLineupData
  lineupConfirmed: boolean
  lineupExpectedAt?: string
  className?: string
}

export default function TacticalPitchGrid({
  homeTeam,
  awayTeam,
  lineupConfirmed,
  lineupExpectedAt,
  className = '',
}: TacticalPitchGridProps) {
  const [activeTab, setActiveTab] = useState<'pitch' | 'benches'>('pitch')

  // Helper to parse formation string into line counts e.g. "4-3-3" -> [4, 3, 3]
  const parseFormation = (formStr?: string): number[] => {
    if (!formStr) return [4, 4, 2]
    const parts = formStr.split('-').map((n) => parseInt(n.trim(), 10)).filter((n) => !isNaN(n))
    return parts.length >= 2 ? parts : [4, 4, 2]
  }

  // Segment 10 outfield players into rows according to formation
  const layoutTeamOnRows = (players: PitchPlayer[], formation: number[], isHome: boolean) => {
    // 1 goalkeeper + formation lines
    const gk = players.find((p) => p.position === 'G') || players[0]
    const outfield = players.filter((p) => p !== gk)

    const rows: PitchPlayer[][] = []
    let cursor = 0
    for (const count of formation) {
      rows.push(outfield.slice(cursor, cursor + count))
      cursor += count
    }

    // Home is bottom half (GK at bottom, forwards near center)
    // Away is top half (GK at top, forwards near center)
    return {
      gk,
      rows: isHome ? rows : [...rows].reverse(),
    }
  }

  const homeFormation = parseFormation(homeTeam.formation)
  const awayFormation = parseFormation(awayTeam.formation)

  const homeLayout = homeTeam.starters.length >= 11
    ? layoutTeamOnRows(homeTeam.starters, homeFormation, true)
    : null

  const awayLayout = awayTeam.starters.length >= 11
    ? layoutTeamOnRows(awayTeam.starters, awayFormation, false)
    : null

  return (
    <div className={`bg-[#0F172A] border border-[#1E293B] rounded-xl overflow-hidden ${className}`}>
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[#0B0F17] border-b border-[#1E293B]">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-[#F8FAFC] tracking-tight">
            Tactical Pitch Lineup
          </span>
          <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
              lineupConfirmed
                ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
                : 'bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                lineupConfirmed ? 'bg-[#10B981]' : 'bg-[#F59E0B]'
              }`}
            />
            {lineupConfirmed ? 'Official Starting 11 Verified' : 'Awaiting Official Team Sheets'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg bg-[#0F172A] p-0.5 border border-[#1E293B] text-[11px] font-mono">
            <button
              onClick={() => setActiveTab('pitch')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                activeTab === 'pitch'
                  ? 'bg-[#1E293B] text-[#F8FAFC] font-semibold'
                  : 'text-[#94A3B8] hover:text-[#F8FAFC]'
              }`}
            >
              2D Pitch
            </button>
            <button
              onClick={() => setActiveTab('benches')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                activeTab === 'benches'
                  ? 'bg-[#1E293B] text-[#F8FAFC] font-semibold'
                  : 'text-[#94A3B8] hover:text-[#F8FAFC]'
              }`}
            >
              Roster & Subs
            </button>
          </div>
        </div>
      </div>

      {/* Main pitch or benches view */}
      {activeTab === 'pitch' ? (
        <div className="p-4 sm:p-6 flex flex-col items-center">
          {/* Teams / Formations info strip */}
          <div className="w-full max-w-xl flex items-center justify-between mb-3 text-xs font-mono text-[#94A3B8]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]" />
              <span className="text-[#F8FAFC] font-medium">{awayTeam.name}</span>
              <span className="text-[10px] text-[#64748B]">
                ({awayTeam.formation || '4-3-3'})
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[#64748B]">
                ({homeTeam.formation || '4-2-3-1'})
              </span>
              <span className="text-[#F8FAFC] font-medium">{homeTeam.name}</span>
              <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
            </div>
          </div>

          {/* 2D Football Pitch Canvas */}
          <div className="relative w-full max-w-xl aspect-[3/4] bg-[#0A1A12] border-2 border-[#1E3A29] rounded-xl overflow-hidden shadow-inner flex flex-col justify-between p-3 select-none">
            {/* Pitch Markings SVG overlay */}
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none opacity-30 stroke-[#4ADE80]"
              fill="none"
              strokeWidth="1.5"
              viewBox="0 0 300 400"
            >
              {/* Outer boundary */}
              <rect x="8" y="8" width="284" height="384" rx="4" />
              {/* Halfway line */}
              <line x1="8" y1="200" x2="292" y2="200" />
              {/* Center circle */}
              <circle cx="150" cy="200" r="35" />
              <circle cx="150" cy="200" r="2" fill="#4ADE80" />
              {/* Top Penalty Area (Away) */}
              <rect x="75" y="8" width="150" height="60" />
              <rect x="110" y="8" width="80" height="22" />
              <path d="M 125 68 A 30 30 0 0 0 175 68" />
              {/* Bottom Penalty Area (Home) */}
              <rect x="75" y="332" width="150" height="60" />
              <rect x="110" y="370" width="80" height="22" />
              <path d="M 125 332 A 30 30 0 0 1 175 332" />
            </svg>

            {!lineupConfirmed ? (
              /* Unconfirmed Lineup Overlay */
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-6 text-center bg-[#090C10]/80 backdrop-blur-[2px]">
                <div className="w-12 h-12 rounded-xl bg-[#0F172A] border border-[#1E293B] flex items-center justify-center text-[#F59E0B] mb-3 shadow-md">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1.75"
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <h4 className="text-sm font-semibold text-[#F8FAFC] tracking-tight">
                  Lineups Not Yet Announced
                </h4>
                <p className="text-xs text-[#94A3B8] max-w-md mt-1 leading-relaxed">
                  Official starting XIs are verified ~60 minutes before kickoff directly from the
                  competition team sheet.
                </p>
                {lineupExpectedAt && (
                  <div className="mt-3 px-3 py-1 rounded-md bg-[#0F172A] border border-[#1E293B] text-[11px] font-mono text-[#F59E0B]">
                    Expected: {lineupExpectedAt}
                  </div>
                )}
                <div className="mt-4 text-[10px] font-mono text-[#64748B]">
                  Lineup Gate Policy: No synthetic lineups rendered.
                </div>
              </div>
            ) : (
              /* Confirmed 22 Players Rendered */
              <div className="relative z-10 w-full h-full flex flex-col justify-between py-1">
                {/* Away Team (Top Half, descending) */}
                <div className="flex-1 flex flex-col justify-around pb-2">
                  {/* Away GK */}
                  {awayLayout && (
                    <div className="flex justify-center">
                      <PlayerPitchNode player={awayLayout.gk} teamColor="blue" isGk />
                    </div>
                  )}
                  {/* Away Outfield Rows */}
                  {awayLayout &&
                    awayLayout.rows.map((row, idx) => (
                      <div key={`away-row-${idx}`} className="flex justify-around px-2">
                        {row.map((player) => (
                          <PlayerPitchNode
                            key={player.id}
                            player={player}
                            teamColor="blue"
                          />
                        ))}
                      </div>
                    ))}
                </div>

                {/* Home Team (Bottom Half, ascending) */}
                <div className="flex-1 flex flex-col justify-around pt-2">
                  {/* Home Outfield Rows */}
                  {homeLayout &&
                    homeLayout.rows.map((row, idx) => (
                      <div key={`home-row-${idx}`} className="flex justify-around px-2">
                        {row.map((player) => (
                          <PlayerPitchNode
                            key={player.id}
                            player={player}
                            teamColor="emerald"
                          />
                        ))}
                      </div>
                    ))}
                  {/* Home GK */}
                  {homeLayout && (
                    <div className="flex justify-center">
                      <PlayerPitchNode player={homeLayout.gk} teamColor="emerald" isGk />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Roster & Substitutes Tab */
        <div className="p-4 sm:p-5 grid grid-cols-1 md:grid-cols-2 gap-5 text-xs font-mono">
          {/* Home Team Bench */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
              <span className="font-semibold text-[#F8FAFC]">{homeTeam.name}</span>
              <span className="text-[10px] text-[#64748B]">
                {homeTeam.starters.length} Starters • {homeTeam.substitutes?.length || 0} Subs
              </span>
            </div>
            <div className="space-y-1">
              <div className="text-[10px] uppercase tracking-wider text-[#64748B] font-bold">
                Starting XI
              </div>
              {homeTeam.starters.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-1 px-2 rounded hover:bg-[#1E293B]/40 transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-5 text-right font-bold text-[#10B981]">{p.number}</span>
                    <span className="text-[#F8FAFC] truncate">{p.name}</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#0B0F17] text-[#94A3B8] border border-[#1E293B]">
                    {p.position}
                  </span>
                </div>
              ))}
            </div>

            {homeTeam.substitutes && homeTeam.substitutes.length > 0 && (
              <div className="space-y-1 pt-2 border-t border-[#1E293B]">
                <div className="text-[10px] uppercase tracking-wider text-[#64748B] font-bold">
                  Bench / Reserves
                </div>
                {homeTeam.substitutes.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between py-1 px-2 rounded hover:bg-[#1E293B]/40 text-[#94A3B8]"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-5 text-right text-[#64748B]">{p.number}</span>
                      <span className="truncate">{p.name}</span>
                    </div>
                    <span className="text-[10px]">{p.position}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Away Team Bench */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
              <span className="font-semibold text-[#F8FAFC]">{awayTeam.name}</span>
              <span className="text-[10px] text-[#64748B]">
                {awayTeam.starters.length} Starters • {awayTeam.substitutes?.length || 0} Subs
              </span>
            </div>
            <div className="space-y-1">
              <div className="text-[10px] uppercase tracking-wider text-[#64748B] font-bold">
                Starting XI
              </div>
              {awayTeam.starters.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-1 px-2 rounded hover:bg-[#1E293B]/40 transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-5 text-right font-bold text-[#3B82F6]">{p.number}</span>
                    <span className="text-[#F8FAFC] truncate">{p.name}</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#0B0F17] text-[#94A3B8] border border-[#1E293B]">
                    {p.position}
                  </span>
                </div>
              ))}
            </div>

            {awayTeam.substitutes && awayTeam.substitutes.length > 0 && (
              <div className="space-y-1 pt-2 border-t border-[#1E293B]">
                <div className="text-[10px] uppercase tracking-wider text-[#64748B] font-bold">
                  Bench / Reserves
                </div>
                {awayTeam.substitutes.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between py-1 px-2 rounded hover:bg-[#1E293B]/40 text-[#94A3B8]"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-5 text-right text-[#64748B]">{p.number}</span>
                      <span className="truncate">{p.name}</span>
                    </div>
                    <span className="text-[10px]">{p.position}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function PlayerPitchNode({
  player,
  teamColor,
  isGk,
}: {
  player: PitchPlayer
  teamColor: 'emerald' | 'blue'
  isGk?: boolean
}) {
  const badgeClasses = isGk
    ? 'bg-amber-600 border-amber-300 text-amber-50'
    : teamColor === 'emerald'
    ? 'bg-[#10B981] border-[#34D399] text-black font-extrabold'
    : 'bg-[#2563EB] border-[#60A5FA] text-white font-extrabold'

  return (
    <div className="flex flex-col items-center group cursor-pointer">
      <div
        className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-[11px] font-mono border shadow-md group-hover:scale-110 transition-transform ${badgeClasses}`}
        title={`${player.name} (#${player.number}) - ${player.position}`}
      >
        {player.number}
      </div>
      <div className="mt-1 px-1.5 py-0.5 rounded bg-[#090C10]/90 border border-[#1E293B] text-[9px] sm:text-[10px] font-mono text-[#F8FAFC] truncate max-w-[70px] sm:max-w-[80px] text-center shadow">
        {player.name}
      </div>
    </div>
  )
}
