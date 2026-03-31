'use client'

import { BenchMisplay } from '@/lib/types'
import { AlertTriangle, Skull, ArrowRight } from 'lucide-react'
import { SectionHeader } from '@/components/wrapped/section-header'

interface BenchMisplaysProps {
  misplays: BenchMisplay[]
}

export function BenchMisplays({ misplays }: BenchMisplaysProps) {
  if (misplays.length === 0) {
    return (
      <section className="relative min-h-[60vh] px-6 py-24 md:px-12 lg:px-24 flex flex-col justify-center">
        <SectionHeader number="08" title="Bench Misplays" />

        <div className="flex flex-col items-center justify-center py-20">
          <p className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-win">CLEAN</p>
          <p className="font-mono text-lg text-muted-foreground mt-4">No significant bench misplays</p>
          <p className="font-mono text-sm text-muted-foreground/60 mt-2">
            Your lineup decisions were on point all season.
          </p>
        </div>
      </section>
    )
  }

  // Sort by biggest impact, prioritizing result-flippers
  const sortedMisplays = [...misplays].sort((a, b) => {
    if (a.wouldHaveWon !== b.wouldHaveWon) return a.wouldHaveWon ? -1 : 1
    return b.diff - a.diff
  })

  const worstMisplay = sortedMisplays[0]
  const otherMisplays = sortedMisplays.slice(1)
  const resultFlippers = misplays.filter(m => m.wouldHaveWon)
  const totalPointsLost = misplays.reduce((acc, m) => acc + m.diff, 0)

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <SectionHeader
        number="08"
        title="Bench Misplays"
        description="The ones that got away. Points left on the bench when it mattered."
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-12">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Total Misplays</p>
          <p className="font-mono text-5xl font-bold text-foreground">{misplays.length}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Points Lost</p>
          <p className="font-mono text-5xl font-bold text-loss">-{totalPointsLost.toFixed(1)}</p>
        </div>
        {resultFlippers.length > 0 && (
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Result Flippers</p>
            <p className="font-mono text-5xl font-bold text-loss">{resultFlippers.length}</p>
          </div>
        )}
      </div>

      {/* Worst Misplay - Hero Card */}
      <div className="relative mb-8 p-8 border border-loss/50 bg-loss/5">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-6 h-6 text-loss" />
          <p className="font-mono text-xs text-loss uppercase tracking-widest">
            Biggest Misplay &mdash; Week {worstMisplay.week}
          </p>
        </div>

        <div className="flex flex-col md:flex-row items-stretch gap-6">
          {/* Benched Player */}
          <div className="flex-1 p-4 border border-win/30 bg-win/5">
            <p className="font-mono text-xs text-win uppercase tracking-widest mb-2">On Bench</p>
            <p className="font-mono text-2xl font-bold text-foreground">{worstMisplay.benchPlayer}</p>
            <p className="font-mono text-4xl font-bold text-win mt-2">{worstMisplay.benchPts.toFixed(1)}</p>
          </div>

          {/* Arrow */}
          <div className="hidden md:flex items-center justify-center px-4">
            <ArrowRight className="w-6 h-6 text-muted-foreground" />
          </div>

          {/* Started Player */}
          <div className="flex-1 p-4 border border-loss/30 bg-loss/5">
            <p className="font-mono text-xs text-loss uppercase tracking-widest mb-2">Started</p>
            <p className="font-mono text-2xl font-bold text-foreground">{worstMisplay.startPlayer}</p>
            <p className="font-mono text-4xl font-bold text-loss mt-2">{worstMisplay.startPts.toFixed(1)}</p>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <p className="font-mono text-sm text-muted-foreground">
              Difference: <span className="text-loss font-bold">+{worstMisplay.diff.toFixed(1)} pts</span>
            </p>
          </div>
          {worstMisplay.wouldHaveWon && (
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-win text-background font-mono text-xs font-bold uppercase tracking-wider">
                <Skull className="w-3.5 h-3.5" />
                Would Have Won
              </span>
              <span className="font-mono text-sm text-muted-foreground">
                Lost by {worstMisplay.lossMargin?.toFixed(1)} pts
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Other Misplays */}
      {otherMisplays.length > 0 && (
        <div className="space-y-4">
          {otherMisplays.map((misplay, index) => (
            <div
              key={index}
              className={`p-6 border ${
                misplay.wouldHaveWon 
                  ? 'border-loss/50 bg-loss/5' 
                  : 'border-border'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
                    Week {misplay.week}
                  </p>
                  {misplay.wouldHaveWon && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-win text-background font-mono text-xs font-bold uppercase tracking-wider">
                      <Skull className="w-3 h-3" />
                      Would Have Won
                    </span>
                  )}
                </div>
                <p className="font-mono text-2xl font-bold text-loss">
                  +{misplay.diff.toFixed(1)}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <p className="font-mono text-xs text-muted-foreground">Benched</p>
                  <p className="font-mono text-lg text-foreground">{misplay.benchPlayer}</p>
                  <p className="font-mono text-sm text-win">{misplay.benchPts.toFixed(1)}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground shrink-0" />
                <div className="flex-1">
                  <p className="font-mono text-xs text-muted-foreground">Started</p>
                  <p className="font-mono text-lg text-foreground">{misplay.startPlayer}</p>
                  <p className="font-mono text-sm text-loss">{misplay.startPts.toFixed(1)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
