'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useChartTooltip } from '@/hooks/use-chart-tooltip'
import { ChartTooltipPortal } from '@/components/ui/chart-tooltip-portal'
import { ScoringProfile as ScoringProfileType } from '@/lib/types'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { ParallaxNumber } from '@/components/ui/parallax-number'
import { useScrollPin } from '@/hooks/use-scroll-pin'

interface ScoringProfileProps {
  profile: ScoringProfileType
  leagueAvg: Record<string, number>
}

export function ScoringProfile({ profile, leagueAvg }: ScoringProfileProps) {
  const [radarScale, setRadarScale] = useState(0)
  const [breakdownReveal, setBreakdownReveal] = useState(0)
  const [teamColor, setTeamColor] = useState('oklch(0.80 0.18 85)')
  const colorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!colorRef.current) return
    const raw = getComputedStyle(colorRef.current).getPropertyValue('--team-primary').trim()
    if (raw) setTeamColor(raw)
  }, [])

  const onProgress = useCallback((p: number) => {
    setRadarScale(Math.min(p / 0.5, 1))
    setBreakdownReveal(Math.max(0, Math.min((p - 0.4) / 0.3, 1)))
  }, [])

  const { ref: pinRef } = useScrollPin({
    endOffset: '+=100%',
    onProgress,
  })
  const { pos: tooltipPos, onMouseMove: onChartMouseMove } = useChartTooltip()
  const categories = ['PTS', 'REB', 'AST', 'STL', 'BLK'] // Exclude TO for radar
  
  const radarData = categories.map(cat => {
    const youRaw = (profile[cat]?.pct ?? 0) * 100
    const leagueRaw = leagueAvg[cat] * 100
    const diff = youRaw - leagueRaw
    const scaledYou = 50 + diff * 8
    const finalYou = Math.max(5, Math.min(95, scaledYou))
    return {
      category: cat,
      you: 50 + (finalYou - 50) * radarScale,
      league: 50,
      youRaw,
      leagueRaw,
      fullName: getFullName(cat),
    }
  })

  function getFullName(cat: string): string {
    switch (cat) {
      case 'PTS': return 'Points'
      case 'REB': return 'Rebounds'
      case 'AST': return 'Assists'
      case 'STL': return 'Steals'
      case 'BLK': return 'Blocks'
      case 'TO': return 'Turnovers'
      default: return cat
    }
  }

  // Calculate differences
  const comparisons = Object.entries(profile).map(([key, value]) => {
    const yourPct = value.pct
    const avgPct = leagueAvg[key] || 0
    const diff = yourPct - avgPct
    const diffPct = avgPct > 0 ? ((yourPct - avgPct) / avgPct) * 100 : 0
    
    return {
      category: key,
      fullName: getFullName(key),
      yourPct: yourPct * 100,
      avgPct: avgPct * 100,
      diff: diff * 100,
      diffPct,
      total: value.total,
    }
  })

  const aboveAvg = comparisons.filter(c => c.diff > 0.5 && c.category !== 'TO')
  const belowAvg = comparisons.filter(c => c.diff < -0.5 && c.category !== 'TO')

  return (
    <section ref={(el) => { (pinRef as React.MutableRefObject<HTMLDivElement | null>).current = el; (colorRef as React.MutableRefObject<HTMLDivElement | null>).current = el; }} className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      {/* Section Header */}
      <div className="mb-16">
        <ParallaxNumber gradient className="font-mono text-6xl md:text-8xl font-bold text-muted-foreground/10">
          05
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Scoring Profile
        </h2>
        <p className="font-mono text-base text-muted-foreground mt-2">
          Where your fantasy points came from, vs league average.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-12" onMouseMove={onChartMouseMove}>
        {/* Radar Chart */}
        <div className="h-[400px] lg:h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid 
                stroke="oklch(0.25 0 0)" 
                strokeDasharray="3 3"
              />
              <PolarAngleAxis 
                dataKey="category" 
                tick={{ 
                  fill: 'oklch(0.98 0 0)', 
                  fontSize: 12, 
                  fontFamily: 'var(--font-barlow-condensed)',
                  fontWeight: 600,
                }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload || !payload[0]) return null
                  const data = payload[0].payload
                  return (
                    <ChartTooltipPortal active pos={tooltipPos}>
                      <p className="font-mono text-sm text-foreground font-bold mb-2">{data.fullName}</p>
                      <div className="space-y-1">
                        <p className="font-mono text-xs">
                          <span className="text-gold">You:</span>{' '}
                          <span className="text-foreground">{data.youRaw.toFixed(1)}%</span>
                        </p>
                        <p className="font-mono text-xs">
                          <span className="text-muted-foreground">League:</span>{' '}
                          <span className="text-foreground">{data.leagueRaw.toFixed(1)}%</span>
                        </p>
                        <p className={`font-mono text-xs font-bold ${data.youRaw > data.leagueRaw ? 'text-win' : 'text-loss'}`}>
                          {data.youRaw > data.leagueRaw ? '+' : ''}{(data.youRaw - data.leagueRaw).toFixed(1)}% vs avg
                        </p>
                      </div>
                    </ChartTooltipPortal>
                  )
                }}
              />
              <Radar
                name="League Avg"
                dataKey="league"
                stroke="oklch(0.65 0.12 25)"
                fill="oklch(0.55 0.10 25)"
                fillOpacity={0.15}
                strokeWidth={2.5}
                strokeDasharray="6 3"
                dot={{ r: 4, fill: "oklch(0.65 0.12 25)", strokeWidth: 0 }}
              />
              <Radar
                name="You"
                dataKey="you"
                stroke={teamColor}
                fill={teamColor}
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown */}
        <div className="space-y-6" style={{ opacity: breakdownReveal, transform: `translateY(${(1 - breakdownReveal) * 20}px)` }}>
          {/* Legend */}
          <div className="flex items-center gap-6 mb-8">
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-gold" />
              <span className="font-mono text-xs text-muted-foreground">Your Profile</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-px border-t border-dashed border-muted-foreground" />
              <span className="font-mono text-xs text-muted-foreground">League Average (circle)</span>
            </div>
          </div>
          <p className="font-mono text-xs text-muted-foreground/60 -mt-4 mb-4">Differences are amplified for visibility. Hover for exact values.</p>

          {/* Above Average */}
          {aboveAvg.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-win" />
                <span className="font-mono text-sm text-win uppercase tracking-widest">Above Average</span>
              </div>
              <div className="space-y-3">
                {aboveAvg.map(comp => (
                  <div key={comp.category} className="flex items-center justify-between p-4 border border-win/30 bg-win/5">
                    <div>
                      <p className="font-mono text-lg font-semibold text-foreground">{comp.fullName}</p>
                      <p className="font-mono text-xs text-muted-foreground">{comp.total.toFixed(1)} total pts</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-2xl font-bold text-win">+{comp.diff.toFixed(1)}%</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {comp.yourPct.toFixed(1)}% vs {comp.avgPct.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Below Average */}
          {belowAvg.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingDown className="w-5 h-5 text-loss" />
                <span className="font-mono text-sm text-loss uppercase tracking-widest">Below Average</span>
              </div>
              <div className="space-y-3">
                {belowAvg.map(comp => (
                  <div key={comp.category} className="flex items-center justify-between p-4 border border-loss/30 bg-loss/5">
                    <div>
                      <p className="font-mono text-lg font-semibold text-foreground">{comp.fullName}</p>
                      <p className="font-mono text-xs text-muted-foreground">{comp.total.toFixed(1)} total pts</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-2xl font-bold text-loss">{comp.diff.toFixed(1)}%</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {comp.yourPct.toFixed(1)}% vs {comp.avgPct.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Neutral */}
          {aboveAvg.length === 0 && belowAvg.length === 0 && (
            <div className="flex items-center gap-2 p-4 border border-muted-foreground/30">
              <Minus className="w-5 h-5 text-muted-foreground" />
              <span className="font-mono text-sm text-muted-foreground">Your scoring profile matches the league average</span>
            </div>
          )}
        </div>
      </div>

      {/* Full Breakdown */}
      <div className="mt-16 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {comparisons.map(comp => (
          <div key={comp.category} className="p-4 border border-border">
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">
              {comp.fullName}
            </p>
            <p className="font-mono text-3xl font-bold text-foreground mb-1">
              {comp.yourPct.toFixed(1)}%
            </p>
            <p className={`font-mono text-sm ${
              comp.category === 'TO' 
                ? comp.diff > 0 ? 'text-loss' : 'text-win'
                : comp.diff > 0 ? 'text-win' : comp.diff < 0 ? 'text-loss' : 'text-muted-foreground'
            }`}>
              {comp.diff > 0 ? '+' : ''}{comp.diff.toFixed(1)}%
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
