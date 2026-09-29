'use client';

import type { SubjectStatsVO } from '@shared';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatInteger } from '@/lib/formater';
import { CardStateGate, toCardState } from './card-state';

/** 番剧条目导入状态：0 待导入、1 已导入；未知值保留原值。 */
const STATUS_LABELS: Record<number, string> = {
  0: '待导入',
  1: '已导入',
};

export function TopReferrers({
  importStatuses,
  isLoading,
  isError,
}: {
  importStatuses: SubjectStatsVO['importStatuses'] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const rows = importStatuses ?? [];
  const state = toCardState({ isLoading, isError, isEmpty: rows.length === 0 });

  return (
    <Card className="relative dark:bg-transparent">
      <CardHeader>
        <CardTitle className="text-balance">番剧导入状态分布</CardTitle>
        <CardDescription className="text-pretty">番剧条目按导入状态统计的条目数</CardDescription>
      </CardHeader>
      <CardContent
        aria-busy={state === 'loading' || undefined}
        className="mask-b-from-50% mask-b-to-100% p-0 pb-2"
      >
        <CardStateGate emptyText="暂无导入状态数据" loadingText="导入状态加载中…" state={state}>
          <Table className="border-t">
            <TableCaption className="sr-only">番剧条目按导入状态的分布。</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6" scope="col">
                  状态
                </TableHead>
                <TableHead className="pr-6 text-end tabular-nums" scope="col">
                  条目数
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow className="hover:bg-transparent" key={row.importStatus}>
                  <TableCell className="pl-6 font-medium">
                    <span className="text-xs">
                      {STATUS_LABELS[row.importStatus] ?? `状态 ${row.importStatus}`}
                    </span>
                  </TableCell>
                  <TableCell className="pr-6 text-end text-muted-foreground text-xs tabular-nums">
                    {formatInteger(row.count)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardStateGate>
      </CardContent>
    </Card>
  );
}
