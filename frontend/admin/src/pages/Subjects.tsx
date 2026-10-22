import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { SearchIcon, XIcon } from 'lucide-react';
import { adminSubjectsApi, subjectsApi, tagsApi } from '@shared';
import { TagChip } from '@/components/TagChip';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from '@/components/ui/input-group';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { toastError, toastSuccess } from '@/lib/toast';

type SubjectFilters = { q?: string; tag?: string[]; scoreMin?: number; scoreMax?: number; year?: number; weekday?: number };
const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
const ALL = '__all__';
// 折叠时按热度展示的标签数，其余收入“展开全部”（与 client /anime 索引页一致）
const TAG_LIMIT = 12;

type FormState = {
  bangumiId?: string; name: string; nameCn?: string; summary?: string;
  type?: string; eps?: string; airDate?: string; image?: string;
};

const EMPTY_FORM: FormState = { name: '', type: '2' };

/** 数值输入统一收窄：空串 → undefined，避免 NaN 进入请求体。 */
const toNumber = (v: string | undefined) => (v === undefined || v === '' ? undefined : Number(v));

export default function Subjects() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<SubjectFilters>({});
  const setFilter = (patch: Partial<SubjectFilters>) => { setFilters((f) => ({ ...f, ...patch })); setPage(1); };
  // 关键词与评分区间保留输入态字符串：受控于 filters 会把 “0.” 这类中间态抹成 “0”，无法继续输入小数
  const [keyword, setKeyword] = useState('');
  const [scoreMin, setScoreMin] = useState('');
  const [scoreMax, setScoreMax] = useState('');
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list, staleTime: 60_000 });
  const { data: years } = useQuery({ queryKey: ['subject-years'], queryFn: subjectsApi.years, staleTime: 60_000 });
  // 展开与标签搜索只是视图状态，不进请求参数；已选标签始终置顶，避免冷门标签被折叠隐藏
  const [tagsExpanded, setTagsExpanded] = useState(false);
  const [tagQuery, setTagQuery] = useState('');
  const selectedTags = filters.tag ?? [];
  const searchingTags = tagQuery.trim().length > 0;
  const showTagSearch = (tags?.length ?? 0) > TAG_LIMIT;

  const visibleTags = useMemo(() => {
    if (!tags) return [];
    const kw = tagQuery.trim();
    const pinned = tags.filter((t) => selectedTags.includes(t.name));
    // 搜索时全量匹配而不截断，否则想找的标签可能被 Top-N 挡在结果外
    const rest = tags.filter((t) => !selectedTags.includes(t.name) && (!kw || t.name.includes(kw)));
    if (searchingTags || tagsExpanded) return [...pinned, ...rest];
    return [...pinned, ...rest.sort((a, b) => b.count - a.count).slice(0, TAG_LIMIT)];
  }, [tags, tagsExpanded, selectedTags, tagQuery, searchingTags]);
  // 搜索时可见项是匹配子集，不能再拿总数差当“被折叠数”
  const hiddenTagCount = searchingTags ? 0 : (tags?.length ?? 0) - visibleTags.length;

  const toggleTag = (name: string) => {
    const next = new Set(selectedTags);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setFilter({ tag: next.size ? [...next] : undefined });
  };
  const reset = () => {
    setFilters({});
    setKeyword('');
    setScoreMin('');
    setScoreMax('');
    setPage(1);
  };
  const { data, isLoading } = useQuery({ queryKey: ['admin-subjects', filters, page], queryFn: () => subjectsApi.search({ ...filters, page, size: 20, sort: 'score', order: 'desc' }) });
  const inval = () => { qc.invalidateQueries({ queryKey: ['admin-subjects'] }); };
  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setFormError(''); setOpen(true); };
  const openEdit = (id: number, rec: Partial<adminSubjectsApi.SubjectForm>) => {
    setEditing(id);
    setForm({
      bangumiId: rec.bangumiId === undefined ? undefined : String(rec.bangumiId),
      name: rec.name ?? '', nameCn: rec.nameCn ?? '', summary: rec.summary ?? '',
      type: rec.type === undefined ? undefined : String(rec.type),
      eps: rec.eps === undefined ? undefined : String(rec.eps),
      airDate: rec.airDate ?? '', image: rec.image ?? '',
    });
    setFormError('');
    setOpen(true);
  };
  const save = useMutation({
    mutationFn: async (v: adminSubjectsApi.SubjectForm) => { if (editing) await adminSubjectsApi.update(editing, v); else await adminSubjectsApi.create(v); },
    onSuccess: () => { toastSuccess('已保存'); setOpen(false); inval(); },
    onError: (e) => toastError((e as Error).message),
  });
  const del = useMutation({ mutationFn: (id: number) => adminSubjectsApi.remove(id), onSuccess: () => { toastSuccess('已删除'); inval(); } });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    // 与 antd 版一致：bangumiId 与 name 必填（bangumiId 仅新建时要求）
    if (!form.name.trim()) { setFormError('请填写日文/英文名'); return; }
    if (!editing && !form.bangumiId) { setFormError('请填写 Bangumi ID'); return; }
    setFormError('');
    save.mutate({
      bangumiId: toNumber(form.bangumiId),
      name: form.name.trim(),
      nameCn: form.nameCn || undefined,
      summary: form.summary || undefined,
      type: toNumber(form.type),
      eps: toNumber(form.eps),
      airDate: form.airDate || undefined,
      image: form.image || undefined,
    });
  };

  const content = (data?.content ?? []) as unknown as Record<string, unknown>[];

  return (
    <div className="flex flex-col gap-4">
      {/* 搜索卡片与 client /anime 索引页保持同一骨架：rounded-xl 卡片 + 行内筛选 + 底部标签胶囊区 */}
      <div className="flex flex-wrap gap-3 rounded-xl border bg-card p-4">
        <form
          className="flex gap-2"
          onSubmit={(e) => { e.preventDefault(); setFilter({ q: keyword.trim() || undefined }); }}
        >
          <Input
            aria-label="搜索番剧"
            placeholder="搜索番剧"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="w-[200px]"
          />
          <Button type="submit" variant="outline">搜索</Button>
        </form>

        <Select value={filters.year != null ? String(filters.year) : ALL} onValueChange={(v) => setFilter({ year: v === ALL ? undefined : Number(v) })}>
          <SelectTrigger aria-label="年份" className="w-[110px]">
            <SelectValue placeholder="年份" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部年份</SelectItem>
            {(years ?? []).map((y) => (
              <SelectItem key={y} value={String(y)}>{y}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filters.weekday != null ? String(filters.weekday) : ALL} onValueChange={(v) => setFilter({ weekday: v === ALL ? undefined : Number(v) })}>
          <SelectTrigger aria-label="星期" className="w-[110px]">
            <SelectValue placeholder="星期" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部星期</SelectItem>
            {WEEKDAYS.map((w, i) => (
              <SelectItem key={w} value={String(i)}>{w}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="number" min={0} max={10} step={0.1} placeholder="最低评分" aria-label="最低评分"
          className="w-[110px]"
          value={scoreMin}
          onChange={(e) => { setScoreMin(e.target.value); setFilter({ scoreMin: toNumber(e.target.value) }); }}
        />
        <Input
          type="number" min={0} max={10} step={0.1} placeholder="最高评分" aria-label="最高评分"
          className="w-[110px]"
          value={scoreMax}
          onChange={(e) => { setScoreMax(e.target.value); setFilter({ scoreMax: toNumber(e.target.value) }); }}
        />

        <Button variant="outline" onClick={reset}>重置</Button>
        <Button onClick={openCreate}>新建番剧</Button>

        {/* 标签多选：shadcn Select 不原生支持 multiple，用可切换胶囊按钮，语义等价且可键盘操作 */}
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

            {/* 内层限高滚动：标签再多也不会把下面的列表顶出视口 */}
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

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[60px]">ID</TableHead>
            <TableHead className="w-[50px]">封面</TableHead>
            <TableHead>中文名</TableHead>
            <TableHead>原名</TableHead>
            <TableHead className="w-[80px]">评分</TableHead>
            <TableHead className="w-[70px]">集数</TableHead>
            <TableHead className="w-[160px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={7} role="status">加载中…</TableCell>
            </TableRow>
          )}
          {!isLoading && content.length === 0 && (
            <TableRow>
              <TableCell colSpan={7}>暂无番剧数据</TableCell>
            </TableRow>
          )}
          {!isLoading && content.map((r) => (
            <TableRow key={String(r.id)}>
              <TableCell>{String(r.id)}</TableCell>
              <TableCell>
                {r.image ? (
                  <img src={String(r.image)} alt="" className="w-9 rounded object-cover" style={{ aspectRatio: '3/4' }} />
                ) : null}
              </TableCell>
              <TableCell>{String(r.nameCn ?? '')}</TableCell>
              <TableCell>{String(r.name ?? '')}</TableCell>
              <TableCell>{String(r.score ?? '')}</TableCell>
              <TableCell>{String(r.eps ?? '')}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(Number(r.id), r as Partial<adminSubjectsApi.SubjectForm>)}>
                    编辑
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="sm" variant="destructive">删除</Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>删除番剧</AlertDialogTitle>
                        <AlertDialogDescription>确定删除？该操作不可撤销。</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>取消</AlertDialogCancel>
                        <AlertDialogAction
                          className="bg-destructive text-white hover:bg-destructive/90"
                          onClick={() => del.mutate(Number(r.id))}
                        >
                          确定
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <div className="flex items-center justify-end gap-3">
        <span className="text-sm text-muted-foreground">共 {data?.total ?? 0} 条</span>
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>上一页</Button>
        <span className="text-sm">第 {page} 页</span>
        <Button variant="outline" size="sm" disabled={(data?.total ?? 0) <= page * 20} onClick={() => setPage((p) => p + 1)}>下一页</Button>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? '编辑番剧' : '新建番剧'}</DialogTitle>
          </DialogHeader>
          <form className="flex flex-col gap-4" onSubmit={submit}>
            {!editing && (
              <div className="flex flex-col gap-2">
                <Label htmlFor="subject-bangumiId">Bangumi ID</Label>
                <Input
                  id="subject-bangumiId" type="number" aria-label="Bangumi ID"
                  value={form.bangumiId ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, bangumiId: e.target.value }))}
                />
              </div>
            )}
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-name">日文/英文名</Label>
              <Input id="subject-name" aria-label="日文/英文名" value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-nameCn">中文名</Label>
              <Input id="subject-nameCn" aria-label="中文名" value={form.nameCn ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, nameCn: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-summary">简介</Label>
              <Textarea id="subject-summary" rows={4} aria-label="简介" value={form.summary ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-type">类型</Label>
              <Input id="subject-type" type="number" min={1} aria-label="类型" value={form.type ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-eps">总集数</Label>
              <Input id="subject-eps" type="number" min={0} aria-label="总集数" value={form.eps ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, eps: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-airDate">播出日期</Label>
              <Input id="subject-airDate" placeholder="2026-04-01" aria-label="播出日期" value={form.airDate ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, airDate: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="subject-image">封面 URL</Label>
              <Input id="subject-image" aria-label="封面 URL" value={form.image ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, image: e.target.value }))} />
            </div>
            {formError && <p role="alert" className="text-sm text-destructive">{formError}</p>}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>取消</Button>
              <Button type="submit" disabled={save.isPending}>{save.isPending ? '保存中…' : '保存'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
