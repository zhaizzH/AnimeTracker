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

/** 收藏类型枚举 1–5；未知值保留原值以免隐藏服务端新增类型。 */
const TYPE_LABELS: Record<number, string> = {
  1: '想看',
  2: '看过',
  3: '在看',
  4: '搁置',
  5: '抛弃',
};

export function TrafficSourcesChart({
  types,
  isLoading,
  isError,
}: {
  types: CollectionStatsVO['types'] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const rows = types ?? [];
  const max = rows.reduce((m, r) => Math.max(m, r.count), 0);
  const state = toCardState({ isLoading, isError, isEmpty: rows.length === 0 });

  return (
    <Card className="dark:bg-transparent">
      <CardHeader className="border-b">
        <CardTitle className="text-balance">收藏类型分布</CardTitle>
        <CardDescription className="text-pretty">用户收藏记录按类型统计</CardDescription>
      </CardHeader>
      <CardContent aria-busy={state === 'loading' || undefined} className="p-0 py-1">
        <CardStateGate emptyText="暂无收藏记录" loadingText="收藏类型加载中…" state={state}>
          <ShareBarList aria-label="按收藏类型统计的记录数">
            {rows.map((row) => (
              <ShareBarListItem
                key={row.type}
                value={max > 0 ? (row.count / max) * 100 : 0}
              >
                <ShareBarListContent>
                  <ShareBarListLabel>{TYPE_LABELS[row.type] ?? `类型 ${row.type}`}</ShareBarListLabel>
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
