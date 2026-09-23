'use client'

import React, { useState, useEffect } from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import TerminalCard from '../ui/terminal/TerminalCard'

export interface ProbabilityPoint {
  minute: number
  homeProb: number // 0 to 1
  drawProb: number // 0 to 1
  awayProb: number // 0 to 1
  event?: string // e.g. "Goal (Home 24')", "Yellow Card 41'"
}

export interface ProbabilityTimelineProps {
  data: ProbabilityPoint[]
  homeTeamName: string
  awayTeamName: string
  currentMinute?: number
  className?: string
}

export default function ProbabilityTimeline({
  data,
  homeTeamName,
  awayTeamName,
  currentMinute,
  className = '',
}: ProbabilityTimelineProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const chartData = data.map((d) => ({
    minute: d.minute,
    home: Math.round(d.homeProb * 1000) / 10,
    draw: Math.round(d.drawProb * 1000) / 10,
    away: Math.round(d.awayProb * 1000) / 10,
    event: d.event,
  }))

  const lastPoint = chartData[chartData.length - 1] || {
    home: 45,
    draw: 28,
    away: 27,
  }

  return (
    <TerminalCard
      title="In-Play Win Probability Drift (0' – 90')"
      subtitle={`Continuous Bayesian hazard tracking conditioned on scoreline, red cards, and elapsed match time`}
      badge={
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
          In-Play Model
        </span>
      }
      className={className}
      padding="none"
    >
      <div className="p-4 sm:p-5 space-y-4">
        {/* Current Probability summary pill strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono pb-2 border-b border-[#1E293B]">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#10B981]" />
              <span className="text-[#94A3B8]">{homeTeamName}:</span>
              <span className="font-bold text-[#F8FAFC]">{lastPoint.home}%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#D4AF37]" />
              <span className="text-[#94A3B8]">Draw:</span>
              <span className="font-bold text-[#F8FAFC]">{lastPoint.draw}%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#3B82F6]" />
              <span className="text-[#94A3B8]">{awayTeamName}:</span>
              <span className="font-bold text-[#F8FAFC]">{lastPoint.away}%</span>
            </div>
          </div>

          {currentMinute !== undefined && (
            <div className="text-[11px] text-[#64748B]">
              Current Time: <span className="text-[#F8FAFC] font-semibold">{currentMinute}&apos;</span>
            </div>
          )}
        </div>

        {/* Chart Container */}
        <div className="h-64 sm:h-72 w-full">
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="homeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="drawGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#D4AF37" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#D4AF37" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="awayGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis
                  dataKey="minute"
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(val) => `${val}'`}
                />
                <YAxis
                  stroke="#64748B"
                  fontSize={11}
                  domain={[0, 100]}
                  tickLine={false}
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const p = payload[0].payload
                      return (
                        <div className="bg-[#0B0F17] border border-[#1E293B] p-3 rounded-lg text-xs font-mono shadow-xl space-y-1.5 min-w-[150px]">
                          <div className="text-[11px] font-semibold text-[#F8FAFC] border-b border-[#1E293B] pb-1 flex justify-between">
                            <span>Minute {p.minute}&apos;</span>
                            {p.event && <span className="text-[#D4AF37]">{p.event}</span>}
                          </div>
                          <div className="flex justify-between text-[#10B981]">
                            <span>{homeTeamName}:</span>
                            <span className="font-bold">{p.home}%</span>
                          </div>
                          <div className="flex justify-between text-[#D4AF37]">
                            <span>Draw:</span>
                            <span className="font-bold">{p.draw}%</span>
                          </div>
                          <div className="flex justify-between text-[#3B82F6]">
                            <span>{awayTeamName}:</span>
                            <span className="font-bold">{p.away}%</span>
                          </div>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="home"
                  stackId="1"
                  stroke="#10B981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#homeGrad)"
                  name={homeTeamName}
                />
                <Area
                  type="monotone"
                  dataKey="draw"
                  stackId="1"
                  stroke="#D4AF37"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#drawGrad)"
                  name="Draw"
                />
                <Area
                  type="monotone"
                  dataKey="away"
                  stackId="1"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#awayGrad)"
                  name={awayTeamName}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-xs font-mono text-[#64748B]">
              Loading probability stream...
            </div>
          )}
        </div>

        {/* Legend footer */}
        <div className="text-[11px] font-mono text-[#64748B] flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#1E293B]">
          <span>Hazard Engine: Bivariate Poisson Process conditioned on game state</span>
          <span>Sample Rate: 1-minute time slices</span>
        </div>
      </div>
    </TerminalCard>
  )
}
