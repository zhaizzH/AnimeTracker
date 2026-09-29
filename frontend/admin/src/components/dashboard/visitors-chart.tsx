'use client';

import { useId } from 'react';
import { Area, AreaChart, CartesianGrid, XAxis } from 'recharts';
import type { TrendPointVO } from '@shared';
import { formatChartAxisTick, formatChartTooltipDate } from '@/lib/formater';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import { CardStateGate, toCardState } from './card-state';

const PERIODS = [7, 30, 90] as const;

const chartConfig = {
  newUsers: { label: '新增用户', color: 'var(--chart-1)' },
  newCollections: { label: '新增收藏', color: 'var(--chart-2)' },
  logins: { label: '登录次数', color: 'var(--chart-3)' },
} satisfies ChartConfig;

export function VisitorsChart({
  days,
  onDaysChange,
  points,
  isLoading,
  isError,
}: {
  days: number;
  onDaysChange: (days: number) => void;
  points: TrendPointVO[] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const titleId = `trend-title-${useId().replace(/:/g, '')}`;
  const rows = (points ?? []).map((p) => ({ ...p, tick: formatChartAxisTick(p.date, days) }));
  const state = toCardState({
    isLoading,
    isError,
    isEmpty: (points?.length ?? 0) === 0,
  });

  return (
    <Card className="md:col-span-2 lg:col-span-3 dark:bg-transparent">
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-1.5">
          <CardTitle className="text-balance">新增趋势</CardTitle>
          <CardDescription className="text-pretty">
            近 {days} 天的新增用户、新增收藏与登录次数
          </CardDescription>
        </div>
        <div aria-label="趋势周期" className="flex gap-1" role="group">
          {PERIODS.map((p) => (
            <Button
              aria-pressed={p === days}
              key={p}
              onClick={() => onDaysChange(p)}
              size="sm"
              type="button"
              variant={p === days ? 'default' : 'outline'}
            >
              {p} 天
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent aria-busy={state === 'loading' || undefined} aria-labelledby={titleId}>
        <span className="sr-only" id={titleId}>
          趋势图
        </span>
        <CardStateGate
          emptyText={`近 ${days} 天暂无新增数据`}
          loadingText="趋势加载中…"
          state={state}
        >
          <ChartContainer className="aspect-auto h-60 w-full" config={chartConfig}>
            <AreaChart accessibilityLayer data={rows} margin={{ left: 12, right: 12 }}>
              <CartesianGrid vertical={false} />
              <XAxis
                axisLine={false}
                dataKey="tick"
                tickFormatter={(value) => String(value)}
                tickLine={false}
                tickMargin={8}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    indicator="dashed"
                    labelFormatter={(_label, payload) => {
                      const date = payload?.[0]?.payload?.date;
                      return typeof date === 'string' ? formatChartTooltipDate(date) : String(_label);
                    }}
                  />
                }
                wrapperStyle={{ outline: 'none' }}
              />
              <ChartLegend content={<ChartLegendContent />} />
              {(['newUsers', 'newCollections', 'logins'] as const).map((key) => (
                <Area
                  dataKey={key}
                  dot={{ r: 2, strokeWidth: 2 }}
                  fill={`var(--color-${key})`}
                  fillOpacity={0.15}
                  isAnimationActive={false}
                  key={key}
                  name={chartConfig[key].label}
                  stroke={`var(--color-${key})`}
                  strokeWidth={2}
                  type="linear"
                />
              ))}
            </AreaChart>
          </ChartContainer>
        </CardStateGate>
      </CardContent>
    </Card>
  );
}
