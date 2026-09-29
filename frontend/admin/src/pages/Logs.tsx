import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminLogsApi } from '@shared';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

const MODULES = ['AUTH', 'USER', 'SUBJECT', 'IMPORT', 'ADMIN'];
const ALL = '__all__';

export default function Logs() {
  const [filter, setFilter] = useState<Record<string, unknown>>({});
  const [page, setPage] = useState(1);
  const [username, setUsername] = useState('');
  const { data, isLoading } = useQuery({ queryKey: ['logs', filter, page], queryFn: () => adminLogsApi.list({ page, size: 20, ...filter }) });
  const stats = data?.stats;
  const content = data?.content ?? [];

  const cards: [string, number | undefined][] = [
    ['总数', stats?.total],
    ['成功', stats?.successCount],
    ['失败', stats?.failedCount],
    ['平均耗时(ms)', stats?.avgDurationMs],
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <Select onValueChange={(v) => setFilter((f) => ({ ...f, module: v === ALL ? undefined : v }))}>
          <SelectTrigger aria-label="模块" className="w-[130px]">
            <SelectValue placeholder="模块" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部模块</SelectItem>
            {MODULES.map((m) => (
              <SelectItem key={m} value={m}>{m}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select onValueChange={(v) => setFilter((f) => ({ ...f, status: v === ALL ? undefined : Number(v) }))}>
          <SelectTrigger aria-label="状态" className="w-[110px]">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>全部状态</SelectItem>
            <SelectItem value="0">成功</SelectItem>
            <SelectItem value="1">失败</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="logs-username">用户名/邮箱</Label>
          <Input
            id="logs-username"
            className="w-[160px]"
            value={username}
            aria-label="用户名/邮箱"
            onChange={(e) => setUsername(e.target.value)}
            // onBlur 触发筛选：避免每次按键都发起请求
            onBlur={(e) => setFilter((f) => ({ ...f, username: e.target.value || undefined }))}
          />
        </div>

        <div className="flex items-end gap-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="logs-start">起始日期</Label>
            <Input id="logs-start" type="date" aria-label="起始日期" onChange={(e) => setFilter((f) => ({ ...f, start: e.target.value || undefined }))} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="logs-end">结束日期</Label>
            <Input id="logs-end" type="date" aria-label="结束日期" onChange={(e) => setFilter((f) => ({ ...f, end: e.target.value || undefined }))} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {cards.map(([label, v]) => (
          <Card key={label}>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-semibold">{v ?? 0}</CardContent>
          </Card>
        ))}
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[70px]">ID</TableHead>
            <TableHead>用户</TableHead>
            <TableHead>模块</TableHead>
            <TableHead>动作</TableHead>
            <TableHead>路径</TableHead>
            <TableHead>IP</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>耗时(ms)</TableHead>
            <TableHead>时间</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={9} role="status">加载中…</TableCell>
            </TableRow>
          )}
          {!isLoading && content.length === 0 && (
            <TableRow>
              <TableCell colSpan={9}>暂无日志</TableCell>
            </TableRow>
          )}
          {!isLoading && content.map((r) => (
            <TableRow key={r.id}>
              <TableCell>{r.id}</TableCell>
              <TableCell>{r.username}</TableCell>
              <TableCell>{r.module}</TableCell>
              <TableCell>
                {/* 点击回填 action 筛选并重置页码 */}
                <Button
                  variant="link"
                  className="h-auto p-0"
                  onClick={() => { setFilter((f) => ({ ...f, action: r.action })); setPage(1); }}
                >
                  {r.action}
                </Button>
              </TableCell>
              <TableCell>{r.path}</TableCell>
              <TableCell>{r.ip}</TableCell>
              <TableCell>{r.status === 0 ? '成功' : '失败'}</TableCell>
              <TableCell>{r.durationMs}</TableCell>
              <TableCell>{r.createdAt}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <div className="flex items-center justify-end gap-3">
        <span className="text-sm text-muted-foreground">共 {data?.total ?? 0} 条</span>
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          上一页
        </Button>
        <span className="text-sm">第 {page} 页</span>
        <Button
          variant="outline"
          size="sm"
          disabled={(data?.total ?? 0) <= page * 20}
          onClick={() => setPage((p) => p + 1)}
        >
          下一页
        </Button>
      </div>
    </div>
  );
}
