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

export function TopCountries({
  seasons,
  isLoading,
  isError,
}: {
  seasons: SubjectStatsVO['seasons'] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const rows = seasons ?? [];
  const state = toCardState({ isLoading, isError, isEmpty: rows.length === 0 });

  return (
    <Card className="relative md:col-span-2 dark:bg-transparent">
      <CardHeader>
        <CardTitle className="text-balance">播出季度分布</CardTitle>
        <CardDescription className="text-pretty">各季度番剧条目数量</CardDescription>
      </CardHeader>
      <CardContent
        aria-busy={state === 'loading' || undefined}
        className="mask-b-from-50% mask-b-to-100% p-0 pb-2"
      >
        <CardStateGate emptyText="暂无季度数据" loadingText="季度分布加载中…" state={state}>
          <Table className="border-t">
            <TableCaption className="sr-only">按季度统计的番剧条目数量。</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6" scope="col">
                  季度
                </TableHead>
                <TableHead className="pr-6 text-end tabular-nums" scope="col">
                  条目数
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow className="hover:bg-transparent" key={row.seasonKey}>
                  <TableCell className="pl-6 font-medium">
                    <span className="text-xs">{row.seasonKey}</span>
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
