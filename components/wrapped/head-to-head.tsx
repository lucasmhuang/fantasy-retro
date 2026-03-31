'use client';

import { Crosshair, Target } from 'lucide-react';
import { SectionHeader } from '@/components/wrapped/section-header';
import { resolveDisplayName } from '@/lib/team-colors';
import { useScrollBatch } from '@/hooks/use-scroll-batch';
import type { HeadToHeadRecord } from '@/lib/types';

interface HeadToHeadProps {
  records: HeadToHeadRecord[];
  nameMap?: Record<string, string>;
}

function totalWins(r: HeadToHeadRecord) {
  return r.wins + (r.playoffWins || 0);
}

function totalLosses(r: HeadToHeadRecord) {
  return r.losses + (r.playoffLosses || 0);
}

function hasPlayoff(r: HeadToHeadRecord) {
  return (r.playoffWins || 0) + (r.playoffLosses || 0) > 0;
}

export function HeadToHead({ records, nameMap = {} }: HeadToHeadProps) {
  const n = resolveDisplayName(nameMap);
  const { ref: batchRef } = useScrollBatch({ childSelector: '[data-batch-item]' });
  const rival = records.reduce((worst, r) =>
    totalLosses(r) > totalLosses(worst) ||
    (totalLosses(r) === totalLosses(worst) && r.avgMargin < worst.avgMargin)
      ? r
      : worst,
  );

  const punchingBag = records.reduce((best, r) =>
    totalWins(r) > totalWins(best) ||
    (totalWins(r) === totalWins(best) && r.avgMargin > best.avgMargin)
      ? r
      : best,
  );

  const sortedRecords = [...records].sort((a, b) => {
    const aTotalW = totalWins(a);
    const aTotalL = totalLosses(a);
    const bTotalW = totalWins(b);
    const bTotalL = totalLosses(b);
    const aWinPct = aTotalW / (aTotalW + aTotalL);
    const bWinPct = bTotalW / (bTotalW + bTotalL);
    if (bWinPct !== aWinPct) return bWinPct - aWinPct;
    return b.avgMargin - a.avgMargin;
  });

  const getBadge = (record: HeadToHeadRecord) => {
    const w = totalWins(record);
    const l = totalLosses(record);
    if (w > 0 && l === 0) return 'SWEPT';
    if (l > 0 && w === 0) return 'GOT SWEPT';
    if (w === l) return 'SPLIT';
    return null;
  };

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <SectionHeader
        number="10"
        title="Head-to-Head"
        description="Every matchup tells a story. Here's yours."
      />

      {/* Rival & Punching Bag Cards */}
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        {/* Rival */}
        <div className="p-6 border border-loss/50 bg-loss/5">
          <div className="flex items-center gap-3 mb-4">
            <Crosshair className="w-6 h-6 text-loss" />
            <p className="font-mono text-xs text-loss uppercase tracking-widest">
              Your Rival
            </p>
          </div>
          <p className="font-mono text-2xl md:text-3xl font-bold text-foreground mb-2">
            {n(rival.opponent)}
          </p>
          <p className="font-mono text-4xl font-bold text-loss">
            {totalWins(rival)}-{totalLosses(rival)}
          </p>
          {hasPlayoff(rival) && (
            <p className="font-mono text-xs text-muted-foreground mt-1">
              Reg {rival.wins}-{rival.losses} &middot; Playoffs{' '}
              {rival.playoffWins || 0}-{rival.playoffLosses || 0}
            </p>
          )}
          <p className="font-mono text-sm text-muted-foreground mt-2">
            Avg margin: {rival.avgMargin > 0 ? '+' : ''}
            {rival.avgMargin.toFixed(1)}
          </p>
        </div>

        {/* Punching Bag */}
        <div className="p-6 border border-win/50 bg-win/5">
          <div className="flex items-center gap-3 mb-4">
            <Target className="w-6 h-6 text-win" />
            <p className="font-mono text-xs text-win uppercase tracking-widest">
              Punching Bag
            </p>
          </div>
          <p className="font-mono text-2xl md:text-3xl font-bold text-foreground mb-2">
            {n(punchingBag.opponent)}
          </p>
          <p className="font-mono text-4xl font-bold text-win">
            {totalWins(punchingBag)}-{totalLosses(punchingBag)}
          </p>
          {hasPlayoff(punchingBag) && (
            <p className="font-mono text-xs text-muted-foreground mt-1">
              Reg {punchingBag.wins}-{punchingBag.losses} &middot; Playoffs{' '}
              {punchingBag.playoffWins || 0}-{punchingBag.playoffLosses || 0}
            </p>
          )}
          <p className="font-mono text-sm text-muted-foreground mt-2">
            Avg margin: {punchingBag.avgMargin > 0 ? '+' : ''}
            {punchingBag.avgMargin.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Full Table */}
      <div ref={batchRef} className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-4 font-mono text-xs text-muted-foreground uppercase tracking-widest">
                Opponent
              </th>
              <th className="text-center py-4 font-mono text-xs text-muted-foreground uppercase tracking-widest">
                Record
              </th>
              <th className="text-center py-4 font-mono text-xs text-muted-foreground uppercase tracking-widest">
                Avg Margin
              </th>
              <th className="text-right py-4 font-mono text-xs text-muted-foreground uppercase tracking-widest">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedRecords.map((record) => {
              const badge = getBadge(record);
              const tw = totalWins(record);
              const tl = totalLosses(record);
              const winPct = tw / (tw + tl);
              const isPositive = record.avgMargin >= 0;
              const playoff = hasPlayoff(record);

              return (
                <tr
                  key={n(record.opponent)}
                  data-batch-item
                  className="border-b border-border/50 hover:bg-card/50 transition-colors"
                >
                  <td className="py-4">
                    <p className="font-mono text-lg text-foreground">
                      {n(record.opponent)}
                    </p>
                  </td>
                  <td className="py-4 text-center">
                    <span
                      className={`font-mono text-xl font-bold ${
                        winPct > 0.5
                          ? 'text-win'
                          : winPct < 0.5
                            ? 'text-loss'
                            : 'text-foreground'
                      }`}
                    >
                      {tw}-{tl}
                    </span>
                    {playoff && (
                      <span className="block font-mono text-xs text-muted-foreground mt-0.5">
                        Reg {record.wins}-{record.losses}
                      </span>
                    )}
                  </td>
                  <td className="py-4 text-center">
                    <span
                      className={`font-mono text-lg font-bold ${isPositive ? 'text-win' : 'text-loss'}`}
                    >
                      {isPositive ? '+' : ''}
                      {record.avgMargin.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-4 text-right space-x-1">
                    {playoff && (
                      <span className="inline-block px-2 py-1 font-mono text-xs font-bold uppercase tracking-widest bg-gold/20 text-gold">
                        Playoffs {record.playoffWins || 0}-
                        {record.playoffLosses || 0}
                      </span>
                    )}
                    {badge && (
                      <span
                        className={`inline-block px-2 py-1 font-mono text-xs font-bold uppercase tracking-widest ${
                          badge === 'SWEPT'
                            ? 'bg-win text-background'
                            : badge === 'GOT SWEPT'
                              ? 'bg-loss text-background'
                              : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {badge}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
