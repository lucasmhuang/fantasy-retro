'use client';

import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useScrollBatch } from '@/hooks/use-scroll-batch';
import { useCountUp } from '@/hooks/use-count-up';

function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const { ref, displayValue } = useCountUp(value, { decimals });
  return <span ref={ref}>{displayValue}</span>;
}
import type { DraftMeta, DraftPick, DraftTeamGrade } from '@/lib/types';

interface DraftRetrospectiveProps {
  picks: DraftPick[];
  meta: DraftMeta;
  teamGrades: Record<string, DraftTeamGrade>;
  enabled?: boolean;
  batchKey?: number;
}

const LABEL_CONFIG: Record<string, { color: string; bg: string }> = {
  steal: { color: 'text-win', bg: 'bg-win/20' },
  value: { color: 'text-win/80', bg: 'bg-win/10' },
  fair: { color: 'text-muted-foreground', bg: 'bg-muted/20' },
  reach: { color: 'text-loss/80', bg: 'bg-loss/10' },
  bust: { color: 'text-loss', bg: 'bg-loss/20' },
};

const GRADE_COLORS: Record<string, string> = {
  'A+': 'text-win',
  A: 'text-win',
  'A-': 'text-win',
  'B+': 'text-win/70',
  B: 'text-win/70',
  'B-': 'text-win/70',
  'C+': 'text-muted-foreground',
  C: 'text-muted-foreground',
  'C-': 'text-muted-foreground',
  'D+': 'text-loss/70',
  D: 'text-loss/70',
  F: 'text-loss',
};

type BoardView = 'round' | 'value';
type SortKey = 'value' | 'grade' | 'seasonPts' | 'ppg' | 'overall';

