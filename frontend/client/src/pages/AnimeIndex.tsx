import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { subjectsApi, tagsApi } from '@shared';
import { SubjectGrid } from '@/components/SubjectGrid';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const SORTS = [
  { value: 'score', label: '评分' },
  { value: 'air_date', label: '播出日期' },
  { value: 'rank', label: '排名' },
  { value: 'collection_total', label: '收藏数' },
];
const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
const ALL = '__all__';

export default function AnimeIndex() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const [keyword, setKeyword] = useState(q);
  const [filters, setFilters] = useState<{ sort?: string; order?: 'asc' | 'desc'; year?: number; weekday?: number; tag?: string[] }>({ sort: 'score', order: 'desc' });
  const page = Number(params.get('page') ?? 1);

  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list });
  const { data: years } = useQuery({ queryKey: ['subjects', 'years'], queryFn: subjectsApi.years });
  const { data, isLoading } = useQuery({
    queryKey: ['subjects', 'search', q, filters, page],
    queryFn: () => subjectsApi.search({ q, page, size: 24, sort: 'score', order: 'desc', ...filters }),
  });

  const applyFilters = (patch: Partial<typeof filters>) => {
    setFilters((f) => ({ ...f, ...patch }));
    setParams(q ? { q } : {});
  };
  const reset = () => {
    setFilters({ sort: 'score', order: 'desc' });
    setKeyword('');
    setParams({});
  };

  return (
    <div className="mx-auto w-full max-w-[1400px] p-6">
      <h1 className="mb-4 text-2xl font-semibold">番剧索引</h1>
      <div className="mb-5 flex flex-wrap gap-3 rounded-xl border bg-card p-4">
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            setParams(keyword ? { q: keyword, page: '1' } : { page: '1' });
          }}
        >
          <Input
            aria-label="关键词"
            placeholder="关键词"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="w-[200px]"
          />
          <Button type="submit" variant="outline">搜索</Button>
        </form>

        <Select value={filters.year != null ? String(filters.year) : ALL} onValueChange={(v) => applyFilters({ year: v === ALL ? undefined : Number(v) })}>
          <SelectTrigger className="w-[110px]" aria-label="年份"><SelectValue placeholder="年份" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部年份</SelectItem>
            {(years ?? []).map((y) => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={filters.weekday != null ? String(filters.weekday) : ALL} onValueChange={(v) => applyFilters({ weekday: v === ALL ? undefined : Number(v) })}>
          <SelectTrigger className="w-[110px]" aria-label="播出星期"><SelectValue placeholder="播出星期" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部星期</SelectItem>
            {WEEKDAYS.map((label, i) => <SelectItem key={i} value={String(i)}>{label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={filters.sort} onValueChange={(v) => applyFilters({ sort: v })}>
          <SelectTrigger className="w-[110px]" aria-label="排序"><SelectValue /></SelectTrigger>
          <SelectContent>
            {SORTS.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={filters.order} onValueChange={(v) => applyFilters({ order: v as 'asc' | 'desc' })}>
          <SelectTrigger className="w-[90px]" aria-label="方向"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">降序</SelectItem>
            <SelectItem value="asc">升序</SelectItem>
          </SelectContent>
        </Select>

        <Button variant="outline" onClick={reset}>重置</Button>
      </div>

      {/* 标签多选：shadcn Select 不原生支持 multiple，改用可切换的胶囊按钮，语义等价且可键盘操作 */}
      {tags && tags.length > 0 && (
        <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="标签筛选">
          {tags.map((t) => {
            const selected = filters.tag?.includes(t.name) ?? false;
            return (
              <button
                key={t.id}
                type="button"
                aria-pressed={selected}
                className={
                  'rounded-full border px-3 py-1 text-xs ' +
                  (selected ? 'border-primary bg-primary text-primary-foreground' : 'hover:bg-accent')
                }
                onClick={() => {
                  const next = new Set(filters.tag ?? []);
                  if (selected) next.delete(t.name);
                  else next.add(t.name);
                  applyFilters({ tag: next.size ? [...next] : undefined });
                }}
              >
                {t.name} ({t.count})
              </button>
            );
          })}
        </div>
      )}

      <SubjectGrid
        items={data?.content ?? []}
        loading={isLoading}
        total={data?.total}
        page={data?.page}
        size={data?.size}
        onPageChange={(p) => setParams({ q, page: String(p) })}
      />
    </div>
  );
}
