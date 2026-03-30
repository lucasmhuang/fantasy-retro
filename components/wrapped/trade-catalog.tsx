'use client';

import {
  ArrowDown,
  ArrowLeftRight,
  ArrowUp,
  Info,
  Search,
  TrendingDown,
  TrendingUp,
  Trophy,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useScrollBatch } from '@/hooks/use-scroll-batch';
import { useCountUp } from '@/hooks/use-count-up';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { LeagueTrade, PlayerTradeStats } from '@/lib/types';

type SortKey = 'week' | 'value';

interface TeamGrade {
  team: string;
  grade: string;
  netPts: number;
}

const GRADE_COLORS: Record<string, string> = {
  'A+': 'text-win', A: 'text-win', 'A-': 'text-win',
  'B+': 'text-win/70', B: 'text-win/70', 'B-': 'text-win/70',
  'C+': 'text-muted-foreground', C: 'text-muted-foreground', 'C-': 'text-muted-foreground',
  'D+': 'text-loss/70', D: 'text-loss/70', F: 'text-loss',
};

interface TradeCatalogProps {
  trades: LeagueTrade[];
  replacementFPW?: number;
  nameMap?: Record<string, string>;
  teamGrades?: Record<string, TeamGrade>;
  enabled?: boolean;
  batchKey?: number;
}

function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const { ref, displayValue } = useCountUp(value, { decimals });
  return <span ref={ref}>{displayValue}</span>;
}

