'use client'

import { OptimalLineup as OptimalLineupType } from '@/lib/types'
import { ComposedChart, Bar, Cell, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine } from 'recharts'
import { ParallaxNumber } from '@/components/ui/parallax-number'
import { useChartTooltip } from '@/hooks/use-chart-tooltip'
import { ChartTooltipPortal } from '@/components/ui/chart-tooltip-portal'

interface OptimalLineupProps {
  data: OptimalLineupType
}

export function OptimalLineup({ data }: OptimalLineupProps) {
  const { pos: tooltipPos, onMouseMove: onChartMouseMove, isMobile } = useChartTooltip()
  const chartData = data.weeklyComparison.map(week => ({
    week: week.week,
    actual: week.actualPts,
    optimal: week.optimalPts,
    diff: week.diff,
    isBigGap: week.diff > 75,
  }))

  const totalDiff = data.totalOptimal - data.totalActual
  const avgDiff = totalDiff / data.weeklyComparison.length
  const worstWeek = data.weeklyComparison.reduce((worst, w) => w.diff > worst.diff ? w : worst)
  const bestWeek = data.weeklyComparison.reduce((best, w) => w.diff < best.diff ? w : best)

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      {/* Section Header */}
      <div className="mb-16">
        <ParallaxNumber gradient className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/10">
          07
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Optimal Lineup
        </h2>
        <p className="font-mono text-base text-muted-foreground mt-2">
          How close did you get to your ceiling each week?
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
        <div className="p-6 border border-gold/50 bg-gold/5">
          <p className="font-mono text-xs text-gold uppercase tracking-widest mb-2">Efficiency</p>
          <p className="font-mono text-5xl md:text-6xl font-bold text-gold">
            {(data.efficiency * 100).toFixed(1)}%
          </p>
        </div>
        
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">Points Left</p>
          <p className="font-mono text-5xl md:text-6xl font-bold text-loss">
            -{totalDiff.toFixed(1)}
          </p>
          <p className="font-mono text-sm text-muted-foreground mt-2">
            {avgDiff.toFixed(1)}/week
          </p>
        </div>

        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">Worst Week</p>
          <p className="font-mono text-4xl md:text-5xl font-bold text-loss">
            -{worstWeek.diff.toFixed(1)}
          </p>
          <p className="font-mono text-sm text-muted-foreground mt-2">
            Week {worstWeek.week}
          </p>
        </div>

        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">Best Week</p>
          <p className="font-mono text-4xl md:text-5xl font-bold text-win">
            {(100 - bestWeek.diff).toFixed(1)}%
          </p>
          <p className="font-mono text-sm text-muted-foreground mt-2">
            Week {bestWeek.week}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[250px] md:h-[400px] mb-8" onMouseMove={onChartMouseMove}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} barGap={0}>
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
              domain={['dataMin - 100', 'dataMax + 50']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload[0]) return null
                const data = payload[0].payload
                return (
                  <ChartTooltipPortal active pos={tooltipPos} isMobile={isMobile}>
                    <p className="font-mono text-xs text-muted-foreground mb-2">Week {data.week}</p>
                    <div className="space-y-1">
                      <p className="font-mono text-sm">
                        <span className="text-foreground">Actual:</span>{' '}
                        <span className="font-bold">{data.actual.toFixed(1)}</span>
                      </p>
                      <p className="font-mono text-sm">
                        <span className="text-gold">Optimal:</span>{' '}
                        <span className="font-bold">{data.optimal.toFixed(1)}</span>
                      </p>
                      <p className={`font-mono text-sm ${data.isBigGap ? 'text-loss font-bold' : 'text-muted-foreground'}`}>
                        Gap: -{data.diff.toFixed(1)}
                      </p>
                    </div>
                  </ChartTooltipPortal>
                )
              }}
            />
            <ReferenceLine y={avgDiff} stroke="oklch(0.55 0.22 25)" strokeDasharray="3 3" />
            <Bar
              dataKey="actual"
              radius={[2, 2, 0, 0]}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.isBigGap ? 'oklch(0.55 0.22 25)' : 'oklch(0.40 0 0)'}
                />
              ))}
            </Bar>
            <Line
              type="monotone"
              dataKey="optimal"
              stroke="oklch(0.80 0.18 85)"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-muted-foreground/40" />
          <span className="font-mono text-xs text-muted-foreground">Actual Points</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-loss" />
          <span className="font-mono text-xs text-muted-foreground">Big Gap (75+ pts)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-px border-t-2 border-dashed border-gold" />
          <span className="font-mono text-xs text-muted-foreground">Optimal Points</span>
        </div>
      </div>
    </section>
  )
}
