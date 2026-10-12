import { SubjectCard } from '@shared';
import type { SubjectListItem } from '@shared';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

interface Props {
  items: SubjectListItem[]; loading?: boolean; emptyText?: string;
  total?: number; page?: number; size?: number;
  onPageChange?: (page: number) => void;
}

export function SubjectGrid({ items, loading, emptyText = '暂无数据', total, page, size, onPageChange }: Props) {
  if (loading) {
    // 卡片形状骨架：与加载后布局一致，消除「窄→宽」跳动
    const count = size && size > 0 ? Math.min(size, 12) : 12;
    return (
      <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-5">
        {Array.from({ length: count }, (_, i) => (
          <div key={i} className="rounded-xl border bg-card p-2.5" aria-hidden>
            <Skeleton className="aspect-[3/4] w-full rounded-lg" />
            <Skeleton className="mt-2 h-4 w-4/5" />
            <Skeleton className="mt-1 h-3 w-1/2" />
          </div>
        ))}
      </div>
    );
  }
  if (!items.length) return <p className="py-12 text-center text-sm text-muted-foreground">{emptyText}</p>;
  const pages = total && size ? Math.max(1, Math.ceil(total / size)) : 1;
  const current = page ?? 1;
  return (
    <div>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-5">
        {items.map((s) => (
          <div key={s.id} className="rounded-xl border bg-card p-2.5 transition hover:-translate-y-1 hover:border-ring">
            <SubjectCard subject={s} />
          </div>
        ))}
      </div>
      {onPageChange && pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button variant="outline" size="sm" disabled={current <= 1} onClick={() => onPageChange(current - 1)}>上一页</Button>
          <span className="text-sm text-muted-foreground">{current} / {pages}</span>
          <Button variant="outline" size="sm" disabled={current >= pages} onClick={() => onPageChange(current + 1)}>下一页</Button>
        </div>
      )}
    </div>
  );
}
