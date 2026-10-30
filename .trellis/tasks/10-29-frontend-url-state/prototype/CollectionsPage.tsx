// 我的收藏页：tab 行结构照生产 MyCollections.tsx。
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { AnimeCard } from './AnimeCard';
import { TABS } from './data';
import type { Anime } from './data';

export function CollectionsPage({
  tab,
  items,
  counts,
  onTabChange,
  highlightIds,
}: {
  tab: string;
  items: Anime[];
  counts: Record<string, number>;
  onTabChange: (t: string) => void;
  highlightIds: number[];
}) {

  return (
    <div className="mx-auto w-full max-w-[1400px] p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b">
        <div role="tablist" aria-label="收藏分类" className="flex flex-wrap gap-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={tab === t.key}
              className={cn(
                '-mb-px border-b-2 px-4 py-2 text-sm',
                tab === t.key ? 'border-primary font-medium text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
              onClick={() => onTabChange(t.key)}
            >
              {t.label}({counts[t.key] ?? 0})
            </button>
          ))}
        </div>
        <Button>更新本周进度</Button>
      </div>

      {items.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground">还没有收藏，去番剧索引逛逛</p>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-5">
          {items.map((a) => (
            <AnimeCard key={a.id} anime={a} highlight={highlightIds.includes(a.id)} />
          ))}
        </div>
      )}
    </div>
  );
}
