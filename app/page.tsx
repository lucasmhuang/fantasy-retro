'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Users, ArrowLeftRight, Gavel, ClipboardList } from 'lucide-react';
import { useScrollBatch } from '@/hooks/use-scroll-batch';
import { useCountUp } from '@/hooks/use-count-up';
import { buildNameLookup } from '@/lib/team-colors';
import { Marquee } from '@/components/ui/marquee';
import { SmoothScrollProvider } from '@/components/providers/smooth-scroll-provider';
import { DraftRetrospective } from '@/components/wrapped/draft-retrospective';
import { TradeCatalog } from '@/components/wrapped/trade-catalog';
import { WaiverCatalog } from '@/components/wrapped/waiver-catalog';
import type { LeagueMeta } from '@/lib/types';

type Tab = 'teams' | 'trades' | 'waivers' | 'draft';

export default function HomePage() {
  const [league, setLeague] = useState<LeagueMeta | null>(null);
  const [hoveredTeam, setHoveredTeam] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('teams');

  useEffect(() => {
    fetch('/data/league_meta.json')
      .then((res) => res.json())
      .then((data) => setLeague(data));
  }, []);

  if (!league) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="font-mono text-muted-foreground tracking-widest text-sm uppercase">
          Loading...
        </div>
      </div>
    );
  }

  const { byName: nameMap } = buildNameLookup(league.teams);

  const tabs: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'teams', label: 'Teams', icon: Users },
    { id: 'trades', label: 'Trades', icon: ArrowLeftRight },
    { id: 'waivers', label: 'Waivers', icon: Gavel },
    { id: 'draft', label: 'Draft', icon: ClipboardList },
  ];

  return (
    <SmoothScrollProvider>
      <main className="min-h-screen bg-background">
        {/* Hero Section */}
        <HeroSection league={league} />

        {/* Marquee */}
        <Marquee className="py-6 border-y border-border/20" speed={40} pauseOnHover>
          {league.teams.map((team) => (
            <span key={team.id} className="font-mono text-sm text-muted-foreground/30 uppercase tracking-widest px-8">
              {team.manager.split(' ')[0]}
            </span>
          ))}
        </Marquee>

        {/* Tabs */}
        <section className="px-6 md:px-12 lg:px-24 mt-8">
          <div className="flex gap-0 border-b border-border/30 mb-8">
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`font-mono text-sm uppercase tracking-widest px-6 py-3 transition-colors duration-200 border-b-2 -mb-px ${
                  activeTab === tab.id
                    ? 'text-gold border-gold'
                    : 'text-muted-foreground border-transparent hover:text-foreground'
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </span>
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'teams' && (
            <TeamGrid
              teams={league.teams}
              hoveredTeam={hoveredTeam}
              setHoveredTeam={setHoveredTeam}
            />
          )}

          {activeTab === 'trades' && (
            <TradeCatalog
              trades={league.leagueTrades || []}
              replacementFPW={league.draftMeta?.replacementFPW}
              nameMap={nameMap}
            />
          )}

          {activeTab === 'waivers' && (
            <WaiverCatalog pickups={league.leaguePickups || []} nameMap={nameMap} />
          )}

          {activeTab === 'draft' &&
            league.draftAnalysis &&
            league.draftMeta &&
            league.draftGrades && (
              <DraftRetrospective
                picks={league.draftAnalysis}
                meta={league.draftMeta}
                teamGrades={league.draftGrades}
                nameMap={nameMap}
              />
            )}
        </section>

        {/* Spacer */}
        <div className="h-24" />

        {/* Footer */}
        <footer className="px-6 py-12 md:px-12 lg:px-24 border-t border-border/30">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <p className="font-mono text-sm text-muted-foreground">
                Fantasy Wrapped &mdash; {league.name}
              </p>
            </div>
            <p className="font-mono text-xs text-muted-foreground/60 tracking-widest uppercase">
              {league.season}
            </p>
          </div>
        </footer>
      </main>
    </SmoothScrollProvider>
  );
}

function CountUpDisplay({ value, decimals = 0, prefix = '' }: { value: number; decimals?: number; prefix?: string }) {
  const { ref, displayValue } = useCountUp(value, { decimals })
  return <span ref={ref}>{prefix}{displayValue}</span>
}

function HeroSection({ league }: { league: LeagueMeta }) {
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  })
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])
  const opacity = useTransform(scrollYProgress, [0, 0.6], [1, 0])

  return (
    <section ref={heroRef} className="relative min-h-[60vh] flex flex-col justify-end px-6 pb-16 md:px-12 lg:px-24 overflow-hidden">

      <motion.div style={{ scale, opacity }} className="relative z-10">
        <p className="font-mono text-muted-foreground text-xs tracking-[0.3em] uppercase mb-4">
          {league.season} Season Recap
        </p>
        <h1 className="font-mono font-bold text-6xl md:text-8xl lg:text-[10rem] tracking-tighter leading-[0.85] text-foreground uppercase">
          Fantasy
          <br />
          <span className="text-gold">Wrapped</span>
        </h1>
        <div className="mt-8 flex items-center gap-8">
          <div>
            <p className="font-mono text-3xl md:text-4xl font-bold text-foreground">
              <CountUpDisplay value={league.teams.length} decimals={0} />
            </p>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest">Managers</p>
          </div>
          <div>
            <p className="font-mono text-3xl md:text-4xl font-bold text-foreground">
              <CountUpDisplay value={21} decimals={0} />
            </p>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest">Weeks</p>
          </div>
          <div>
            <p className="font-mono text-3xl md:text-4xl font-bold text-gold">
              <CountUpDisplay value={1} decimals={0} />
            </p>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest">Champion</p>
          </div>
        </div>
      </motion.div>
    </section>
  )
}

function TeamGrid({
  teams,
  hoveredTeam,
  setHoveredTeam,
}: {
  teams: LeagueMeta['teams'];
  hoveredTeam: number | null;
  setHoveredTeam: (id: number | null) => void;
}) {
  const { ref: batchRef } = useScrollBatch({ stagger: 0.05 });
  return (
    <div ref={batchRef} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-background">
      {teams.map((team) => {
        const isHovered = hoveredTeam === team.id;
        const pointDiff = team.pointsFor - team.pointsAgainst;
        const isPositive = pointDiff >= 0;

        return (
          <Link
            key={team.id}
            data-batch-item
            href={`/team/${team.id}`}
            className="group relative bg-background p-8 transition-all duration-300 hover:bg-card"
            onMouseEnter={() => setHoveredTeam(team.id)}
            onMouseLeave={() => setHoveredTeam(null)}
          >
            {/* Placement Badge */}
            <div className="absolute top-6 right-6">
              <span
                className={`font-mono text-5xl font-bold transition-colors duration-300 ${
                  team.finalPlacement === 1
                    ? 'text-gold'
                    : team.finalPlacement <= 4
                      ? 'text-muted-foreground/40'
                      : 'text-muted-foreground/20'
                } ${isHovered ? 'text-foreground/30' : ''}`}
              >
                {String(team.finalPlacement).padStart(2, '0')}
              </span>
            </div>

            {/* Team Info */}
            <div className="min-h-[180px] flex flex-col justify-between">
              <div>
                <p className="font-mono text-xs text-muted-foreground tracking-widest uppercase mb-2">
                  {team.name}
                </p>
                <h2
                  className={`font-mono font-bold text-2xl tracking-tight leading-tight uppercase transition-colors duration-300 ${
                    isHovered ? 'text-gold' : 'text-foreground'
                  }`}
                >
                  {team.manager.split(' ')[0]}
                </h2>
              </div>

              <div className="flex items-end justify-between mt-6">
                <div>
                  <p className="font-mono text-3xl font-bold tracking-tight text-foreground">
                    {team.record}
                  </p>
                  <p
                    className={`font-mono text-sm mt-1 ${isPositive ? 'text-win' : 'text-loss'}`}
                  >
                    {isPositive ? '+' : ''}
                    {pointDiff.toFixed(1)} pts
                  </p>
                </div>

                <div className="text-right">
                  <p className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                    Points For
                  </p>
                  <p className="font-mono text-lg font-semibold text-foreground">
                    {team.pointsFor.toLocaleString(undefined, {
                      maximumFractionDigits: 1,
                    })}
                  </p>
                </div>
              </div>
            </div>

            {/* Hover indicator */}
            <div
              className={`absolute bottom-0 left-0 h-px bg-gold transition-all duration-300 ${
                isHovered ? 'w-full' : 'w-0'
              }`}
            />
          </Link>
        );
      })}
    </div>
  );
}
