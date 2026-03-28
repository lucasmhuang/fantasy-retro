'use client'

import { OptimalLineup as OptimalLineupType } from '@/lib/types'
import { ComposedChart, Bar, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine } from 'recharts'
import { ParallaxNumber } from '@/components/ui/parallax-number'

interface OptimalLineupProps {
  data: OptimalLineupType
}

export function OptimalLineup({ data }: OptimalLineupProps) {
  const chartData = data.weeklyComparison.map(week => ({
    week: week.week,
    actual: week.actualPts,
    optimal: week.optimalPts,
    diff: week.diff,
    isBigGap: week.diff > 50,
  }))

  const totalDiff = data.totalOptimal - data.totalActual
  const avgDiff = totalDiff / data.weeklyComparison.length
  const worstWeek = data.weeklyComparison.reduce((worst, w) => w.diff > worst.diff ? w : worst)
  const bestWeek = data.weeklyComparison.reduce((best, w) => w.diff < best.diff ? w : best)

  const efficiencyGrade = data.efficiency >= 0.98 ? 'A+' :
    data.efficiency >= 0.96 ? 'A' :
    data.efficiency >= 0.94 ? 'A-' :
    data.efficiency >= 0.92 ? 'B+' :
    data.efficiency >= 0.90 ? 'B' :
    data.efficiency >= 0.88 ? 'B-' :
    data.efficiency >= 0.85 ? 'C+' :
    data.efficiency >= 0.82 ? 'C' : 'D'

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      {/* Section Header */}
      <div className="mb-16">
        <ParallaxNumber className="font-mono text-6xl md:text-8xl font-bold text-muted-foreground/10">
          07
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Optimal Lineup
        </h2>
        <p className="font-mono text-sm text-muted-foreground mt-2">
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
          <p className="font-mono text-lg font-bold text-gold mt-2">{efficiencyGrade}</p>
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
      <div className="h-[400px] mb-8">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} barGap={0}>
            <XAxis
              dataKey="week"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'oklch(0.60 0 0)', fontSize: 10, fontFamily: 'var(--font-barlow-condensed)' }}
              tickFormatter={(value) => `W${value}`}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'oklch(0.60 0 0)', fontSize: 10, fontFamily: 'var(--font-barlow-condensed)' }}
              domain={['dataMin - 100', 'dataMax + 50']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload[0]) return null
                const data = payload[0].payload
                return (
                  <div className="bg-card border border-border px-4 py-3">
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
                  </div>
                )
              }}
            />
            <ReferenceLine y={avgDiff} stroke="oklch(0.55 0.22 25)" strokeDasharray="3 3" />
            <Bar
              dataKey="actual"
              radius={[2, 2, 0, 0]}
              fill="oklch(0.40 0 0)"
            >
              {chartData.map((entry, index) => (
                <Bar
                  key={index}
                  dataKey="actual"
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
          <span className="font-mono text-xs text-muted-foreground">Big Gap (50+ pts)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-px border-t-2 border-dashed border-gold" />
          <span className="font-mono text-xs text-muted-foreground">Optimal Points</span>
        </div>
      </div>
    </section>
  )
}
