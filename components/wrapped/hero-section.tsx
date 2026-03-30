'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Team, League } from '@/lib/types'
import { useCountUp } from '@/hooks/use-count-up'

interface HeroSectionProps {
  team: Team
  league: League
}

function CountUp({ value, decimals = 1, prefix = '' }: { value: number; decimals?: number; prefix?: string }) {
  const { ref, displayValue } = useCountUp(value, { decimals })
  return <span ref={ref}>{prefix}{displayValue}</span>
}

export function HeroSection({ team, league }: HeroSectionProps) {
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  })
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])
  const opacity = useTransform(scrollYProgress, [0, 0.6], [1, 0])

  const pointDiff = team.pointsFor - team.pointsAgainst
  const weeklyAvgDiff = pointDiff / 21
  const isPositive = pointDiff >= 0

  return (
    <section ref={heroRef} className="relative min-h-screen flex flex-col justify-center px-6 py-24 md:px-12 lg:px-24 overflow-hidden">
      <motion.div style={{ scale, opacity }} className="relative z-10 max-w-6xl">
        {/* Season badge */}
        <div className="flex items-center gap-4 mb-8">
          <span className="font-mono text-xs tracking-[0.3em] text-muted-foreground uppercase">
            {league.season} Season
          </span>
          <span className="font-mono text-xs text-muted-foreground/40">|</span>
          <span className="font-mono text-xs tracking-[0.3em] text-muted-foreground uppercase">
            {league.name}
          </span>
        </div>

        {/* Seed badge */}
        <div className="inline-flex items-center gap-3 mb-6">
          <div className={`w-16 h-16 flex items-center justify-center border ${
            team.seed === 1
              ? 'border-team-primary text-team-primary'
              : team.seed <= 4
                ? 'border-foreground/30 text-foreground'
                : 'border-muted-foreground/30 text-muted-foreground'
          }`}>
            <span className="font-mono text-3xl font-bold">
              {team.seed}
            </span>
          </div>
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
              Seed
            </p>
            <p className="font-mono text-sm text-foreground">
              {team.seed === 1 ? 'Regular Season Champion' : team.seed <= 4 ? 'Playoff Team' : team.seed <= 8 ? 'Playoff Contender' : 'Lottery Team'}
            </p>
          </div>
        </div>

        {/* Manager Name */}
        <h1 className="font-mono font-bold text-5xl sm:text-7xl md:text-8xl lg:text-[9rem] tracking-tighter leading-[0.85] text-foreground uppercase mb-4">
          {team.manager.split(' ')[0]}
        </h1>

        {/* Team Name */}
        <p className="font-mono text-lg md:text-xl text-muted-foreground tracking-wide mb-16">
          {team.name}
        </p>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12 panel-frosted p-6 -mx-6">
          {/* Record */}
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">
              Record
            </p>
            <p className="font-mono text-5xl md:text-6xl font-bold tracking-tight text-foreground">
              {team.record}
            </p>
          </div>

          {/* Points For */}
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">
              Points For
            </p>
            <p className="font-mono text-5xl md:text-6xl font-bold tracking-tight text-foreground">
              <CountUp value={team.pointsFor} />
            </p>
          </div>

          {/* Point Differential */}
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">
              Point Diff
            </p>
            <p className={`font-mono text-5xl md:text-6xl font-bold tracking-tight ${isPositive ? 'text-win' : 'text-loss'}`}>
              <CountUp value={pointDiff} prefix={isPositive ? '+' : ''} />
            </p>
          </div>

          {/* Weekly Avg Diff */}
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-2">
              Per Week
            </p>
            <p className={`font-mono text-5xl md:text-6xl font-bold tracking-tight ${isPositive ? 'text-win' : 'text-loss'}`}>
              <CountUp value={weeklyAvgDiff} prefix={isPositive ? '+' : ''} />
            </p>
          </div>
        </div>
      </motion.div>

      {/* Scroll indicator */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2">
        <div className="flex flex-col items-center gap-2 animate-pulse">
          <span className="font-mono text-xs text-muted-foreground/40 uppercase tracking-widest">
            Scroll
          </span>
          <div className="w-px h-8 bg-gradient-to-b from-muted-foreground/40 to-transparent" />
        </div>
      </div>
    </section>
  )
}
