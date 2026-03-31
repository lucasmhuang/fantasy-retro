'use client';

import {
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Info,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useState } from 'react';
import { useScrollBatch } from '@/hooks/use-scroll-batch';
import { useChartTooltip } from '@/hooks/use-chart-tooltip';
import { AXIS_TICK, COLORS } from '@/lib/chart';
import { ChartTooltipPortal } from '@/components/ui/chart-tooltip-portal';
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { SectionHeader } from '@/components/wrapped/section-header';
import {
  Tooltip as InfoTooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { Trade } from '@/lib/types';

interface TradeCenterProps {
  trades: Trade[];
  replacementFPW?: number;
  nameMap?: Record<string, string>;
}

export function TradeCenter({ trades, replacementFPW, nameMap = {} }: TradeCenterProps) {
  const [expandedTrade, setExpandedTrade] = useState<number | null>(null);
  const { ref: batchRef } = useScrollBatch();
  const { pos: tooltipPos, onMouseMove: onChartMouseMove, isMobile } = useChartTooltip();

  const totalNet = trades.reduce((acc, t) => acc + t.net, 0);
  const isPositiveOverall = totalNet >= 0;

  if (trades.length === 0) {
    return (
      <section className="relative min-h-[60vh] px-6 py-24 md:px-12 lg:px-24 flex flex-col justify-center">
        <SectionHeader number="02" title="Trade Center" />

        <div className="flex flex-col items-center justify-center py-20">
          <p className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/20">
            0
          </p>
          <p className="font-mono text-lg text-muted-foreground mt-4">
            No trades made this season
          </p>
          <p className="font-mono text-sm text-muted-foreground/60 mt-2">
            Sometimes the best trade is no trade at all.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <SectionHeader
        number="02"
        title="Trade Center"
        description={<>{trades.length} deal{trades.length !== 1 ? 's' : ''} made. Did you buy low and sell high?</>}
      />

      {/* Overall Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-12">
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Trades Made
          </p>
          <p className="font-mono text-5xl font-bold text-foreground">
            {trades.length}
          </p>
        </div>
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Net Impact
          </p>
          <p
            className={`font-mono text-5xl font-bold ${isPositiveOverall ? 'text-win' : 'text-loss'}`}
          >
            {isPositiveOverall ? '+' : ''}
            {totalNet.toFixed(1)}
          </p>
        </div>
        <div className="hidden md:block">
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
            Verdict
          </p>
          <p
            className={`font-mono text-2xl font-bold ${isPositiveOverall ? 'text-win' : 'text-loss'}`}
          >
            {totalNet > 50 ? 'Trade Shark' : totalNet >= 0 ? 'Trade Winner' : totalNet > -50 ? 'Trade Loser' : 'Got Fleeced'}
          </p>
        </div>
      </div>

      {/* Trade Cards */}
      <div ref={batchRef} className="space-y-6">
        {trades.map((trade, index) => {
          const isExpanded = expandedTrade === index;
          const isPositive = trade.net >= 0;

          // Build cumulative net chart data
          const cumulativeData = trade.weeklyBreakdown.reduce(
            (acc, week) => {
              const prev = acc.length > 0 ? acc[acc.length - 1].cumulative : 0;
              const weekNet = week.receivedPts - week.sentPts;
              acc.push({
                week: week.week,
                cumulative: prev + weekNet,
                weekNet,
              });
              return acc;
            },
            [] as { week: number; cumulative: number; weekNet: number }[],
          );

          return (
            <div
              key={index}
              data-batch-item
              className={`border transition-all duration-300 ${
                isPositive
                  ? 'border-win/30 hover:border-win/50'
                  : 'border-loss/30 hover:border-loss/50'
              }`}
            >
              {/* Trade Header */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-1">
                      Week {trade.week ?? '?'} &mdash; with {nameMap[trade.partner] || trade.partner}
                    </p>
                    <div
                      className={`inline-flex items-center gap-2 font-mono text-2xl font-bold ${isPositive ? 'text-win' : 'text-loss'}`}
                    >
                      {isPositive ? (
                        <TrendingUp className="w-6 h-6" />
                      ) : (
                        <TrendingDown className="w-6 h-6" />
                      )}
                      {isPositive ? '+' : ''}
                      {trade.net.toFixed(1)} pts
                    </div>
                  </div>
                </div>

                {/* Trade Details */}
                <div className="flex flex-col md:flex-row items-stretch gap-4">
                  {/* Sent */}
                  <div className="flex-1 p-4 bg-loss/10 border border-loss/20">
                    <p className="font-mono text-xs text-loss uppercase tracking-widest mb-3">
                      Sent
                    </p>
                    <div className="space-y-2">
                      {(trade.sentStats || []).length > 0
                        ? trade.sentStats?.map((s) => (
                            <div
                              key={s.player}
                              className="flex items-baseline justify-between gap-2"
                            >
                              <p className="font-mono text-lg text-foreground truncate">
                                {s.player}
                              </p>
                              <p className="font-mono text-xs text-muted-foreground whitespace-nowrap">
                                {s.gamesROS}G &middot; {s.ppgROS} PPG
                              </p>
                            </div>
                          ))
                        : trade.sent.map((player, i) => (
                            <p
                              key={i}
                              className="font-mono text-lg text-foreground"
                            >
                              {player}
                            </p>
                          ))}
                    </div>
                    <p className="font-mono text-sm text-muted-foreground mt-4">
                      {trade.sentPtsROS.toFixed(1)} pts ROS
                    </p>
                    {trade.slotAdjustment &&
                    trade.received.length > trade.sent.length ? (
                      <InfoTooltip>
                        <TooltipTrigger asChild>
                          <span className="inline-flex items-center gap-1 font-mono text-xs text-muted-foreground/60 mt-1 cursor-help">
                            <Info className="w-3 h-3" />+
                            {trade.slotAdjustment.toFixed(1)} roster spot value
                          </span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p>
                            This trade was uneven — the freed roster spot is
                            valued at replacement-level production (~
                            {replacementFPW ?? '?'} fantasy points per week) for
                            the remaining weeks.
                          </p>
                        </TooltipContent>
                      </InfoTooltip>
                    ) : null}
                  </div>

                  {/* Arrow */}
                  <div className="hidden md:flex items-center justify-center px-4">
                    <ArrowRight className="w-6 h-6 text-muted-foreground" />
                  </div>

                  {/* Received */}
                  <div className="flex-1 p-4 bg-win/10 border border-win/20">
                    <p className="font-mono text-xs text-win uppercase tracking-widest mb-3">
                      Received
                    </p>
                    <div className="space-y-2">
                      {(trade.receivedStats || []).length > 0
                        ? trade.receivedStats?.map((s) => (
                            <div
                              key={s.player}
                              className="flex items-baseline justify-between gap-2"
                            >
                              <p className="font-mono text-lg text-foreground truncate">
                                {s.player}
                              </p>
                              <p className="font-mono text-xs text-muted-foreground whitespace-nowrap">
                                {s.gamesROS}G &middot; {s.ppgROS} PPG
                              </p>
                            </div>
                          ))
                        : trade.received.map((player, i) => (
                            <p
                              key={i}
                              className="font-mono text-lg text-foreground"
                            >
                              {player}
                            </p>
                          ))}
                    </div>
                    <p className="font-mono text-sm text-muted-foreground mt-4">
                      {trade.receivedPtsROS.toFixed(1)} pts ROS
                    </p>
                    {trade.slotAdjustment &&
                    trade.sent.length > trade.received.length ? (
                      <InfoTooltip>
                        <TooltipTrigger asChild>
                          <span className="inline-flex items-center gap-1 font-mono text-xs text-muted-foreground/60 mt-1 cursor-help">
                            <Info className="w-3 h-3" />+
                            {trade.slotAdjustment.toFixed(1)} roster spot value
                          </span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p>
                            This trade was uneven — the freed roster spot is
                            valued at replacement-level production (~
                            {replacementFPW ?? '?'} fantasy points per week) for
                            the remaining weeks.
                          </p>
                        </TooltipContent>
                      </InfoTooltip>
                    ) : null}
                  </div>
                </div>

                {/* Expand Button */}
                <button
                  onClick={() => setExpandedTrade(isExpanded ? null : index)}
                  className="flex items-center gap-2 mt-6 font-mono text-xs text-muted-foreground hover:text-foreground uppercase tracking-widest transition-colors"
                >
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                  {isExpanded ? 'Hide' : 'Show'} Breakdown
                </button>
              </div>

              {/* Expanded Chart */}
              {isExpanded && (
                <div className="px-6 pb-6 border-t border-border">
                  <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mt-6 mb-4">
                    Cumulative Net Impact
                  </p>
                  <div className="h-[150px] md:h-[200px]" onMouseMove={onChartMouseMove}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={cumulativeData}>
                        <XAxis
                          dataKey="week"
                          axisLine={false}
                          tickLine={false}
                          tick={AXIS_TICK}
                          tickFormatter={(value) => `W${value}`}
                        />
                        <YAxis
                          axisLine={false}
                          tickLine={false}
                          tick={AXIS_TICK}
                        />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (!active || !payload || !payload[0]) return null;
                            const data = payload[0].payload;
                            return (
                              <ChartTooltipPortal active pos={tooltipPos} isMobile={isMobile}>
                                <p className="font-mono text-xs text-muted-foreground mb-1">
                                  Week {data.week}
                                </p>
                                <p
                                  className={`font-mono text-lg font-bold ${data.cumulative >= 0 ? 'text-win' : 'text-loss'}`}
                                >
                                  {data.cumulative >= 0 ? '+' : ''}
                                  {data.cumulative.toFixed(1)}
                                </p>
                                <p className="font-mono text-xs text-muted-foreground mt-1">
                                  Week net: {data.weekNet >= 0 ? '+' : ''}
                                  {data.weekNet.toFixed(1)}
                                </p>
                              </ChartTooltipPortal>
                            );
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="cumulative"
                          stroke={isPositive ? COLORS.win : COLORS.loss}
                          strokeWidth={2}
                          dot={{ fill: isPositive ? COLORS.win : COLORS.loss, r: 3 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
