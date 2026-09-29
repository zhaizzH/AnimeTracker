import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminImportApi } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
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
import { toastError, toastSuccess } from '@/lib/toast';

type Mode = 'full' | 'season' | 'recent' | 'since';

const SEASON_OPTIONS = ['2026-summer', '2026-spring', '2025-winter'];
const STATUS_LABELS: Record<string, string> = {
  RUNNING: '运行中',
  COMPLETED: '已完成',
  FAILED: '失败',
};

/** 数值输入统一收窄：空串 → undefined，避免 NaN 进入请求体。 */
const toNumber = (v: string) => (v === '' ? undefined : Number(v));

export default function ImportPage() {
  const qc = useQueryClient();
  const [mode, setMode] = useState<Mode>('season');
  const [key, setKey] = useState('');
  const [since, setSince] = useState('');
  const [workers, setWorkers] = useState('');
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const rec = useQuery({ queryKey: ['import-records', page, statusFilter], queryFn: () => adminImportApi.records({ page, size: 10, status: statusFilter || undefined }) });
  const st = useQuery({ queryKey: ['import-status'], queryFn: adminImportApi.status, refetchInterval: 3000 });
  const runMut = useMutation({
    mutationFn: () => adminImportApi.run({ mode, key: mode === 'season' ? key || undefined : undefined, since: mode === 'since' ? since || undefined : undefined, workers: toNumber(workers) }),
    onSuccess: (d) => { toastSuccess(d || '导入已触发'); qc.invalidateQueries({ queryKey: ['import-status'] }); },
    onError: (e) => toastError((e as Error).message),
  });
  useEffect(() => { if (st.data && (st.data.totalLogs > 0)) qc.invalidateQueries({ queryKey: ['import-records'] }); }, [st.data, qc]);

  const content = rec.data?.content ?? [];

  return (
    <div className="flex flex-col gap-4">
      <form
        className="flex flex-wrap items-end gap-4"
        onSubmit={(e) => { e.preventDefault(); runMut.mutate(); }}
      >
        <fieldset className="flex items-center gap-3">
          <legend className="mb-1 text-sm font-medium">模式</legend>
          <RadioGroup
            className="flex gap-3"
            value={mode}
            onValueChange={(v) => setMode(v as Mode)}
          >
            {([['full', '全量'], ['season', '季度'], ['recent', '近期'], ['since', '自某日起']] as const).map(([value, label]) => (
              <label key={value} className="flex items-center gap-1.5 text-sm">
                <RadioGroupItem value={value} aria-label={label} />
                {label}
              </label>
            ))}
          </RadioGroup>
        </fieldset>

        {mode === 'season' && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="import-key">季度</Label>
            <Select value={key} onValueChange={setKey}>
              <SelectTrigger id="import-key" aria-label="季度" className="w-[160px]">
                <SelectValue placeholder="2026-summer" />
              </SelectTrigger>
              <SelectContent>
                {SEASON_OPTIONS.map((k) => (
                  <SelectItem key={k} value={k}>{k}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {mode === 'since' && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="import-since">起始日期</Label>
            <Input
              id="import-since"
              placeholder="2026-01-01"
              value={since}
              onChange={(e) => setSince(e.target.value)}
              aria-label="起始日期"
            />
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="import-workers">并发</Label>
          <Input
            id="import-workers"
            type="number"
            min={1}
            value={workers}
            onChange={(e) => setWorkers(e.target.value)}
            aria-label="并发"
            className="w-[110px]"
          />
        </div>

        <Button type="submit" disabled={runMut.isPending}>
          {runMut.isPending ? '触发中…' : '触发导入'}
        </Button>
      </form>

      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
        <span>最近导入：{st.data?.lastImportedAt ?? '从未导入'}</span>
        <span>成功 {st.data?.completedCount ?? 0} · 失败 {st.data?.failedCount ?? 0}</span>
      </div>

      <Select
        value={statusFilter}
        onValueChange={(v) => { setStatusFilter(v === '__all__' ? '' : v); setPage(1); }}
      >
        <SelectTrigger aria-label="状态筛选" className="w-[160px]">
          <SelectValue placeholder="状态筛选" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部状态</SelectItem>
          <SelectItem value="RUNNING">运行中</SelectItem>
          <SelectItem value="COMPLETED">已完成</SelectItem>
          <SelectItem value="FAILED">失败</SelectItem>
        </SelectContent>
      </Select>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>季度</TableHead>
            <TableHead>开始</TableHead>
            <TableHead>完成</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>条目数</TableHead>
            <TableHead>错误</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rec.isLoading && (
            <TableRow>
              <TableCell colSpan={6} role="status">加载中…</TableCell>
            </TableRow>
          )}
          {!rec.isLoading && content.length === 0 && (
            <TableRow>
              <TableCell colSpan={6}>暂无导入记录</TableCell>
            </TableRow>
          )}
          {!rec.isLoading && content.map((r) => (
            <TableRow key={r.id}>
              <TableCell>{r.season}</TableCell>
              <TableCell>{r.startedAt}</TableCell>
              <TableCell>{r.completedAt}</TableCell>
              <TableCell>{STATUS_LABELS[r.status] ?? r.status}</TableCell>
              <TableCell>{r.subjectCount}</TableCell>
              <TableCell>{r.errorMessage}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <div className="flex items-center justify-end gap-3">
        <span className="text-sm text-muted-foreground">共 {rec.data?.total ?? 0} 条</span>
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          上一页
        </Button>
        <span className="text-sm">第 {page} 页</span>
        <Button
          variant="outline"
          size="sm"
          disabled={(rec.data?.total ?? 0) <= page * 10}
          onClick={() => setPage((p) => p + 1)}
        >
          下一页
        </Button>
      </div>
    </div>
  );
}
