// 番剧索引页：筛选栏结构照生产 AnimeIndex.tsx，数据全假。
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AnimeCard } from './AnimeCard';
import { ALL, WEEKDAYS, YEARS } from './data';
import type { Anime } from './data';

export type Filters = {
  keyword: string;
  year: string;
  weekday: string;
  sort: string;
  order: string;
};

export function AnimeIndexPage({
  filters,
  items,
  onFiltersChange,
  highlightIds,
}: {
  filters: Filters;
  items: Anime[];
  onFiltersChange: (f: Filters) => void;
  highlightIds: number[];
}) {
  const set = (patch: Partial<Filters>) => onFiltersChange({ ...filters, ...patch });

  return (
    <div className="mx-auto w-full max-w-[1400px] p-6">
      <h1 className="mb-4 text-2xl font-semibold">番剧索引</h1>

      <div className="mb-5 flex flex-wrap gap-3 rounded-xl border bg-card p-4">
        <div className="flex gap-2">
          <Input
            aria-label="关键词"
            placeholder="关键词"
            value={filters.keyword}
            onChange={(e) => set({ keyword: e.target.value })}
            className="w-[200px]"
          />
          <Button variant="outline">搜索</Button>
        </div>

        <Select value={filters.year} onValueChange={(v) => set({ year: v })}>
          <SelectTrigger className="w-[110px]" aria-label="年份">
            <SelectValue placeholder="年份" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部年份</SelectItem>
            {YEARS.map((y) => (
              <SelectItem key={y} value={y}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filters.weekday} onValueChange={(v) => set({ weekday: v })}>
          <SelectTrigger className="w-[110px]" aria-label="播出星期">
            <SelectValue placeholder="播出星期" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部星期</SelectItem>
            {WEEKDAYS.map((w, i) => (
              <SelectItem key={w} value={String(i)}>
                {w}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filters.sort} onValueChange={(v) => set({ sort: v })}>
          <SelectTrigger className="w-[110px]" aria-label="排序">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="score">评分</SelectItem>
            <SelectItem value="air_date">播出日期</SelectItem>
            <SelectItem value="rank">排名</SelectItem>
            <SelectItem value="collection_total">收藏数</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.order} onValueChange={(v) => set({ order: v })}>
          <SelectTrigger className="w-[90px]" aria-label="方向">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">降序</SelectItem>
            <SelectItem value="asc">升序</SelectItem>
          </SelectContent>
        </Select>

        <Button variant="outline" onClick={() => onFiltersChange({ keyword: '', year: ALL, weekday: ALL, sort: 'score', order: 'desc' })}>
          重置
        </Button>
      </div>

      <div className="mb-3 text-sm text-muted-foreground">共 {items.length} 部作品</div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-5">
        {items.map((a) => (
          <AnimeCard key={a.id} anime={a} highlight={highlightIds.includes(a.id)} />
        ))}
      </div>
      {items.length === 0 && <p className="py-12 text-center text-sm text-muted-foreground">没有符合筛选条件的番剧</p>}
    </div>
  );
}
