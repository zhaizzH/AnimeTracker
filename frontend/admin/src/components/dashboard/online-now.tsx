'use client';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CardStateGate, toCardState } from './card-state';

type TodayMetric = {
  label: string;
  hint: string;
  value: number | undefined;
};

export function OnlineNow({
  todayNewUsers,
  todayNewCollections,
  todayLogins,
  isLoading,
  isError,
}: {
  todayNewUsers: number | undefined;
  todayNewCollections: number | undefined;
  todayLogins: number | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const metrics: TodayMetric[] = [
    { label: '新增用户', hint: '今日注册', value: todayNewUsers },
    { label: '新增收藏', hint: '今日添加', value: todayNewCollections },
    { label: '登录次数', hint: '今日成功登录', value: todayLogins },
  ];

  const state = toCardState({ isLoading, isError, isEmpty: false });

  return (
    <Card className="gap-0 pb-0 md:col-span-2 lg:col-span-1 dark:bg-transparent">
      <CardHeader className="border-b">
        <CardTitle className="text-balance">今日运营</CardTitle>
        <CardDescription className="text-pretty">今日新增与登录人次统计</CardDescription>
      </CardHeader>
      <CardContent
        aria-busy={state === 'loading' || undefined}
        className="flex h-full flex-col justify-center gap-3 py-3"
      >
        <CardStateGate loadingText="今日数据加载中…" state={state}>
          <dl className="flex flex-col gap-3">
            {metrics.map((m) => (
              <div className="flex items-baseline justify-between gap-2" key={m.label}>
                <dt className="text-muted-foreground text-sm">
                  {m.label}
                  <span className="sr-only">（{m.hint}）</span>
                </dt>
                <dd className="font-mono font-semibold text-2xl tabular-nums">
                  {m.value ?? 0}
                </dd>
              </div>
            ))}
          </dl>
        </CardStateGate>
      </CardContent>
    </Card>
  );
}
