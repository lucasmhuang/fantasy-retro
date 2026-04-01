'use client'

import { AllPlayRecord as AllPlayRecordType } from '@/lib/types'
import { Sparkles, Target, Scale } from 'lucide-react'
import { SectionHeader } from '@/components/wrapped/section-header'

interface AllPlayRecordProps {
  allPlay: AllPlayRecordType
  actualRecord: string
}

export function AllPlayRecord({ allPlay, actualRecord }: AllPlayRecordProps) {
  const [actualWins, actualLosses] = actualRecord.split('-').map(Number)
  const totalActualGames = actualWins + actualLosses
  const actualWinPct = actualWins / totalActualGames

  // Calculate luck factor
  const luckDiff = actualWinPct - allPlay.winPct
  const luckPctDiff = (luckDiff * 100).toFixed(1)
  
  type LuckStatus = 'very_lucky' | 'lucky' | 'fair' | 'unlucky' | 'very_unlucky'
  let luckStatus: LuckStatus
  let luckColor: string
  let luckIcon: React.ReactNode
  let luckLabel: string

  if (luckDiff > 0.06) {
    luckStatus = 'very_lucky'
    luckColor = 'text-win'
    luckIcon = <Sparkles className="w-8 h-8 text-win" />
    luckLabel = 'VERY LUCKY'
  } else if (luckDiff > 0.02) {
    luckStatus = 'lucky'
    luckColor = 'text-win'
    luckIcon = <Sparkles className="w-8 h-8 text-win" />
    luckLabel = 'LUCKY'
  } else if (luckDiff < -0.06) {
    luckStatus = 'very_unlucky'
    luckColor = 'text-loss'
    luckIcon = <Target className="w-8 h-8 text-loss" />
    luckLabel = 'VERY UNLUCKY'
  } else if (luckDiff < -0.02) {
    luckStatus = 'unlucky'
    luckColor = 'text-loss'
    luckIcon = <Target className="w-8 h-8 text-loss" />
    luckLabel = 'UNLUCKY'
  } else {
    luckStatus = 'fair'
    luckColor = 'text-muted-foreground'
    luckIcon = <Scale className="w-8 h-8 text-muted-foreground" />
    luckLabel = 'FAIR'
  }

  const luckMessages: Record<LuckStatus, string> = {
    very_lucky: 'Your wins came gift-wrapped. The schedule carried you harder than your roster did.',
    lucky: 'A few bounces went your way. Your record got a nice bump from favorable scheduling.',
    fair: 'No luck to blame, no luck to thank. Your record is your resume.',
    unlucky: 'You drew some tough matchups. Your all-play says you were better than your record.',
    very_unlucky: 'You ran into buzzsaw after buzzsaw. Way better team than your record shows.',
  }

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <SectionHeader
        number="06"
        title="Luck"
        description="If you played all 11 other teams every week, how would you really stack up?"
      />

      {/* Three Cards */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Actual Record */}
        <div className="p-8 border border-border">
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-4">
            Actual Record
          </p>
          <p className="font-mono text-6xl md:text-7xl font-bold text-foreground mb-4">
            {actualRecord}
          </p>
          <div className="flex items-baseline gap-2">
            <p className="font-mono text-3xl font-bold text-foreground">
              {(actualWinPct * 100).toFixed(1)}%
            </p>
            <p className="font-mono text-sm text-muted-foreground">win rate</p>
          </div>
        </div>

        {/* All-Play Record */}
        <div className="p-8 border border-gold/50 bg-gold/5">
          <p className="font-mono text-xs text-gold uppercase tracking-widest mb-4">
            All-Play Record
          </p>
          <p className="font-mono text-6xl md:text-7xl font-bold text-gold mb-4">
            {allPlay.wins}-{allPlay.losses}
          </p>
          <div className="flex items-baseline gap-2">
            <p className="font-mono text-3xl font-bold text-gold">
              {(allPlay.winPct * 100).toFixed(1)}%
            </p>
            <p className="font-mono text-sm text-muted-foreground">win rate</p>
          </div>
          <p className="font-mono text-xs text-muted-foreground mt-4">
            {allPlay.wins + allPlay.losses} total matchups
          </p>
        </div>

        {/* Luck Factor */}
        <div className={`p-8 border ${
          luckStatus === 'very_lucky' || luckStatus === 'lucky' ? 'border-win/50 bg-win/5' :
          luckStatus === 'very_unlucky' || luckStatus === 'unlucky' ? 'border-loss/50 bg-loss/5' :
          'border-border'
        }`}>
          <p className={`font-mono text-xs uppercase tracking-widest mb-4 ${luckColor}`}>
            Luck Factor
          </p>
          <div className="flex items-center gap-4 mb-4">
            {luckIcon}
            <p className={`font-mono text-5xl md:text-6xl font-bold uppercase ${luckColor}`}>
              {luckLabel}
            </p>
          </div>
          <p className={`font-mono text-2xl font-bold ${luckColor}`}>
            {luckDiff > 0 ? '+' : ''}{luckPctDiff}%
          </p>
          <p className="font-mono text-xs text-muted-foreground mt-4 leading-relaxed">
            {luckMessages[luckStatus]}
          </p>
        </div>
      </div>

    </section>
  )
}
