'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
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

  const tabs: { id: Tab; label: string }[] = [
    { id: 'teams', label: 'Teams' },
    { id: 'trades', label: 'Trades' },
    { id: 'waivers', label: 'Waivers' },
    { id: 'draft', label: 'Draft' },
  ];

  return (
    <SmoothScrollProvider>
      <main className="min-h-screen bg-background">
        {/* Hero Section */}
        <section className="relative min-h-[60vh] flex flex-col justify-end px-6 pb-16 md:px-12 lg:px-24">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gold/5 rounded-full blur-[120px]" />
            <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-gold/3 rounded-full blur-[100px]" />
          </div>

          <div className="relative z-10">
            <p className="font-mono text-muted-foreground text-xs tracking-[0.3em] uppercase mb-4">
              {league.season} Season Recap
            </p>
            <h1 className="font-mono font-bold text-6xl md:text-8xl lg:text-[10rem] tracking-tighter leading-[0.85] text-foreground uppercase">
              Fantasy
              <br />
              <span className="text-gold">Wrapped</span>
            </h1>
            <p className="mt-8 font-mono text-muted-foreground text-sm tracking-wide max-w-md">
              {league.name} &mdash; {league.teams.length} managers, 21 weeks,
              one champion. Select your team to see your season story.
            </p>
          </div>
        </section>

        {/* Tabs */}
        <section className="px-6 md:px-12 lg:px-24">
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
                {tab.label}
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
            />
          )}

          {activeTab === 'waivers' && (
            <WaiverCatalog pickups={league.leaguePickups || []} />
          )}

          {activeTab === 'draft' &&
            league.draftAnalysis &&
            league.draftMeta &&
            league.draftGrades && (
              <DraftRetrospective
                picks={league.draftAnalysis}
                meta={league.draftMeta}
                teamGrades={league.draftGrades}
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

function TeamGrid({
  teams,
  hoveredTeam,
  setHoveredTeam,
}: {
  teams: LeagueMeta['teams'];
  hoveredTeam: number | null;
  setHoveredTeam: (id: number | null) => void;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-border/30">
      {teams.map((team) => {
        const isHovered = hoveredTeam === team.id;
        const pointDiff = team.pointsFor - team.pointsAgainst;
        const isPositive = pointDiff >= 0;

        return (
          <Link
            key={team.id}
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
                  {team.manager}
                </p>
                <h2
                  className={`font-mono font-bold text-2xl tracking-tight leading-tight uppercase transition-colors duration-300 ${
                    isHovered ? 'text-gold' : 'text-foreground'
                  }`}
                >
                  {team.name}
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
