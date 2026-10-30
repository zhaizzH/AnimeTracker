import { useEffect, useMemo, useState } from 'react';
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
// 四个可写进 URL 的筛选字段；默认值在 URL 缺省时生效、不写入地址栏
const FILTER_KEYS = ['sort', 'order', 'year', 'weekday'] as const;
type FilterKey = (typeof FILTER_KEYS)[number];
const FILTER_DEFAULTS: Record<FilterKey, string | undefined> = { sort: 'score', order: 'desc', year: undefined, weekday: undefined };
// 非法数值（?year=abc）当未筛选：NaN 带进 queryKey/请求参数会直接打到后端
function toNum(value: string | null): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}
// 折叠时按热度展示的标签数，其余收入“展开全部”
const TAG_LIMIT = 12;

export default function AnimeIndex() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  // 标签以 URL 为唯一来源：详情页标签链接直达 /anime?tag=x，切换标签无需组件重挂载即可生效
  const selectedTags = params.getAll('tag');
  const [keyword, setKeyword] = useState(q);
  // q 只在提交时变，同步是幂等的；用 key={q} 重挂会丢输入焦点
  useEffect(() => setKeyword(q), [q]);
  // 筛选以 URL 为唯一来源（与本文件既有约定一致）：四个字段都从 params 派生，默认值不在 URL 时生效
  const sort = params.get('sort') ?? 'score';
  const order = params.get('order') === 'asc' ? 'asc' : 'desc';
  const year = toNum(params.get('year'));
  const weekday = toNum(params.get('weekday'));
  const page = Number(params.get('page') ?? 1);

  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list });
  const { data: years } = useQuery({ queryKey: ['subjects', 'years'], queryFn: subjectsApi.years });
  // queryKey 用原始标量：对象每次渲染都是新引用，标量天然稳定，且漏字段会让换筛选不重查
  const { data, isLoading } = useQuery({
    queryKey: ['subjects', 'search', q, sort, order, year, weekday, page, selectedTags],
    queryFn: () =>
      subjectsApi.search({
        q,
        page,
        size: 24,
        sort,
        order,
        year,
        weekday,
        tag: selectedTags.length ? selectedTags : undefined,
      }),
  });

  // 以当前 params 为底重建：保留 q/tag 等未提及的键；默认值不写进 URL，保持地址栏干净
  // 筛选值用字符串（与 URL 编码一致），page 用数字（翻页回调直接给数字）
  const nav = (patch: Partial<Record<FilterKey | 'q', string | undefined>> & { tags?: string[]; page?: number } = {}) => {
    const next = new URLSearchParams(params);
    const text = patch.q ?? q;
    if (text) next.set('q', text);
    else next.delete('q');
    if (patch.tags) {
      next.delete('tag');
      patch.tags.forEach((t) => next.append('tag', t));
    }
    let touchedFilter = false;
    FILTER_KEYS.forEach((key) => {
      if (!(key in patch)) return;
      touchedFilter = true;
      const value = patch[key];
      if (value == null || value === FILTER_DEFAULTS[key]) next.delete(key);
      else next.set(key, value);
    });
    // 筛选与标签变更都回第 1 页；翻页本身（只传 page）不被重置
    const resetsPage = touchedFilter || patch.tags != null || patch.q != null;
    next.set('page', String(patch.page ?? (resetsPage ? 1 : page)));
    setParams(next);
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

        <Select value={year != null ? String(year) : ALL} onValueChange={(v) => nav({ year: v === ALL ? undefined : v })}>
          <SelectTrigger className="w-[110px]" aria-label="年份"><SelectValue placeholder="年份" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部年份</SelectItem>
            {(years ?? []).map((y) => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={weekday != null ? String(weekday) : ALL} onValueChange={(v) => nav({ weekday: v === ALL ? undefined : v })}>
          <SelectTrigger className="w-[110px]" aria-label="播出星期"><SelectValue placeholder="播出星期" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部星期</SelectItem>
            {WEEKDAYS.map((label, i) => <SelectItem key={i} value={String(i)}>{label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={sort} onValueChange={(v) => nav({ sort: v })}>
          <SelectTrigger className="w-[110px]" aria-label="排序"><SelectValue /></SelectTrigger>
          <SelectContent>
            {SORTS.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={order} onValueChange={(v) => nav({ order: v })}>
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
