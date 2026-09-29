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
  ShareBarList,
  ShareBarListContent,
  ShareBarListFill,
  ShareBarListItem,
  ShareBarListLabel,
  ShareBarListValue,
} from '@/components/share-bar-list';
import { formatInteger } from '@/lib/formater';
import { CardStateGate, toCardState } from './card-state';

export function BrowserShare({
  scoreCounts,
  isLoading,
  isError,
}: {
  scoreCounts: SubjectStatsVO['scoreCounts'] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const rows = scoreCounts ?? [];
  const max = rows.reduce((m, r) => Math.max(m, r.count), 0);
  const state = toCardState({ isLoading, isError, isEmpty: rows.length === 0 });

  return (
    <Card className="dark:bg-transparent">
      <CardHeader className="border-b">
        <CardTitle className="text-balance">番剧自身评分分布</CardTitle>
        <CardDescription className="text-pretty">
          番剧条目的评分按整数分档统计（与用户收藏评分为不同口径）
        </CardDescription>
      </CardHeader>
      <CardContent aria-busy={state === 'loading' || undefined} className="p-0 py-1">
        <CardStateGate emptyText="暂无评分数据" loadingText="番剧评分加载中…" state={state}>
          <ShareBarList aria-label="番剧自身评分分档条目数">
            {rows.map((row) => (
              <ShareBarListItem key={row.rate} value={max > 0 ? (row.count / max) * 100 : 0}>
                <ShareBarListContent>
                  <ShareBarListLabel>{row.rate} 分</ShareBarListLabel>
                  <ShareBarListValue>{formatInteger(row.count)}</ShareBarListValue>
                </ShareBarListContent>
                <ShareBarListFill />
              </ShareBarListItem>
            ))}
          </ShareBarList>
        </CardStateGate>
      </CardContent>
    </Card>
  );
}
