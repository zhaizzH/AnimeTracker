import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * 标签胶囊样式，与 client `components/TagChip.tsx` 逐字节保持一致
 * （ADR 0021：装饰件各端自持，允许重复，不因“两端相同”上提 shared）。
 * 管理端只在番剧列表的标签筛选中使用，避免两端视觉漂移。
 */
export function tagChipClass(selected: boolean, className?: string) {
  return cn(
    'rounded-full border px-3 py-1 text-xs',
    selected ? 'border-primary bg-primary text-primary-foreground' : 'hover:bg-accent',
    className,
  );
}

export function TagChip({
  children,
  selected = false,
  className,
  ...props
}: {
  children: ReactNode;
  selected?: boolean;
  className?: string;
} & React.ComponentProps<'button'>) {
  return (
    <button type="button" aria-pressed={selected} className={tagChipClass(selected, className)} {...props}>
      {children}
    </button>
  );
}
