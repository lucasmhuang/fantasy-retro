'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getTeamCSSVars, buildNameLookup } from '@/lib/team-colors'
import { useTeamData } from '@/hooks/use-team-data'
import { useActiveSection } from '@/hooks/use-active-section'
import { AmbientHalo } from '@/components/ui/ambient-halo'
import { SmoothScrollProvider } from '@/components/providers/smooth-scroll-provider'
import { ScrollReveal } from '@/components/ui/scroll-reveal'
import { HeroSection } from '@/components/wrapped/hero-section'
import { SeasonTimeline } from '@/components/wrapped/season-timeline'
import { TradeCenter } from '@/components/wrapped/trade-center'
import { WaiverWire } from '@/components/wrapped/waiver-wire'
import { RosterHeatmap } from '@/components/wrapped/roster-heatmap'
import { ScoringProfile } from '@/components/wrapped/scoring-profile'
import { AllPlayRecord } from '@/components/wrapped/all-play-record'
import { OptimalLineup } from '@/components/wrapped/optimal-lineup'
import { BenchMisplays } from '@/components/wrapped/bench-misplays'
import { AwardsSection } from '@/components/wrapped/awards-section'
import { HeadToHead } from '@/components/wrapped/head-to-head'
import { ReportCard } from '@/components/wrapped/report-card'
import { WrappedFooter } from '@/components/wrapped/wrapped-footer'
import { SectionNav } from '@/components/wrapped/section-nav'
import { ErrorState } from '@/components/ui/error-state'
import { ArrowLeft } from 'lucide-react'

export default function TeamWrappedPage() {
  const params = useParams()
  const teamId = params.id as string
  const { teamData, leagueMeta, isLoading, error } = useTeamData(teamId)
  const activeSection = useActiveSection()

  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />
  }

  if (isLoading || !teamData || !leagueMeta) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="font-mono text-muted-foreground tracking-widest text-sm uppercase animate-pulse">
          Loading your season...
        </div>
      </div>
    )
  }

  const { byName: nameMap } = buildNameLookup(leagueMeta.teams)

  const sections = [
    { id: 'hero', label: 'Overview' },
    { id: 'timeline', label: '01 Timeline' },
    { id: 'trades', label: '02 Trades' },
    { id: 'waivers', label: '03 Waivers' },
    { id: 'heatmap', label: '04 Roster' },
    { id: 'scoring', label: '05 Scoring' },
    { id: 'allplay', label: '06 Luck' },
    { id: 'optimal', label: '07 Optimal' },
    { id: 'bench', label: '08 Bench' },
    { id: 'awards', label: '09 Awards' },
    { id: 'h2h', label: '10 H2H' },
    { id: 'grades', label: '11 Grades' },
  ]

  return (
    <SmoothScrollProvider>
      <main
        className="min-h-screen relative overflow-x-hidden"
        style={getTeamCSSVars(Number(teamId))}
      >
        <AmbientHalo sectionCount={sections.length} />

        <Link
          href="/"
          className="fixed top-6 left-6 z-50 flex items-center gap-2 font-mono text-xs text-muted-foreground hover:text-foreground transition-colors uppercase tracking-widest"
        >
          <ArrowLeft className="w-4 h-4" />
          All Teams
        </Link>

        <SectionNav sections={sections} activeSection={activeSection} />

        <div data-section id="hero">
          <HeroSection team={teamData.team} league={teamData.league} />
        </div>

        <div data-section id="timeline">
          <SeasonTimeline weeklyResults={teamData.weeklyResults} nameMap={nameMap} />
        </div>

        <div data-section id="trades">
          <ScrollReveal>
            <TradeCenter trades={teamData.trades} replacementFPW={leagueMeta?.draftMeta?.replacementFPW} nameMap={nameMap} />
          </ScrollReveal>
        </div>

        <div data-section id="waivers">
          <ScrollReveal>
            <WaiverWire pickups={teamData.waiverPickups} />
          </ScrollReveal>
        </div>

        <div data-section id="heatmap">
          <ScrollReveal variant="blur">
            <RosterHeatmap heatmap={teamData.rosterHeatmap} weeklyResults={teamData.weeklyResults} nameMap={nameMap} />
          </ScrollReveal>
        </div>

        <div data-section id="scoring">
          <ScoringProfile profile={teamData.scoringProfile} leagueAvg={leagueMeta.leagueAvgScoringProfile} />
        </div>

        <div data-section id="allplay">
          <ScrollReveal>
            <AllPlayRecord allPlay={teamData.allPlayRecord} actualRecord={teamData.team.record} />
          </ScrollReveal>
        </div>

        <div data-section id="optimal">
          <ScrollReveal>
            <OptimalLineup data={teamData.optimalLineup} />
          </ScrollReveal>
        </div>

        <div data-section id="bench">
          <ScrollReveal>
            <BenchMisplays misplays={teamData.pointsLeftOnBench} />
          </ScrollReveal>
        </div>

        <div data-section id="awards">
          <AwardsSection awards={teamData.awards} nameMap={nameMap} />
        </div>

        <div data-section id="h2h">
          <ScrollReveal>
            <HeadToHead records={teamData.headToHead} nameMap={nameMap} />
          </ScrollReveal>
        </div>

        <div data-section id="grades">
          <ScrollReveal variant="scale">
            <ReportCard grades={teamData.grades} allPlay={teamData.allPlayRecord} finalPlacement={teamData.team.finalPlacement} />
          </ScrollReveal>
        </div>

        <ScrollReveal>
          <WrappedFooter league={teamData.league} />
        </ScrollReveal>
      </main>
    </SmoothScrollProvider>
  )
}
