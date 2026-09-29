'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * 卡片三态的统一呈现。只承载「加载中 / 失败 / 空」的可见文本与 aria 语义，
 * 不参与数据获取，因此每张卡片可独立使用而互不影响。
 */
export type CardState = 'loading' | 'error' | 'empty' | 'ready';

/** 由查询状态与「成功但结果为空」推导出卡片状态。 */
export function toCardState(opts: {
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
}): CardState {
  if (opts.isLoading) return 'loading';
  if (opts.isError) return 'error';
  if (opts.isEmpty) return 'empty';
  return 'ready';
}

/** 多查询复合卡片：任一加载即加载，任一失败即失败，其后才看空态。 */
export function toCompositeCardState(
  parts: Array<{ isLoading: boolean; isError: boolean }>,
  isEmpty: boolean,
): CardState {
  if (parts.some((p) => p.isLoading)) return 'loading';
  if (parts.some((p) => p.isError)) return 'error';
  return isEmpty ? 'empty' : 'ready';
}

export function CardStateNotice({
  state,
  loadingText = '加载中…',
  errorText = '加载失败，请稍后重试',
  emptyText = '暂无数据',
  className,
}: {
  state: CardState;
  loadingText?: string;
  errorText?: string;
  emptyText?: string;
  className?: string;
}) {
  if (state === 'ready') return null;

  const text = state === 'loading' ? loadingText : state === 'error' ? errorText : emptyText;
  const role = state === 'error' ? 'alert' : state === 'loading' ? 'status' : undefined;

  return (
    <div
      aria-busy={state === 'loading' || undefined}
      className={cn(
        'flex min-h-24 items-center justify-center px-4 py-6 text-center text-muted-foreground text-sm',
        state === 'error' && 'text-rose-600 dark:text-rose-400',
        className,
      )}
      data-state={state}
      role={role}
    >
      {text}
    </div>
  );
}

/** 包裹卡片内容：三态时渲染提示，就绪时渲染 children。 */
export function CardStateGate({
  state,
  children,
  loadingText,
  errorText,
  emptyText,
  className,
}: {
  state: CardState;
  children: ReactNode;
  loadingText?: string;
  errorText?: string;
  emptyText?: string;
  className?: string;
}) {
  if (state !== 'ready') {
    return (
      <CardStateNotice
        className={className}
        emptyText={emptyText}
        errorText={errorText}
        loadingText={loadingText}
        state={state}
      />
    );
  }
  return <>{children}</>;
}