export function TradeCatalog({ trades, replacementFPW, nameMap = {}, teamGrades, enabled = true, batchKey }: TradeCatalogProps) {
  const n = (name: string) => nameMap[name] || name;
  const { ref: gradesBatchRef } = useScrollBatch({ stagger: 0.05, enabled, key: batchKey });
  const [teamFilter, setTeamFilter] = useState<string | null>(null);
  const [playerSearch, setPlayerSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('week');
  const [sortAsc, setSortAsc] = useState(true);
  const [filterTick, setFilterTick] = useState(0);
  const { ref: batchRef } = useScrollBatch({ enabled, key: (batchKey ?? 0) + filterTick });

  const allTeams = useMemo(() => {
    const names = new Set<string>();
    for (const t of trades) {
      names.add(t.team1);
      names.add(t.team2);
    }
    return [...names].sort();
  }, [trades]);

  const filtered = useMemo(() => {
    let result = [...trades];
    if (teamFilter) {
      result = result.filter(
        (t) => t.team1 === teamFilter || t.team2 === teamFilter,
      );
    }
    if (playerSearch.trim()) {
      const q = playerSearch.toLowerCase();
      result = result.filter((t) => {
        const allPlayers = [...t.team1Sent, ...t.team2Sent];
        return allPlayers.some((p) => p.toLowerCase().includes(q));
      });
    }
    const dir = sortAsc ? 1 : -1;
    result.sort((a, b) =>
      sortBy === 'week'
        ? ((a.week ?? 0) - (b.week ?? 0)) * dir
        : (a.net - b.net) * dir,
    );
    return result;
  }, [trades, teamFilter, playerSearch, sortBy, sortAsc]);

  if (trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="font-mono text-6xl md:text-8xl font-bold text-muted-foreground/20">
          0
        </p>
        <p className="font-mono text-lg text-muted-foreground mt-4">
          No trades made this season
        </p>
      </div>
    );
  }

  const biggestWin = [...trades].sort((a, b) => b.net - a.net)[0];

  return (
    <div className="space-y-8">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Total Trades
          </p>
          <p className="font-mono text-5xl font-bold text-foreground">
            <CountUp value={trades.length} />
          </p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Biggest Win
          </p>
          <p className="font-mono text-2xl font-bold text-win">
            +{biggestWin.net.toFixed(1)} pts
          </p>
          <p className="font-mono text-xs text-muted-foreground mt-1">
            {n(biggestWin.winner)} dunked on{' '}
            {n(biggestWin.winner === biggestWin.team1 ? biggestWin.team2 : biggestWin.team1)}
          </p>
        </div>
        <div className="hidden md:block">
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Most Active
          </p>
          <p className="font-mono text-2xl font-bold text-foreground">
            {n(mostActiveTrader(trades))}
          </p>
        </div>
      </div>

      {/* Team Trade Grades */}
      {teamGrades && (
        <div>
          <h3 className="font-mono text-sm font-medium text-foreground uppercase tracking-widest mb-4">
            Team Trade Grades
          </h3>
          <div ref={gradesBatchRef} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(teamGrades)
              .sort(([, a], [, b]) => b.netPts - a.netPts)
              .map(([tid, tg]) => (
                <div key={tid} data-batch-item className="border border-border/50 p-4 flex items-center justify-between">
                  <div>
                    <p className="font-mono text-sm font-bold text-foreground truncate max-w-[140px]">
                      {n(tg.team)}
                    </p>
                    <p className="font-mono text-xs text-muted-foreground">
                      {tg.netPts >= 0 ? '+' : ''}{tg.netPts.toFixed(0)} net pts
                    </p>
                  </div>
                  <span className={`font-mono text-3xl font-bold ${GRADE_COLORS[tg.grade] || 'text-foreground'}`}>
                    {tg.grade}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="space-y-3">
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
              onClick={() => { setTeamFilter(teamFilter === team ? null : team); setFilterTick((t) => t + 1); }}
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
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            value={playerSearch}
            onChange={(e) => setPlayerSearch(e.target.value)}
            placeholder="Search player..."
            className="w-full font-mono text-sm bg-transparent border border-border/50 pl-9 pr-3 py-2 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-gold/50"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {(['week', 'value'] as SortKey[]).map((key) => {
            const active = sortBy === key;
            const defaultAsc = key === 'week';
            return (
              <button
                type="button"
                key={key}
                onClick={() => {
                  if (active) {
                    setSortAsc((prev) => !prev);
                  } else {
                    setSortBy(key);
                    setSortAsc(defaultAsc);
                  }
                }}
                className={`flex items-center gap-1 font-mono text-xs uppercase tracking-widest px-2 py-1 border transition-colors ${
                  active ? 'border-foreground/30 text-foreground' : 'border-border/50 text-muted-foreground hover:text-foreground'
                }`}
              >
                {key === 'week' ? 'Timeline' : 'Win/Loss'}
                {active && (sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Results count */}
      {(teamFilter || playerSearch) && (
        <p className="font-mono text-xs text-muted-foreground">
          {filtered.length} of {trades.length} trades
        </p>
      )}

      {/* Trade Cards */}
      <div ref={batchRef} className="space-y-6">
        {filtered.map((trade, index) => (
          <TradeCard
            key={`${index}-${trade.week}-${trade.team1}`}
            trade={trade}
            rank={index + 1}
            replacementFPW={replacementFPW}
            nameMap={nameMap}
          />
        ))}
      </div>
    </div>
  );
}

function mostActiveTrader(trades: LeagueTrade[]): string {
  const counts: Record<string, number> = {};
  for (const trade of trades) {
    counts[trade.team1] = (counts[trade.team1] || 0) + 1;
    counts[trade.team2] = (counts[trade.team2] || 0) + 1;
  }
  let maxName = '';
  let maxCount = 0;
  for (const [name, count] of Object.entries(counts)) {
    if (count > maxCount) {
      maxName = name;
      maxCount = count;
    }
  }
  return maxName;
}

function TradeCard({
  trade,
  rank,
  replacementFPW,
  nameMap = {},
}: {
  trade: LeagueTrade;
  rank: number;
  replacementFPW?: number;
  nameMap?: Record<string, string>;
}) {
  const n = (name: string) => nameMap[name] || name;
  const team1ReceivedPts = trade.team2PtsROS;
  const team2ReceivedPts = trade.team1PtsROS;
  const team1Won = team1ReceivedPts > team2ReceivedPts;
  const team1Net = team1ReceivedPts - team2ReceivedPts;

  return (
    <div data-batch-item className="border border-border/50 hover:border-border transition-colors duration-300">
      {/* Header */}
      <div className="flex items-center justify-between p-6 pb-4">
        <div className="flex items-center gap-4">
          <span className="font-mono text-3xl font-bold text-muted-foreground/20">
            {String(rank).padStart(2, '0')}
          </span>
          <div>
            <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
              Week {trade.week ?? '?'}
            </p>
            <div className="flex items-center gap-2 font-mono text-lg font-bold text-foreground">
              {n(trade.team1)}
              <ArrowLeftRight className="w-4 h-4 text-muted-foreground" />
              {n(trade.team2)}
            </div>
          </div>
        </div>
        <div className="text-right flex items-center gap-3">
          {trade.slotAdjustment ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex items-center gap-1 font-mono text-xs uppercase tracking-wider px-2 py-1 bg-muted/30 text-muted-foreground border border-border/50 cursor-help">
                  <Info className="w-3 h-3" />
                  Roster-adjusted
                </span>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>
                  This trade was uneven. The freed roster spot is
                  valued at replacement-level production (~
                  {replacementFPW ?? '?'} fantasy points per week) for the
                  remaining weeks.
                </p>
              </TooltipContent>
            </Tooltip>
          ) : null}
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-gold" />
            <span className="font-mono text-sm font-bold text-gold">
              {trade.winner}
            </span>
          </div>
        </div>
      </div>

      {/* Trade Details — each side shows what that team RECEIVED */}
      <div className="flex flex-col md:flex-row items-stretch gap-4 px-6 pb-6">
        <TradeTeamSide
          teamName={n(trade.team1)}
          stats={trade.team2Stats || []}
          ptsROS={team1ReceivedPts}
          net={team1Net}
          won={team1Won}
        />
        <div className="hidden md:flex items-center justify-center px-2">
          <div className="w-px h-full bg-border" />
        </div>
        <TradeTeamSide
          teamName={n(trade.team2)}
          stats={trade.team1Stats || []}
          ptsROS={team2ReceivedPts}
          net={-team1Net}
          won={!team1Won}
        />
      </div>
    </div>
  );
}

function TradeTeamSide({
  teamName,
  stats,
  ptsROS,
  net,
  won,
}: {
  teamName: string;
  stats: PlayerTradeStats[];
  ptsROS: number;
  net: number;
  won: boolean;
}) {
  return (
    <div
      className={`flex-1 p-4 ${won ? 'bg-win/5 border border-win/20' : 'bg-loss/5 border border-loss/20'}`}
    >
      <div className="flex items-center justify-between mb-1">
        <p
          className={`font-mono text-xs uppercase tracking-widest ${won ? 'text-win' : 'text-loss'}`}
        >
          {teamName}
        </p>
        <div
          className={`flex items-center gap-1 font-mono text-sm font-bold ${won ? 'text-win' : 'text-loss'}`}
        >
          {won ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          {net >= 0 ? '+' : ''}
          {net.toFixed(1)}
        </div>
      </div>
      <p className="font-mono text-xs text-muted-foreground/50 uppercase tracking-widest mb-3">
        Received
      </p>
      <div className="space-y-2">
        {stats.length > 0
          ? stats.map((s) => (
              <div
                key={s.player}
                className="flex items-baseline justify-between gap-2"
              >
                <p className="font-mono text-base text-foreground truncate">
                  {s.player}
                </p>
                <p className="font-mono text-xs text-muted-foreground whitespace-nowrap">
                  {s.gamesROS}G &middot; {s.ppgROS} PPG
                </p>
              </div>
            ))
          : null}
      </div>
      <p className="font-mono text-sm text-muted-foreground mt-3">
        {ptsROS.toFixed(1)} pts ROS
      </p>
    </div>
  );
}
