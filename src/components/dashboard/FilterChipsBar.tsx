'use client'

import React from 'react'

interface FilterChipsBarProps {
  selectedLeague: string
  onSelectLeague: (league: string) => void
  filterType: 'all' | 'lineups_confirmed' | 'high_ev'
  onSelectFilterType: (filter: 'all' | 'lineups_confirmed' | 'high_ev') => void
  totalCount: number
}

const LEAGUES = [
  { id: 'all', name: 'All Competitions' },
  { id: 'premier_league', name: 'Premier League' },
  { id: 'la_liga', name: 'La Liga' },
  { id: 'serie_a', name: 'Serie A' },
  { id: 'bundesliga', name: 'Bundesliga' },
  { id: 'ligue_1', name: 'Ligue 1' },
  { id: 'eredivisie', name: 'Eredivisie' },
  { id: 'champions_league', name: 'UEFA Champions League' }
]

export default function FilterChipsBar({
  selectedLeague,
  onSelectLeague,
  filterType,
  onSelectFilterType,
  totalCount
}: FilterChipsBarProps) {
  return (
    <div className="space-y-3">
      {/* Top Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Status Toggles (Mixpanel segmented control) */}
        <div className="inline-flex p-1 bg-[#0e131b] border border-[#1e2638] rounded-xl text-xs font-mono">
          <button
            onClick={() => onSelectFilterType('all')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterType === 'all'
                ? 'bg-[#182030] text-[#f0f4fc] font-semibold border border-[#2b374e] shadow-sm'
                : 'text-[#8a99ad] hover:text-[#f0f4fc]'
            }`}
          >
            All Matches ({totalCount})
          </button>
          <button
            onClick={() => onSelectFilterType('lineups_confirmed')}
            className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              filterType === 'lineups_confirmed'
                ? 'bg-[#182030] text-[#d4af37] font-semibold border border-[#2b374e] shadow-sm'
                : 'text-[#8a99ad] hover:text-[#d4af37]'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#d4af37]"></span>
            <span>Lineups Confirmed</span>
          </button>
          <button
            onClick={() => onSelectFilterType('high_ev')}
            className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              filterType === 'high_ev'
                ? 'bg-[#182030] text-[#10b981] font-semibold border border-[#2b374e] shadow-sm'
                : 'text-[#8a99ad] hover:text-[#10b981]'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
            <span>High EV (&gt;3%)</span>
          </button>
        </div>

        {/* Informational Pill */}
        <div className="text-[11px] font-mono text-[#56657a] flex items-center gap-2">
          <span>Sort: Kickoff (Ascending IST)</span>
        </div>
      </div>

      {/* Horizontal League Scroll Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {LEAGUES.map((league) => {
          const isSelected = selectedLeague === league.id
          return (
            <button
              key={league.id}
              onClick={() => onSelectLeague(league.id)}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors border ${
                isSelected
                  ? 'bg-[#131924] text-[#f0f4fc] border-[#d4af37]/60 shadow-sm font-semibold'
                  : 'bg-[#0e131b] text-[#8a99ad] border-[#1e2638] hover:text-[#f0f4fc] hover:border-[#2b374e]'
              }`}
            >
              {league.name}
            </button>
          )
        })}
      </div>
    </div>
  )
}
