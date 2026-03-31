'use client'

import { useState } from 'react'
import { WaiverPickup } from '@/lib/types'
import { ChevronDown, ChevronUp, Star } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip } from 'recharts'
import { SectionHeader } from '@/components/wrapped/section-header'
import { AXIS_TICK, COLORS } from '@/lib/chart'
import { useChartTooltip } from '@/hooks/use-chart-tooltip'
import { ChartTooltipPortal } from '@/components/ui/chart-tooltip-portal'

interface WaiverWireProps {
  pickups: WaiverPickup[]
}

export function WaiverWire({ pickups }: WaiverWireProps) {
  const { pos: tooltipPos, onMouseMove: onChartMouseMove, isMobile } = useChartTooltip()
  const [expandedPickup, setExpandedPickup] = useState<number | null>(null)

  if (pickups.length === 0) {
    return (
      <section className="relative min-h-[60vh] px-6 py-24 md:px-12 lg:px-24 flex flex-col justify-center">
        <SectionHeader number="03" title="Waiver Wire" />

        <div className="flex flex-col items-center justify-center py-20">
          <p className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/20">0</p>
          <p className="font-mono text-lg text-muted-foreground mt-4">No waiver pickups</p>
          <p className="font-mono text-sm text-muted-foreground/60 mt-2">
            Who needs FAAB when you can just draft the best players?
          </p>
        </div>
      </section>
    )
  }

  // Sort by points after add
  const sortedPickups = [...pickups].sort((a, b) => b.ptsAfterAdd - a.ptsAfterAdd)
  const mvpPickup = sortedPickups[0]
  const otherPickups = sortedPickups.slice(1)

  const totalWaiverPts = pickups.reduce((acc, p) => acc + p.ptsAfterAdd, 0)

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <SectionHeader
        number="03"
        title="Waiver Wire"
        description={<>The hidden gems you found on the wire. {pickups.length} pickup{pickups.length !== 1 ? "s" : ""} that moved the needle.</>}
      />

      {/* Stats */}
      <div className="grid grid-cols-2 gap-6 mb-12">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Total Pickups</p>
          <p className="font-mono text-5xl font-bold text-foreground">{pickups.length}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Points Added</p>
          <p className="font-mono text-5xl font-bold text-win">+{totalWaiverPts.toFixed(1)}</p>
        </div>
      </div>

      {/* MVP Pickup */}
      <div className="relative mb-8 p-8 border border-gold/50 bg-gold/5 animate-pulse-gold">
        <div className="absolute top-4 right-4">
          <Star className="w-8 h-8 text-gold fill-gold/30" />
        </div>
        
        <p className="font-mono text-xs text-gold uppercase tracking-widest mb-2">
          MVP Pickup
        </p>
        <h3 className="font-mono text-4xl md:text-5xl font-bold text-gold mb-4">
          {mvpPickup.player}
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Week Added</p>
            <p className="font-mono text-2xl font-bold text-foreground">{mvpPickup.weekAdded ?? "—"}</p>
          </div>
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Points After Add</p>
            <p className="font-mono text-2xl font-bold text-win">+{mvpPickup.ptsAfterAdd.toFixed(1)}</p>
          </div>
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Avg/Start</p>
            <p className="font-mono text-2xl font-bold text-foreground">
              {(mvpPickup.ptsAfterAdd / (mvpPickup.weeklyPoints.filter(w => w.pts > 0).length || 1)).toFixed(1)}
            </p>
          </div>
        </div>

        {/* MVP Weekly Chart */}
        <div className="h-[120px] md:h-[150px] mt-6" onMouseMove={onChartMouseMove}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={mvpPickup.weeklyPoints}>
              <XAxis
                dataKey="week"
                axisLine={false}
                tickLine={false}
                tick={AXIS_TICK}
                tickFormatter={(value) => `W${value}`}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={AXIS_TICK}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload || !payload[0]) return null
                  const data = payload[0].payload
                  return (
                    <ChartTooltipPortal active pos={tooltipPos} isMobile={isMobile}>
                      <p className="font-mono text-xs text-muted-foreground">Week {data.week}</p>
                      <p className="font-mono text-lg font-bold text-gold">{data.pts.toFixed(1)}</p>
                    </ChartTooltipPortal>
                  )
                }}
              />
              <Bar dataKey="pts" fill={COLORS.gold} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Other Pickups */}
      {otherPickups.length > 0 && (
        <div className="space-y-4">
          {otherPickups.map((pickup, index) => {
            const isExpanded = expandedPickup === index
            const activeWeeks = pickup.weeklyPoints.filter(w => w.pts > 0).length || 1
            const avgPts = pickup.ptsAfterAdd / activeWeeks

            return (
              <div
                key={index}
                className="border border-border hover:border-muted-foreground/30 transition-colors"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
                        Week {pickup.weekAdded ?? "?"}
                      </p>
                      <h3 className="font-mono text-2xl font-bold text-foreground">
                        {pickup.player}
                      </h3>
                    </div>
                    <div className="text-right flex items-baseline gap-4">
                      <span className="font-mono text-sm text-muted-foreground border border-border px-2 py-0.5">
                        {avgPts.toFixed(1)} avg/wk
                      </span>
                      <span className="font-mono text-2xl font-bold text-win">
                        +{pickup.ptsAfterAdd.toFixed(1)}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => setExpandedPickup(isExpanded ? null : index)}
                    className="flex items-center gap-2 mt-4 font-mono text-xs text-muted-foreground hover:text-foreground uppercase tracking-widest transition-colors"
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    {isExpanded ? 'Hide' : 'Show'} Weekly
                  </button>
                </div>

                {isExpanded && (
                  <div className="px-6 pb-6 border-t border-border">
                    <div className="flex items-center gap-4 mt-4 mb-2">
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-3 bg-win" />
                        <span className="font-mono text-xs text-muted-foreground">Above avg</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-3" style={{ background: COLORS.muted }} />
                        <span className="font-mono text-xs text-muted-foreground">Below avg</span>
                      </div>
                    </div>
                    <div className="h-[100px] md:h-[120px]" onMouseMove={onChartMouseMove}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={pickup.weeklyPoints}>
                          <XAxis
                            dataKey="week"
                            axisLine={false}
                            tickLine={false}
                            tick={AXIS_TICK}
                            tickFormatter={(value) => `W${value}`}
                          />
                          <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={AXIS_TICK}
                          />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (!active || !payload || !payload[0]) return null
                              const data = payload[0].payload
                              return (
                                <ChartTooltipPortal active pos={tooltipPos} isMobile={isMobile}>
                                  <p className="font-mono text-xs text-muted-foreground">Week {data.week}</p>
                                  <p className="font-mono text-lg font-bold text-foreground">{data.pts.toFixed(1)}</p>
                                </ChartTooltipPortal>
                              )
                            }}
                          />
                          <Bar dataKey="pts" radius={[2, 2, 0, 0]}>
                            {pickup.weeklyPoints.map((entry, i) => (
                              <Cell
                                key={`cell-${i}`}
                                fill={entry.pts >= avgPts ? COLORS.win : COLORS.muted}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
