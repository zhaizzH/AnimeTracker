import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * 标签胶囊的全站统一样式。
 * 索引页与详情页共用同一份，避免两处各写一套 class 后逐渐漂移。
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
