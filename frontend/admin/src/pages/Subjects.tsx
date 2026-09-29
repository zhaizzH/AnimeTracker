import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminSubjectsApi, subjectsApi, tagsApi } from '@shared';
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

/** 多选标签筛选：antd Select mode=multiple 的等价实现（原生 checkbox，键盘可达）。 */
function TagFilter({ tags, value, onChange }: { tags: string[]; value: string[]; onChange: (v: string[]) => void }) {
  const toggle = (name: string, checked: boolean) =>
    onChange(checked ? [...value, name] : value.filter((t) => t !== name));
  return (
    <fieldset className="flex flex-wrap items-center gap-3 rounded-md border px-3 py-2">
      <legend className="px-1 text-sm text-muted-foreground">标签</legend>
      {tags.length === 0 && <span className="text-sm text-muted-foreground">无标签</span>}
      {tags.map((name) => (
        <label key={name} className="flex items-center gap-1.5 text-sm">
          <input
            type="checkbox"
            aria-label={`标签 ${name}`}
            checked={value.includes(name)}
            onChange={(e) => toggle(name, e.target.checked)}
          />
          {name}
        </label>
      ))}
    </fieldset>
  );
}

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
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list, staleTime: 60_000 });
  const { data: years } = useQuery({ queryKey: ['subject-years'], queryFn: subjectsApi.years, staleTime: 60_000 });
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
      <div className="flex flex-wrap items-center gap-4">
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => { e.preventDefault(); const v = new FormData(e.currentTarget).get('q'); setFilter({ q: String(v ?? '').trim() || undefined }); }}
        >
          <Input name="q" placeholder="搜索番剧" aria-label="搜索番剧" className="w-[220px]" />
          <Button type="submit" variant="outline" size="sm">搜索</Button>
        </form>

        <TagFilter
          tags={(tags ?? []).map((t) => t.name)}
          value={filters.tag ?? []}
          onChange={(v) => setFilter({ tag: v.length ? v : undefined })}
        />

        <Input
          type="number" min={0} max={10} step={0.1} placeholder="最低评分" aria-label="最低评分"
          className="w-[120px]"
          onChange={(e) => setFilter({ scoreMin: toNumber(e.target.value) })}
        />
        <Input
          type="number" min={0} max={10} step={0.1} placeholder="最高评分" aria-label="最高评分"
          className="w-[120px]"
          onChange={(e) => setFilter({ scoreMax: toNumber(e.target.value) })}
        />

        <Select onValueChange={(v) => setFilter({ year: v === '__all__' ? undefined : Number(v) })}>
          <SelectTrigger aria-label="年份" className="w-[110px]">
            <SelectValue placeholder="年份" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部年份</SelectItem>
            {(years ?? []).map((y) => (
              <SelectItem key={y} value={String(y)}>{y}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select onValueChange={(v) => setFilter({ weekday: v === '__all__' ? undefined : Number(v) })}>
          <SelectTrigger aria-label="星期" className="w-[110px]">
            <SelectValue placeholder="星期" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部星期</SelectItem>
            {WEEKDAYS.map((w, i) => (
              <SelectItem key={w} value={String(i)}>{w}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button onClick={openCreate}>新建番剧</Button>
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
