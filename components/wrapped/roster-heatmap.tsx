'use client'

import { useState, useMemo, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { RosterRow, WeeklyResult } from '@/lib/types'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { ParallaxNumber } from '@/components/ui/parallax-number'
import { useScrollBatch } from '@/hooks/use-scroll-batch'

interface RosterHeatmapProps {
  heatmap: RosterRow[]
  weeklyResults: WeeklyResult[]
  nameMap?: Record<string, string>
}

type HoverData = {
  player: string
  slot: string
  week: number
  pts: number
  opponent: string
} | null

export function RosterHeatmap({ heatmap, weeklyResults, nameMap = {} }: RosterHeatmapProps) {
  const [showAll, setShowAll] = useState(false)
  const [hovered, setHovered] = useState<HoverData>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  const { ref: batchRef } = useScrollBatch({ childSelector: '[data-batch-item]', stagger: 0.04 })

  useEffect(() => {
    if (!hovered) return
    const dismiss = () => setHovered(null)
    window.addEventListener('scroll', dismiss, { passive: true, once: true })
    window.addEventListener('touchmove', dismiss, { passive: true, once: true })
    return () => {
      window.removeEventListener('scroll', dismiss)
      window.removeEventListener('touchmove', dismiss)
    }
  }, [hovered])

  const allValues = heatmap.flatMap(row => row.weeks.filter(v => v > 0))
  const maxValue = Math.max(...allValues)

  const sortedHeatmap = useMemo(() => {
    return [...heatmap]
      .map(row => ({
        ...row,
        total: row.weeks.reduce((a, b) => a + b, 0),
        gamesPlayed: row.weeks.filter(v => v > 0).length,
      }))
      .sort((a, b) => b.total - a.total)
  }, [heatmap])

  const displayedRows = showAll ? sortedHeatmap : sortedHeatmap.slice(0, 12)

  const getHeatColor = (value: number): string => {
    if (value === 0) return 'bg-muted/20'
    const intensity = value / maxValue
    if (intensity >= 0.8) return 'bg-gold'
    if (intensity >= 0.6) return 'bg-gold/70'
    if (intensity >= 0.4) return 'bg-win/60'
    if (intensity >= 0.2) return 'bg-win/40'
    return 'bg-win/20'
  }

  const getSlotColor = (slot: string): string => {
    switch (slot) {
      case 'G': return 'text-chart-4'
      case 'F': return 'text-chart-5'
      case 'C': return 'text-gold'
      case 'F-C': case 'F/C': return 'text-chart-3'
      case 'UT': return 'text-muted-foreground'
      case 'BN': return 'text-muted-foreground/50'
      default: return 'text-muted-foreground'
    }
  }

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <div className="mb-16">
        <ParallaxNumber gradient className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/10">
          04
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Roster Heatmap
        </h2>
        <p className="font-mono text-base text-muted-foreground mt-2">
          The whole squad under the microscope, week by week.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-6 mb-8">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-muted/20" />
          <span className="font-mono text-xs text-muted-foreground">Inactive</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-win/20" />
          <span className="font-mono text-xs text-muted-foreground">Low</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-win/60" />
          <span className="font-mono text-xs text-muted-foreground">Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gold" />
          <span className="font-mono text-xs text-muted-foreground">High</span>
        </div>
      </div>

      {hovered && typeof document !== 'undefined' && createPortal(
        <div
          className="fixed z-50 pointer-events-none px-4 py-3 bg-card border border-border shadow-xl"
          style={{ left: tooltipPos.x + 14, top: tooltipPos.y - 14 }}
        >
          <p className="font-mono text-xs font-bold text-foreground">{hovered.player}</p>
          <p className="font-mono text-xs text-muted-foreground">Week {hovered.week} · {nameMap[hovered.opponent] || hovered.opponent}</p>
          <p className={`font-mono text-sm font-bold ${hovered.pts === 0 ? 'text-muted-foreground' : 'text-gold'}`}>
            {hovered.pts === 0 ? 'Inactive' : `${hovered.pts.toFixed(1)} pts`}
          </p>
        </div>,
        document.body
      )}

      <div className="overflow-x-auto relative">

        <div className="min-w-[900px]">
          <div className="flex items-center mb-2">
            <div className="w-32 shrink-0" />
            <div className="w-10 shrink-0" />
            <div className="flex-1 flex">
              {weeklyResults.map((week) => (
                <div key={week.week} className="flex-1 min-w-[28px] text-center">
                  <span className={`font-mono text-xs ${
                    week.result === 'W' ? 'text-win' : 'text-loss'
                  }`}>
                    {week.week}
                  </span>
                </div>
              ))}
            </div>
            <div className="w-16 shrink-0 text-right">
              <span className="font-mono text-xs text-muted-foreground">Total</span>
            </div>
          </div>

          <div ref={batchRef} className="space-y-px">
            {displayedRows.map((row, index) => (
              <div
                key={index}
                data-batch-item
                className="flex items-center group hover:bg-card/50 transition-colors"
              >
                <div className="w-32 shrink-0 pr-2">
                  <span className="font-mono text-xs text-foreground truncate block">
                    {row.player}
                  </span>
                </div>

                <div className="w-10 shrink-0">
                  <span className={`font-mono text-xs font-bold uppercase ${getSlotColor(row.slot)}`}>
                    {row.slot}
                  </span>
                </div>

                <div className="flex-1 flex gap-px">
                  {row.weeks.map((value, weekIndex) => {
                    const week = weekIndex + 1
                    const opponent = weeklyResults.find((w) => w.week === week)?.opponent ?? "—"
                    return (
                      <div
                        key={weekIndex}
                        className={`flex-1 min-w-[28px] h-6 ${getHeatColor(value)} transition-all cursor-pointer hover:opacity-80 ${
                          hovered?.player === row.player && hovered?.week === week
                            ? 'ring-1 ring-gold'
                            : ''
                        }`}
                        onMouseEnter={(e) => {
                          setHovered({ player: row.player, slot: row.slot, week, pts: value, opponent })
                          setTooltipPos({ x: e.clientX, y: e.clientY })
                        }}
                        onMouseMove={(e) => setTooltipPos({ x: e.clientX, y: e.clientY })}
                        onMouseLeave={() => setHovered(null)}
                        onTouchEnd={(e) => {
                          if (hovered?.player === row.player && hovered?.week === week) {
                            setHovered(null)
                          } else {
                            const touch = e.changedTouches[0]
                            setHovered({ player: row.player, slot: row.slot, week, pts: value, opponent })
                            setTooltipPos({ x: touch.clientX, y: touch.clientY })
                          }
                        }}
                      />
                    )
                  })}
                </div>

                <div className="w-16 shrink-0 text-right">
                  <span className="font-mono text-xs font-bold text-foreground">
                    {row.total.toFixed(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {sortedHeatmap.length > 12 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="flex items-center gap-2 mt-8 font-mono text-xs text-muted-foreground hover:text-foreground uppercase tracking-widest transition-colors"
        >
          {showAll ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          {showAll ? 'Show Less' : `Show All (${sortedHeatmap.length} players)`}
        </button>
      )}

      <div className="flex flex-wrap gap-6 mt-12 pt-8 border-t border-border">
        {[
          { slot: 'G', label: 'Guard', color: 'text-chart-4' },
          { slot: 'F', label: 'Forward', color: 'text-chart-5' },
          { slot: 'C', label: 'Center', color: 'text-gold' },
          { slot: 'F/C', label: 'Forward-Center', color: 'text-chart-3' },
          { slot: 'UT', label: 'Utility', color: 'text-muted-foreground' },
          { slot: 'BN', label: 'Bench', color: 'text-muted-foreground/50' },
        ].map(({ slot, label, color }) => (
          <div key={slot} className="flex items-center gap-2">
            <span className={`font-mono text-xs font-bold ${color}`}>{slot}</span>
            <span className="font-mono text-xs text-muted-foreground">{label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
