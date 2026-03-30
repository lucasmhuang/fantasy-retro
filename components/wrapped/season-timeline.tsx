'use client'

import { useState, useCallback } from 'react'
import { WeeklyResult } from '@/lib/types'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, ReferenceLine, Tooltip, LineChart, Line } from 'recharts'
import { ParallaxNumber } from '@/components/ui/parallax-number'
import { useScrollPin } from '@/hooks/use-scroll-pin'
import { useChartTooltip } from '@/hooks/use-chart-tooltip'
import { ChartTooltipPortal } from '@/components/ui/chart-tooltip-portal'

interface SeasonTimelineProps {
  weeklyResults: WeeklyResult[]
  nameMap?: Record<string, string>
}

export function SeasonTimeline({ weeklyResults, nameMap = {} }: SeasonTimelineProps) {
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null)
  const [chartReveal, setChartReveal] = useState(0)

  const onProgress = useCallback((p: number) => {
    setChartReveal(Math.min(p / 0.4, 1))
  }, [])

  const { ref: pinRef } = useScrollPin({
    endOffset: '+=80%',
    onProgress,
  })

  const { pos: tooltipPos, onMouseMove: onChartMouseMove } = useChartTooltip()

  const rawData = weeklyResults.map((week) => ({
    week: week.week,
    yourScore: week.score,
    oppScore: week.oppScore,
    result: week.result,
    opponent: week.opponent,
    standing: week.standing,
    event: week.event,
    diff: week.score - week.oppScore,
    isBye: false,
  }))

  const byeStubHeight = weeklyResults.reduce((acc, w) => acc + w.score, 0) / weeklyResults.length * 0.06

  const chartData = rawData.reduce<typeof rawData>((acc, entry, i) => {
    if (i > 0) {
      const prevWeek = rawData[i - 1].week
      for (let w = prevWeek + 1; w < entry.week; w++) {
        acc.push({
          week: w,
          yourScore: byeStubHeight,
          oppScore: 0,
          result: 'BYE' as WeeklyResult['result'],
          opponent: '',
          standing: 0,
          event: undefined as string | undefined,
          diff: 0,
          isBye: true,
        })
      }
    }
    acc.push(entry)
    return acc
  }, [])

  const wins = weeklyResults.filter(w => w.result === 'W').length
  const losses = weeklyResults.filter(w => w.result === 'L').length
  const avgScore = weeklyResults.reduce((acc, w) => acc + w.score, 0) / weeklyResults.length
  const bestWeek = weeklyResults.reduce((best, w) => w.score > best.score ? w : best)
  const worstWeek = weeklyResults.reduce((worst, w) => w.score < worst.score ? w : worst)

  const selectedData = selectedWeek ? chartData.find(d => d.week === selectedWeek) : null

  return (
    <section ref={pinRef} className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      {/* Section Header */}
      <div className="mb-16">
        <ParallaxNumber gradient className="font-mono text-6xl md:text-8xl font-bold text-muted-foreground/10">
          01
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Season Timeline
        </h2>
        <p className="font-mono text-base text-muted-foreground mt-2">
          {weeklyResults.length} weeks of battle. Every win and loss.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Wins</p>
          <p className="font-mono text-4xl font-bold text-win">{wins}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Losses</p>
          <p className="font-mono text-4xl font-bold text-loss">{losses}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Avg Score</p>
          <p className="font-mono text-4xl font-bold text-foreground">{avgScore.toFixed(1)}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Best Week</p>
          <p className="font-mono text-4xl font-bold text-gold">{bestWeek.score.toFixed(1)}</p>
        </div>
      </div>

      {/* Score Chart */}
      <div style={{ opacity: chartReveal, transform: `translateY(${(1 - chartReveal) * 20}px)` }}>
        <div className="h-[300px] md:h-[400px] mb-8" onMouseMove={onChartMouseMove}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} barGap={2}>
              <XAxis
                dataKey="week"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'oklch(0.60 0 0)', fontSize: 12, fontFamily: 'var(--font-barlow-condensed)' }}
                tickFormatter={(value) => `W${value}`}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'oklch(0.60 0 0)', fontSize: 12, fontFamily: 'var(--font-barlow-condensed)' }}
                domain={['dataMin - 50', 'dataMax + 50']}
              />
              <Tooltip
                cursor={false}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload[0]) return null
                  const data = payload[0].payload
                  if (data.isBye) {
                    return (
                      <ChartTooltipPortal active pos={tooltipPos}>
                        <p className="font-mono text-xs text-muted-foreground mb-1">Week {data.week}</p>
                        <p className="font-mono text-lg font-bold text-gold">BYE</p>
                        <p className="font-mono text-xs text-muted-foreground mt-1">First-round bye</p>
                      </ChartTooltipPortal>
                    )
                  }
                  return (
                    <ChartTooltipPortal active pos={tooltipPos}>
                      <p className="font-mono text-xs text-muted-foreground mb-1">Week {data.week}</p>
                      <p className={`font-mono text-lg font-bold ${data.result === 'W' ? 'text-win' : 'text-loss'}`}>
                        {data.result === 'W' ? 'WIN' : 'LOSS'}
                      </p>
                      <p className="font-mono text-sm text-foreground">{data.yourScore.toFixed(1)} - {data.oppScore.toFixed(1)}</p>
                      <p className="font-mono text-xs text-muted-foreground mt-1">vs {nameMap[data.opponent] || data.opponent}</p>
                      {data.event && (
                        <p className="font-mono text-xs text-gold mt-2 border-t border-border pt-2">{data.event}</p>
                      )}
                    </ChartTooltipPortal>
                  )
                }}
              />
              <ReferenceLine y={avgScore} stroke="oklch(0.60 0 0)" strokeDasharray="3 3" />
              <Bar
                dataKey="yourScore"
                radius={[2, 2, 0, 0]}
                cursor="pointer"
                activeBar={{ stroke: 'oklch(0.98 0 0)', strokeWidth: 2, strokeOpacity: 0.6 }}
                onClick={(data) => !data.isBye && setSelectedWeek(data.week)}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.isBye ? 'oklch(0.25 0 0)' : entry.result === 'W' ? 'oklch(0.65 0.20 145)' : 'oklch(0.55 0.22 25)'}
                    fillOpacity={entry.isBye ? 0.4 : selectedWeek === entry.week ? 1 : 0.8}
                    strokeDasharray={entry.isBye ? '4 2' : undefined}
                    stroke={entry.isBye ? 'oklch(0.40 0 0)' : undefined}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Standings Line Chart */}
        <div className="h-[150px] mb-8" onMouseMove={onChartMouseMove}>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-4">Standing Over Time</p>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData.filter(d => d.standing > 0)}>
              <XAxis
                dataKey="week"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'oklch(0.60 0 0)', fontSize: 12, fontFamily: 'var(--font-barlow-condensed)' }}
                tickFormatter={(value) => `W${value}`}
              />
              <YAxis
                reversed
                domain={[1, 12]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'oklch(0.60 0 0)', fontSize: 12, fontFamily: 'var(--font-barlow-condensed)' }}
                ticks={[1, 4, 8, 12]}
              />
              <Tooltip
                cursor={false}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload[0]) return null
                  const data = payload[0].payload
                  return (
                    <ChartTooltipPortal active pos={tooltipPos}>
                      <p className="font-mono text-xs text-muted-foreground">Week {data.week}</p>
                      <p className="font-mono text-lg font-bold text-foreground">#{data.standing}</p>
                    </ChartTooltipPortal>
                  )
                }}
              />
              <Line 
                type="stepAfter"
                dataKey="standing" 
                stroke="oklch(0.80 0.18 85)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: 'oklch(0.80 0.18 85)' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* W/L Chips */}
      <div className="flex flex-wrap gap-2 mt-8">
        {chartData.map((week) => (
          week.isBye ? (
            <div
              key={week.week}
              className="flex items-center justify-center w-10 h-10 font-mono text-xs font-bold border border-dashed border-muted-foreground/30 text-muted-foreground/50"
            >
              BYE
            </div>
          ) : (
            <button
              key={week.week}
              onClick={() => setSelectedWeek(week.week === selectedWeek ? null : week.week)}
              className={`relative group flex items-center justify-center w-10 h-10 font-mono text-xs font-bold transition-all ${
                week.result === 'W'
                  ? 'bg-win/20 text-win hover:bg-win/30'
                  : 'bg-loss/20 text-loss hover:bg-loss/30'
              } ${selectedWeek === week.week ? 'ring-1 ring-gold' : ''} ${week.event ? 'ring-1 ring-gold/50' : ''}`}
            >
              {week.result}
              {week.event && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-gold rounded-full" />
              )}
            </button>
          )
        ))}
        {(() => {
          const last = weeklyResults[weeklyResults.length - 1]
          if (!last) return null
          const muted = "flex items-center justify-center h-10 px-3 font-mono text-xs font-bold uppercase tracking-widest text-muted-foreground/50 border border-dashed border-muted-foreground/20"
          if (last.week >= 21 && last.result === 'W')
            return (
              <div className="flex items-center justify-center h-10 px-3 font-mono text-xs font-bold uppercase tracking-widest text-gold border border-gold/40">
                Champion
              </div>
            )
          if (last.week >= 21) return <div className={muted}>Runner-Up</div>
          if (last.week === 20) return <div className={muted}>Eliminated &mdash; Top 4</div>
          if (last.week === 19) return <div className={muted}>Eliminated &mdash; Top 6</div>
          return <div className={muted}>Season Over</div>
        })()}
      </div>

      {/* Selected Week Detail */}
      {selectedData && (
        <div className="mt-8 p-6 border border-border bg-card/50">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest">Week {selectedData.week}</p>
              <p className={`font-mono text-3xl font-bold ${selectedData.result === 'W' ? 'text-win' : 'text-loss'}`}>
                {selectedData.result === 'W' ? 'VICTORY' : 'DEFEAT'}
              </p>
            </div>
            <div className="text-right">
              <p className="font-mono text-4xl font-bold text-foreground">
                {selectedData.yourScore.toFixed(1)} <span className="text-muted-foreground text-2xl">-</span> {selectedData.oppScore.toFixed(1)}
              </p>
              <p className="font-mono text-sm text-muted-foreground">vs {nameMap[selectedData.opponent] || selectedData.opponent}</p>
            </div>
          </div>
          {selectedData.event && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="font-mono text-sm text-gold">{selectedData.event}</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
