import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { SearchIcon, XIcon } from 'lucide-react';
import { subjectsApi, tagsApi } from '@shared';
import { TagChip } from '@/components/TagChip';
import { SubjectGrid } from '@/components/SubjectGrid';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from '@/components/ui/input-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const SORTS = [
  { value: 'score', label: '评分' },
  { value: 'air_date', label: '播出日期' },
  { value: 'rank', label: '排名' },
  { value: 'collection_total', label: '收藏数' },
];
const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
const ALL = '__all__';
// 折叠时按热度展示的标签数，其余收入“展开全部”
const TAG_LIMIT = 12;

export default function AnimeIndex() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  // 标签以 URL 为唯一来源：详情页标签链接直达 /anime?tag=x，切换标签无需组件重挂载即可生效
  const selectedTags = params.getAll('tag');
  const [keyword, setKeyword] = useState(q);
  const [filters, setFilters] = useState<{ sort?: string; order?: 'asc' | 'desc'; year?: number; weekday?: number }>({ sort: 'score', order: 'desc' });
  const page = Number(params.get('page') ?? 1);

  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list });
  const { data: years } = useQuery({ queryKey: ['subjects', 'years'], queryFn: subjectsApi.years });
  const { data, isLoading } = useQuery({
    queryKey: ['subjects', 'search', q, filters, page, selectedTags],
    queryFn: () => subjectsApi.search({ q, page, size: 24, sort: 'score', order: 'desc', ...filters, tag: selectedTags.length ? selectedTags : undefined }),
  });

  // 所有筛选变更都回写 URL，并统一重置到第 1 页
  const nav = (over: { q?: string; tags?: string[]; page?: number } = {}) => {
    const next = new URLSearchParams();
    const text = over.q ?? q;
    if (text) next.set('q', text);
    (over.tags ?? selectedTags).forEach((t) => next.append('tag', t));
    next.set('page', String(over.page ?? 1));
    setParams(next);
  };
  const applyFilters = (patch: Partial<typeof filters>) => {
    setFilters((f) => ({ ...f, ...patch }));
    nav();
  };
  // 展开与搜索词只是视图状态，不进 URL；已选标签始终置顶，避免 URL 带入的冷门标签被折叠隐藏
  const [tagsExpanded, setTagsExpanded] = useState(false);
  const [tagQuery, setTagQuery] = useState('');
  const searchingTags = tagQuery.trim().length > 0;
  const showTagSearch = (tags?.length ?? 0) > TAG_LIMIT;

  const visibleTags = useMemo(() => {
    if (!tags) return [];
    const kw = tagQuery.trim();
    // 已选恒显：保证任何情况下都能看到并取消自己的筛选
    const pinned = tags.filter((t) => selectedTags.includes(t.name));
    // 搜索时全量匹配而不截断，否则想找的标签可能被 Top-N 挡在结果外，搜了也搜不到
    const rest = tags.filter((t) => !selectedTags.includes(t.name) && (!kw || t.name.includes(kw)));
    if (searchingTags || tagsExpanded) return [...pinned, ...rest];
    // filter 已返回新数组，sort 就地排序不会改动 query 缓存
    return [...pinned, ...rest.sort((a, b) => b.count - a.count).slice(0, TAG_LIMIT)];
  }, [tags, tagsExpanded, selectedTags, tagQuery, searchingTags]);
  // 搜索时可见项是匹配子集，不能再拿总数差当“被折叠数”，否则会误报“展开全部 N 个”
  const hiddenTagCount = searchingTags ? 0 : (tags?.length ?? 0) - visibleTags.length;

  const toggleTag = (name: string) => {
    const next = new Set(selectedTags);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    nav({ tags: [...next] });
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
            nav({ q: keyword });
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

        {/* 标签多选：shadcn Select 不原生支持 multiple，改用可切换的胶囊按钮，语义等价且可键盘操作 */}
        {tags && tags.length > 0 && (
          <div className="-mx-4 mt-4 w-full space-y-2 border-t px-4 pt-3">
            {showTagSearch && (
              <InputGroup className="w-full max-w-xs">
                <InputGroupAddon>
                  <SearchIcon />
                </InputGroupAddon>
                <InputGroupInput
                  value={tagQuery}
                  onChange={(e) => setTagQuery(e.target.value)}
                  placeholder="搜索标签…"
                  aria-label="搜索标签"
                />
                {searchingTags && (
                  <InputGroupAddon align="inline-end">
                    <InputGroupButton
                      size="icon-xs"
                      aria-label="清除标签搜索"
                      onClick={() => setTagQuery('')}
                    >
                      <XIcon />
                    </InputGroupButton>
                  </InputGroupAddon>
                )}
              </InputGroup>
            )}

            {/* 内层限高滚动：标签再多也不会把下面的结果网格顶出视口，缓解“展开后全部弹出” */}
            <div
              className="flex max-h-[7.5rem] flex-wrap items-start gap-2 overflow-y-auto"
              role="group"
              aria-label="标签筛选"
            >
              {visibleTags.map((t) => (
                <TagChip key={t.id} selected={selectedTags.includes(t.name)} onClick={() => toggleTag(t.name)}>
                  {t.name} ({t.count})
                </TagChip>
              ))}
              {!searchingTags && (tagsExpanded || hiddenTagCount > 0) && (
                <button
                  type="button"
                  aria-expanded={tagsExpanded}
                  className="rounded-full px-3 py-1 text-xs text-muted-foreground underline-offset-4 hover:underline"
                  onClick={() => setTagsExpanded((v) => !v)}
                >
                  {tagsExpanded ? '收起' : `展开全部 ${tags.length} 个标签`}
                </button>
              )}
              {searchingTags && visibleTags.length === 0 && (
                <p className="py-1 text-xs text-muted-foreground">没有匹配的标签</p>
              )}
            </div>
          </div>
        )}
      </div>

      <SubjectGrid
        items={data?.content ?? []}
        loading={isLoading}
        total={data?.total}
        page={data?.page}
        size={data?.size}
        onPageChange={(p) => nav({ page: p })}
      />
    </div>
  );
}
