'use client';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CardStateGate, type CardState } from './card-state';

export function WebVitals({
  importCount,
  importSucceeded,
  importFailed,
  state,
}: {
  importCount: number | undefined;
  importSucceeded: number | undefined;
  importFailed: number | undefined;
  state: CardState;
}) {
  const rows = [
    { label: '导入记录总数', value: importCount },
    { label: '成功', value: importSucceeded },
    { label: '失败', value: importFailed },
  ];

  return (
    <Card className="md:col-span-2 lg:col-span-4 dark:bg-transparent">
      <CardHeader className="border-b">
        <CardTitle className="text-balance">导入记录</CardTitle>
        <CardDescription className="text-pretty">
          导入任务记录的总数、成功数与失败数
        </CardDescription>
      </CardHeader>
      <CardContent aria-busy={state === 'loading' || undefined}>
        <CardStateGate loadingText="导入记录加载中…" state={state}>
          <ul className="grid gap-6 sm:grid-cols-3">
            {rows.map((row) => (
              <li className="flex flex-col gap-1" key={row.label}>
                <p className="text-muted-foreground text-sm">{row.label}</p>
                <p className="font-semibold text-2xl tabular-nums">{row.value ?? 0}</p>
              </li>
            ))}
          </ul>
        </CardStateGate>
      </CardContent>
    </Card>
  );
}
