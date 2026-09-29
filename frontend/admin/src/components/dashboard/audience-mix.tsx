'use client';

import type { CollectionStatsVO } from '@shared';
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

export function AudienceMix({
  ratings,
  isLoading,
  isError,
}: {
  ratings: CollectionStatsVO['ratings'] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const rows = ratings ?? [];
  const max = rows.reduce((m, r) => Math.max(m, r.count), 0);
  const state = toCardState({ isLoading, isError, isEmpty: rows.length === 0 });

  return (
    <Card className="dark:bg-transparent">
      <CardHeader className="border-b">
        <CardTitle className="text-balance">用户收藏评分分布</CardTitle>
        <CardDescription className="text-pretty">
          用户为收藏条目打出的评分档（仅统计已评分记录）
        </CardDescription>
      </CardHeader>
      <CardContent aria-busy={state === 'loading' || undefined} className="p-0 py-1">
        <CardStateGate emptyText="暂无评分记录" loadingText="用户评分加载中…" state={state}>
          <ShareBarList aria-label="用户收藏评分档记录数">
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
