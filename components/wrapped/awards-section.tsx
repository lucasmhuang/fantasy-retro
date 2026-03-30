'use client'

import { Awards } from '@/lib/types'
import { Star, Armchair, HeartCrack, Zap, Clover, CloudLightning } from 'lucide-react'
import { motion } from 'framer-motion'
import { ParallaxNumber } from '@/components/ui/parallax-number'

interface AwardsSectionProps {
  awards: Awards
  nameMap?: Record<string, string>
}

export function AwardsSection({ awards, nameMap = {} }: AwardsSectionProps) {
  const awardCards = [
    {
      key: 'mvp',
      title: 'Season MVP',
      icon: Star,
      data: awards.mvp,
      color: 'gold',
      bgClass: 'border-gold/50 bg-gold/5',
      render: awards.mvp ? (
        <>
          <p className="font-mono text-3xl md:text-4xl font-bold text-gold mb-2">{awards.mvp.player}</p>
          <div className="mt-4">
            <p className="font-mono text-xs text-muted-foreground">Total Pts</p>
            <p className="font-mono text-xl font-bold text-foreground">{awards.mvp.totalPts.toFixed(1)}</p>
          </div>
        </>
      ) : null,
    },
    {
      key: 'benchWarmer',
      title: 'Bench Warmer',
      icon: Armchair,
      data: awards.benchWarmer,
      color: 'muted',
      bgClass: 'border-muted-foreground/30',
      render: awards.benchWarmer ? (
        <>
          <p className="font-mono text-2xl md:text-3xl font-bold text-muted-foreground mb-2">{awards.benchWarmer.player}</p>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <p className="font-mono text-xs text-muted-foreground">Avg Pts/Week</p>
              <p className="font-mono text-xl font-bold text-foreground">{awards.benchWarmer.avgPts.toFixed(1)}</p>
            </div>
            <div>
              <p className="font-mono text-xs text-muted-foreground">Weeks Rostered</p>
              <p className="font-mono text-xl font-bold text-foreground">{awards.benchWarmer.weeks}</p>
            </div>
          </div>
        </>
      ) : null,
    },
    {
      key: 'heartbreakLoss',
      title: 'Heartbreak Loss',
      icon: HeartCrack,
      data: awards.heartbreakLoss,
      color: 'loss',
      bgClass: 'border-loss/50 bg-loss/5',
      render: awards.heartbreakLoss ? (
        <>
          <p className="font-mono text-sm text-loss mb-2">Week {awards.heartbreakLoss.week}</p>
          <p className="font-mono text-2xl md:text-3xl font-bold text-foreground mb-1">vs {nameMap[awards.heartbreakLoss.opponent] || awards.heartbreakLoss.opponent}</p>
          <p className="font-mono text-sm text-muted-foreground">{awards.heartbreakLoss.score.toFixed(1)} – {awards.heartbreakLoss.oppScore.toFixed(1)}</p>
          <p className="font-mono text-4xl font-bold text-loss">-{awards.heartbreakLoss.margin.toFixed(1)}</p>
        </>
      ) : null,
    },
    {
      key: 'statementWin',
      title: 'Statement Win',
      icon: Zap,
      data: awards.statementWin,
      color: 'orange',
      bgClass: 'border-chart-3/50 bg-chart-3/5',
      render: awards.statementWin ? (
        <>
          <p className="font-mono text-sm text-chart-3 mb-2">Week {awards.statementWin.week}</p>
          <p className="font-mono text-2xl md:text-3xl font-bold text-foreground mb-1">vs {nameMap[awards.statementWin.opponent] || awards.statementWin.opponent}</p>
          <p className="font-mono text-sm text-muted-foreground">{awards.statementWin.score.toFixed(1)} – {awards.statementWin.oppScore.toFixed(1)}</p>
          <p className="font-mono text-4xl font-bold text-win">+{awards.statementWin.margin.toFixed(1)}</p>
        </>
      ) : null,
    },
    {
      key: 'luckyWin',
      title: 'Lucky Win',
      icon: Clover,
      data: awards.luckyWin,
      color: 'win',
      bgClass: 'border-win/50 bg-win/5',
      render: awards.luckyWin ? (
        <>
          <p className="font-mono text-sm text-win mb-2">Week {awards.luckyWin.week}</p>
          <p className="font-mono text-2xl md:text-3xl font-bold text-foreground mb-1">vs {nameMap[awards.luckyWin.opponent] || awards.luckyWin.opponent}</p>
          <p className="font-mono text-sm text-muted-foreground mt-2">
            League rank #{awards.luckyWin.leagueRank} that week — still won
          </p>
          <p className="font-mono text-xs text-muted-foreground">{awards.luckyWin.score.toFixed(1)} – {awards.luckyWin.oppScore.toFixed(1)}</p>
        </>
      ) : null,
    },
    {
      key: 'unluckyLoss',
      title: 'Unlucky Loss',
      icon: CloudLightning,
      data: awards.unluckyLoss,
      color: 'loss',
      bgClass: 'border-loss/50 bg-loss/5',
      render: awards.unluckyLoss ? (
        <>
          <p className="font-mono text-sm text-loss mb-2">Week {awards.unluckyLoss.week}</p>
          <p className="font-mono text-2xl md:text-3xl font-bold text-foreground mb-1">vs {nameMap[awards.unluckyLoss.opponent] || awards.unluckyLoss.opponent}</p>
          <p className="font-mono text-sm text-muted-foreground mt-2">
            League rank #{awards.unluckyLoss.leagueRank} that week — still lost
          </p>
          <p className="font-mono text-xs text-muted-foreground">{awards.unluckyLoss.score.toFixed(1)} – {awards.unluckyLoss.oppScore.toFixed(1)}</p>
        </>
      ) : null,
    },
  ]

  const validAwards = awardCards.filter(card => card.data != null)

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <div className="mb-16">
        <ParallaxNumber gradient className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/10">
          09
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Awards
        </h2>
        <p className="font-mono text-base text-muted-foreground mt-2">
          The highs, the lows, and everything in between.
        </p>
      </div>

      <motion.div
        className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-100px' }}
      >
        {validAwards.map((card, index) => {
          const Icon = card.icon
          return (
            <motion.div
              key={card.key}
              custom={index}
              variants={{
                hidden: { opacity: 0, scale: 0.92, y: 20 },
                visible: (i: number) => ({
                  opacity: 1,
                  scale: 1,
                  y: 0,
                  transition: { delay: i * 0.12, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] },
                }),
              }}
              className={`relative p-6 border transition-all hover:scale-[1.02] ${card.bgClass} ${
                card.key === 'mvp' ? 'md:col-span-2 lg:col-span-1 animate-pulse-gold' : ''
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <Icon className={`w-6 h-6 ${
                  card.color === 'gold' ? 'text-gold' :
                  card.color === 'loss' ? 'text-loss' :
                  card.color === 'win' ? 'text-win' :
                  card.color === 'orange' ? 'text-chart-3' :
                  'text-muted-foreground'
                }`} />
                <p className={`font-mono text-xs uppercase tracking-widest ${
                  card.color === 'gold' ? 'text-gold' :
                  card.color === 'loss' ? 'text-loss' :
                  card.color === 'win' ? 'text-win' :
                  card.color === 'orange' ? 'text-chart-3' :
                  'text-muted-foreground'
                }`}>
                  {card.title}
                </p>
              </div>
              {card.render}
            </motion.div>
          )
        })}
      </motion.div>

      {validAwards.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <p className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/20">?</p>
          <p className="font-mono text-lg text-muted-foreground mt-4">No awards data available</p>
        </div>
      )}
    </section>
  )
}
