'use client';

import type { HotItemVO } from '@shared';
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
import { CardStateGate, toCardState } from './card-state';

export function TopPages({
  items,
  isLoading,
  isError,
}: {
  items: HotItemVO[] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const rows = items ?? [];
  const state = toCardState({ isLoading, isError, isEmpty: rows.length === 0 });

  return (
    <Card className="relative md:col-span-2 dark:bg-transparent">
      <CardHeader>
        <CardTitle className="text-balance">热门番剧</CardTitle>
        <CardDescription className="text-pretty">按收藏数排序的前 10 部番剧</CardDescription>
      </CardHeader>
      <CardContent
        aria-busy={state === 'loading' || undefined}
        className="mask-b-from-50% mask-b-to-100% p-0 pb-2"
      >
        <CardStateGate emptyText="暂无收藏数据" loadingText="热门番剧加载中…" state={state}>
          <Table className="border-t">
            <TableCaption className="sr-only">按收藏数排序的热门番剧列表。</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6" scope="col">
                  番剧
                </TableHead>
                <TableHead className="pr-6 text-end tabular-nums" scope="col">
                  收藏数
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow className="hover:bg-transparent" key={row.id}>
                  <TableCell className="max-w-[220px] truncate pl-6 font-medium">
                    <span className="text-xs">{row.nameCn ?? row.name}</span>
                  </TableCell>
                  <TableCell className="pr-6 text-end text-muted-foreground text-xs tabular-nums">
                    {row.collectionCount}
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