export function DraftRetrospective({
  picks,
  meta,
  teamGrades,
  nameMap = {},
  enabled = true,
  batchKey,
}: DraftRetrospectiveProps & { nameMap?: Record<string, string> }) {
  const n = (name: string) => nameMap[name] || name;
  const [expandedRound, setExpandedRound] = useState<number | null>(1);
  const [showMethodology, setShowMethodology] = useState(false);
  const [boardView, setBoardView] = useState<BoardView>('round');
  const [sortKey, setSortKey] = useState<SortKey>('value');
  const [sortAsc, setSortAsc] = useState(false);
  const { ref: gradesBatchRef } = useScrollBatch({ stagger: 0.05, enabled, key: batchKey });
  const [teamFilter, setTeamFilter] = useState<string | null>(null);
  const [filterTick, setFilterTick] = useState(0);
  const { ref: picksBatchRef } = useScrollBatch({ stagger: 0.03, enabled, key: (batchKey ?? 0) + filterTick });
  const { ref: roundsBatchRef } = useScrollBatch({ stagger: 0.06, enabled, key: (batchKey ?? 0) + filterTick });

  const maxRound = Math.max(...picks.map((p) => p.round));
  const rounds = Array.from({ length: maxRound }, (_, i) => i + 1);
  const picksPerRound = picks.filter((p) => p.round === 1).length;

  const sortedTeamGrades = Object.entries(teamGrades).sort(
    ([, a], [, b]) => b.avgValueOverDraft - a.avgValueOverDraft,
  );

  const steals = [...picks]
    .sort((a, b) => b.valueOverDraft - a.valueOverDraft)
    .slice(0, 5);
  const busts = [...picks]
    .sort((a, b) => a.valueOverDraft - b.valueOverDraft)
    .slice(0, 5);

  const allTeams = useMemo(() => {
    const names = new Set(picks.map((p) => p.team));
    return [...names].sort();
  }, [picks]);

  const valueSorted = useMemo(() => {
    const filtered = teamFilter
      ? picks.filter((p) => p.team === teamFilter)
      : [...picks];
    const key = sortKey;
    filtered.sort((a, b) => {
      let cmp = 0;
      if (key === 'value') cmp = a.valueOverDraft - b.valueOverDraft;
      else if (key === 'seasonPts') cmp = a.seasonPts - b.seasonPts;
      else if (key === 'ppg') cmp = a.ppg - b.ppg;
      else if (key === 'overall') cmp = a.overall - b.overall;
      else if (key === 'grade') cmp = a.valueOverDraft - b.valueOverDraft;
      return sortAsc ? cmp : -cmp;
    });
    return filtered;
  }, [picks, sortKey, sortAsc, teamFilter]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === 'overall');
    }
  }

  return (
    <div className="space-y-12">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Players Drafted
          </p>
          <p className="font-mono text-5xl font-bold text-foreground">
            <CountUp value={picks.length} />
          </p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Rounds
          </p>
          <p className="font-mono text-5xl font-bold text-foreground">
            <CountUp value={maxRound} />
          </p>
        </div>
        {steals[0] && (
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
              Biggest Steal
            </p>
            <p className="font-mono text-lg font-bold text-win">
              {steals[0].player}
            </p>
            <p className="font-mono text-xs text-muted-foreground">
              Pick {steals[0].overall} &rarr; Rank {steals[0].seasonRank}
            </p>
          </div>
        )}
        {busts[0] && (
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
              Biggest Bust
            </p>
            <p className="font-mono text-lg font-bold text-loss">
              {busts[0].player}
            </p>
            <p className="font-mono text-xs text-muted-foreground">
              Pick {busts[0].overall} &rarr; Rank {busts[0].seasonRank}
            </p>
          </div>
        )}
      </div>

      {/* Methodology */}
      <div>
        <button
          type="button"
          onClick={() => setShowMethodology(!showMethodology)}
          className="flex items-center gap-2 font-mono text-xs text-muted-foreground hover:text-foreground uppercase tracking-widest transition-colors"
        >
          <Info className="w-3.5 h-3.5" />
          {showMethodology ? 'Hide' : 'How it works'}
          {showMethodology ? (
            <ChevronUp className="w-3 h-3" />
          ) : (
            <ChevronDown className="w-3 h-3" />
          )}
        </button>
        {showMethodology && (
          <div className="mt-3 p-4 border border-border/50 bg-card/30">
            <p className="font-mono text-xs text-muted-foreground leading-relaxed">
              Each pick is graded by comparing draft position to season rank.
              Season rank is based on adjusted total points &mdash; actual
              points scored plus replacement-level production (~
              {meta.replacementFPW + ' '} fantasy points per week) for any weeks
              missed, capped at the player&apos;s own production rate.
            </p>
          </div>
        )}
      </div>

      {/* Team Draft Grades */}
      <div>
        <h3 className="font-mono text-sm font-medium text-foreground uppercase tracking-widest mb-4">
          Team Draft Grades
        </h3>
        <div ref={gradesBatchRef} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {sortedTeamGrades.map(
            ([tid, tg]) => (
              <div
                key={tid}
                data-batch-item
                className="border border-border/50 p-4 flex items-center justify-between"
              >
                <div>
                  <p className="font-mono text-sm font-bold text-foreground truncate max-w-[140px]">
                    {n(tg.team)}
                  </p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {tg.avgValueOverDraft >= 0 ? '+' : ''}
                    {tg.avgValueOverDraft.toFixed(1)} avg
                  </p>
                </div>
                <span
                  className={`font-mono text-3xl font-bold ${GRADE_COLORS[tg.grade] || 'text-foreground'}`}
                >
                  {tg.grade}
                </span>
              </div>
            ),
          )}
        </div>
      </div>

      {/* Steals & Busts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PickList title="Top Steals" picks={steals} variant="win" nameMap={nameMap} />
        <PickList title="Biggest Busts" picks={busts} variant="loss" nameMap={nameMap} />
      </div>

      {/* Draft Board */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-mono text-sm text-muted-foreground uppercase tracking-widest">
            Draft Board
          </h3>
          <div className="flex gap-0 border border-border/50">
            <button
              type="button"
              onClick={() => { setBoardView('round'); setFilterTick((t) => t + 1); }}
              className={`font-mono text-xs uppercase tracking-widest px-3 py-1.5 transition-colors ${
                boardView === 'round'
                  ? 'bg-gold/20 text-gold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              By Round
            </button>
            <button
              type="button"
              onClick={() => { setBoardView('value'); setFilterTick((t) => t + 1); }}
              className={`font-mono text-xs uppercase tracking-widest px-3 py-1.5 border-l border-border/50 transition-colors ${
                boardView === 'value'
                  ? 'bg-gold/20 text-gold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All Picks
            </button>
          </div>
        </div>

        {boardView === 'round' ? (
          <div ref={roundsBatchRef} className="space-y-2">
            {rounds.map((round) => {
              const roundPicks = picks
                .filter((p) => p.round === round)
                .sort((a, b) => a.pick - b.pick);
              const isExpanded = expandedRound === round;
              const avgGrade =
                roundPicks.reduce((s, p) => s + p.valueOverDraft, 0) /
                roundPicks.length;
              return (
                <div key={round} data-batch-item className="border border-border/50">
                  <button
                    type="button"
                    onClick={() => setExpandedRound(isExpanded ? null : round)}
                    className="w-full flex items-center justify-between p-4 hover:bg-card/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <span className="font-mono text-2xl font-bold text-muted-foreground/30">
                        R{round}
                      </span>
                      <span className="font-mono text-sm text-foreground">
                        Picks {(round - 1) * picksPerRound + 1}&ndash;
                        {round * picksPerRound}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span
                        className={`font-mono text-xs ${avgGrade >= 0 ? 'text-win' : 'text-loss'}`}
                      >
                        avg {avgGrade >= 0 ? '+' : ''}
                        {avgGrade.toFixed(1)}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="border-t border-border/50">
                      {roundPicks.map((pick) => (
                        <DraftPickRow
                          key={pick.overall}
                          pick={pick}
                          nameMap={nameMap}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div>
            {/* Team filter + sort controls */}
            <div className="space-y-3 mb-4">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => { setTeamFilter(null); setFilterTick((t) => t + 1); }}
                  className={`font-mono text-xs uppercase tracking-widest px-3 py-1.5 border transition-colors ${
                    !teamFilter
                      ? 'border-gold text-gold'
                      : 'border-border/50 text-muted-foreground hover:text-foreground'
                  }`}
                >
                  All
                </button>
                {allTeams.map((team) => (
                  <button
                    type="button"
                    key={team}
                    onClick={() => {
                      setTeamFilter(teamFilter === team ? null : team);
                      setFilterTick((t) => t + 1);
                    }}
                    className={`font-mono text-xs uppercase tracking-widest px-3 py-1.5 border transition-colors ${
                      teamFilter === team
                        ? 'border-gold text-gold'
                        : 'border-border/50 text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {n(team)}
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {(['value', 'seasonPts', 'ppg', 'overall'] as SortKey[]).map(
                  (key) => (
                    <button
                      type="button"
                      key={key}
                      onClick={() => toggleSort(key)}
                      className={`flex items-center gap-1 font-mono text-xs uppercase tracking-widest px-2 py-1 border transition-colors ${
                        sortKey === key
                          ? 'border-foreground/30 text-foreground'
                          : 'border-border/50 text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {key === 'seasonPts'
                        ? 'Pts'
                        : key === 'overall'
                          ? 'Pick'
                          : key}
                      {sortKey === key && (sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />)}
                    </button>
                  ),
                )}
              </div>
            </div>
            <div ref={picksBatchRef} className="border border-border/50">
              {valueSorted.map((pick) => (
                <DraftPickRow key={pick.overall} pick={pick} nameMap={nameMap} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PickList({
  title,
  picks,
  variant,
  nameMap = {},
}: {
  title: string;
  picks: DraftPick[];
  variant: 'win' | 'loss';
  nameMap?: Record<string, string>;
}) {
  const n = (name: string) => nameMap[name] || name;
  const { ref: listBatchRef } = useScrollBatch({ stagger: 0.06 });
  return (
    <div
      className={`border p-6 ${variant === 'win' ? 'border-win/30' : 'border-loss/30'}`}
    >
      <h3
        className={`font-mono text-xs uppercase tracking-widest mb-4 ${variant === 'win' ? 'text-win' : 'text-loss'}`}
      >
        {title}
      </h3>
      <div ref={listBatchRef} className="space-y-3">
        {picks.map((pick, i) => {
          const delta = pick.overall - pick.seasonRank;
          return (
            <div
              key={pick.overall}
              data-batch-item
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-lg font-bold text-muted-foreground/30 w-6">
                  {i + 1}
                </span>
                <div>
                  <p className="font-mono text-sm font-bold text-foreground">
                    {pick.player}
                  </p>
                  <p className="font-mono text-xs text-muted-foreground">
                    Pick {pick.overall} &rarr; Rank {pick.seasonRank} &mdash;{' '}
                    {n(pick.team)}
                  </p>
                </div>
              </div>
              <span
                className={`font-mono text-sm font-bold ${variant === 'win' ? 'text-win' : 'text-loss'}`}
              >
                {delta >= 0 ? '+' : ''}
                {delta}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DraftPickRow({ pick, nameMap = {} }: { pick: DraftPick; nameMap?: Record<string, string> }) {
  const n = (name: string) => nameMap[name] || name;
  const labelCfg = LABEL_CONFIG[pick.label] || LABEL_CONFIG.fair;
  const delta = pick.valueOverDraft;

  return (
    <div data-batch-item className="flex items-center gap-4 px-4 py-3 hover:bg-card/30 transition-colors border-b border-border/30 last:border-b-0">
      <span className="font-mono text-xs text-muted-foreground w-8 text-right shrink-0">
        #{pick.overall}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-mono text-sm font-bold text-foreground truncate">
            {pick.player}
          </p>
          <span
            className={`font-mono text-xs uppercase tracking-wider px-1.5 py-0.5 ${labelCfg.bg} ${labelCfg.color}`}
          >
            {pick.label}
          </span>
        </div>
        <p className="font-mono text-xs text-muted-foreground truncate">
          {n(pick.team)}
        </p>
      </div>
      <div className="text-right shrink-0 hidden md:block">
        <p className="font-mono text-sm font-bold text-foreground">
          {pick.seasonPts.toFixed(0)} pts
        </p>
        <p className="font-mono text-xs text-muted-foreground">
          {pick.gamesPlayed} GP &middot; {pick.ppg} PPG
        </p>
      </div>
      <div className="text-right shrink-0 w-10 md:w-16">
        <p
          className={`font-mono text-lg font-bold ${GRADE_COLORS[pick.grade] || 'text-foreground'}`}
        >
          {pick.grade}
        </p>
        <p
          className={`font-mono text-xs ${delta >= 0 ? 'text-win' : 'text-loss'}`}
        >
          {delta >= 0 ? '+' : ''}
          {delta}
        </p>
      </div>
    </div>
  );
}
