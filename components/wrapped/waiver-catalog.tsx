'use client';

import { ArrowDown, ArrowUp, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { LeaguePickup } from '@/lib/types';

type SortKey = 'ppg' | 'pts';

interface WaiverCatalogProps {
  pickups: LeaguePickup[];
}

export function WaiverCatalog({ pickups }: WaiverCatalogProps) {
  const [teamFilter, setTeamFilter] = useState<string | null>(null);
  const [playerSearch, setPlayerSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('pts');
  const [sortAsc, setSortAsc] = useState(false);

  const allTeams = useMemo(() => {
    const names = new Set(pickups.map((p) => p.team));
    return [...names].sort();
  }, [pickups]);

  const filtered = useMemo(() => {
    let result = [...pickups];
    if (teamFilter) {
      result = result.filter((p) => p.team === teamFilter);
    }
    if (playerSearch.trim()) {
      const q = playerSearch.toLowerCase();
      result = result.filter((p) => p.player.toLowerCase().includes(q));
    }
    const dir = sortAsc ? -1 : 1;
    result.sort((a, b) =>
      sortBy === 'ppg'
        ? (b.ppg - a.ppg) * dir
        : (b.ptsAfterAdd - a.ptsAfterAdd) * dir,
    );
    return result;
  }, [pickups, teamFilter, playerSearch, sortBy, sortAsc]);

  if (pickups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="font-mono text-6xl md:text-8xl font-bold text-muted-foreground/20">0</p>
        <p className="font-mono text-lg text-muted-foreground mt-4">No waiver pickups this season</p>
      </div>
    );
  }

  const bestPickup = [...pickups].sort((a, b) => b.ptsAfterAdd - a.ptsAfterAdd)[0];
  const mostActiveTeam = getMostActive(pickups);

  return (
    <div className="space-y-8">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Total Pickups</p>
          <p className="font-mono text-5xl font-bold text-foreground">{pickups.length}</p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Best Pickup</p>
          <p className="font-mono text-lg font-bold text-win">{bestPickup.player}</p>
          <p className="font-mono text-xs text-muted-foreground mt-1">
            {bestPickup.ptsAfterAdd.toFixed(0)} pts &mdash; {bestPickup.team}
            {bestPickup.faabBid > 0 && <span className="text-gold ml-1">(${bestPickup.faabBid})</span>}
          </p>
        </div>
        <div className="hidden md:block">
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">Most Active</p>
          <p className="font-mono text-2xl font-bold text-foreground">{mostActiveTeam}</p>
        </div>
      </div>

      {/* Team Waiver Summary */}
      <div>
        <h3 className="font-mono text-sm font-bold text-foreground uppercase tracking-widest mb-4">
          Team Waiver Activity
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {(() => {
            const teamStats = new Map<string, { pickups: number; spent: number; pts: number }>();
            for (const p of pickups) {
              const prev = teamStats.get(p.team) || { pickups: 0, spent: 0, pts: 0 };
              teamStats.set(p.team, {
                pickups: prev.pickups + 1,
                spent: prev.spent + (p.faabBid || 0),
                pts: prev.pts + p.ptsAfterAdd,
              });
            }
            return [...teamStats.entries()]
              .sort((a, b) => b[1].spent - a[1].spent || b[1].pts - a[1].pts)
              .map(([team, stats]) => (
                <div key={team} className="border border-border/50 p-4 flex items-center justify-between">
                  <div>
                    <p className="font-mono text-sm font-bold text-foreground truncate max-w-[140px]">{team}</p>
                    <p className="font-mono text-xs text-muted-foreground mt-1">
                      {stats.pickups} pickups &middot; {stats.pts.toFixed(0)} pts
                    </p>
                  </div>
                  {stats.spent > 0 && (
                    <span className="font-mono text-xl font-bold text-gold">
                      ${stats.spent}
                    </span>
                  )}
                </div>
              ));
          })()}
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setTeamFilter(null)}
            className={`font-mono text-[10px] uppercase tracking-widest px-3 py-1.5 border transition-colors ${
              !teamFilter ? 'border-gold text-gold' : 'border-border/50 text-muted-foreground hover:text-foreground'
            }`}
          >
            All
          </button>
          {allTeams.map((team) => (
            <button
              type="button"
              key={team}
              onClick={() => setTeamFilter(teamFilter === team ? null : team)}
              className={`font-mono text-[10px] uppercase tracking-widest px-3 py-1.5 border transition-colors ${
                teamFilter === team ? 'border-gold text-gold' : 'border-border/50 text-muted-foreground hover:text-foreground'
              }`}
            >
              {team}
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
        <div className="flex gap-2">
          {(['ppg', 'pts'] as SortKey[]).map((key) => {
            const active = sortBy === key;
            return (
              <button
                type="button"
                key={key}
                onClick={() => {
                  if (active) {
                    setSortAsc((prev) => !prev);
                  } else {
                    setSortBy(key);
                    setSortAsc(false);
                  }
                }}
                className={`flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest px-2 py-1 border transition-colors ${
                  active ? 'border-foreground/30 text-foreground' : 'border-border/50 text-muted-foreground hover:text-foreground'
                }`}
              >
                {key === 'ppg' ? 'PPG' : 'Total Pts'}
                {active && (sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />)}
              </button>
            );
          })}
        </div>
      </div>

      {(teamFilter || playerSearch) && (
        <p className="font-mono text-xs text-muted-foreground">
          {filtered.length} of {pickups.length} pickups
        </p>
      )}

      {/* Pickup Table */}
      <div className="border border-border/50">
        {filtered.map((pickup, index) => (
          <div
            key={`${index}-${pickup.player}`}
            className="flex items-center gap-4 px-4 py-3 hover:bg-card/30 transition-colors border-b border-border/30 last:border-b-0"
          >
            <span className="font-mono text-xs text-muted-foreground w-8 text-right shrink-0">
              #{index + 1}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-mono text-sm font-bold text-foreground truncate">{pickup.player}</p>
              <p className="font-mono text-xs text-muted-foreground truncate">
                {pickup.team} &mdash; Week {pickup.weekAdded ?? '?'}
                {pickup.faabBid > 0 && (
                  <span className="text-gold ml-2">${pickup.faabBid}</span>
                )}
              </p>
            </div>
            <div className="text-right shrink-0">
              <p className="font-mono text-sm font-bold text-foreground">
                {sortBy === 'ppg' ? `${pickup.ppg} PPG` : `${pickup.ptsAfterAdd.toFixed(0)} pts`}
              </p>
              <p className="font-mono text-xs text-muted-foreground">
                {sortBy === 'ppg'
                  ? `${pickup.ptsAfterAdd.toFixed(0)} pts · ${pickup.gamesPlayed}G`
                  : `${pickup.ppg} PPG · ${pickup.gamesPlayed}G`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getMostActive(pickups: LeaguePickup[]): string {
  const counts: Record<string, number> = {};
  for (const p of pickups) {
    counts[p.team] = (counts[p.team] || 0) + 1;
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
