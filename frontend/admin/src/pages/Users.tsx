import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminUsersApi, type UserRole, type UserVO } from '@shared';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toastError, toastSuccess } from '@/lib/toast';

export default function Users() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const pendingUserIds = useRef(new Set<number>());
  const [pendingUserIdsSnapshot, setPendingUserIdsSnapshot] = useState<ReadonlySet<number>>(() => new Set());
  const { data, isLoading } = useQuery({ queryKey: ['admin-users', page], queryFn: () => adminUsersApi.list({ page, size: 20 }) });
  const change = useMutation({
    mutationFn: ({ id, role }: { id: number; role: UserRole }) => adminUsersApi.updateRole(id, role),
    onSuccess: () => { toastSuccess('角色已更新'); qc.invalidateQueries({ queryKey: ['admin-users'] }); },
    onError: (e) => toastError((e as Error).message),
  });
  const toggle = useMutation({
    mutationFn: async ({ id, enabled }: { id: number; enabled: boolean }) => {
      try {
        return await adminUsersApi.updateEnabled(id, enabled);
      } finally {
        pendingUserIds.current.delete(id);
        setPendingUserIdsSnapshot(new Set(pendingUserIds.current));
      }
    },
    onSuccess: (_, vars) => { toastSuccess(vars.enabled ? '用户已启用' : '用户已禁用'); qc.invalidateQueries({ queryKey: ['admin-users'] }); },
    onError: (e) => toastError((e as Error).message),
  });
  const setUserEnabled = (id: number, enabled: boolean) => {
    if (pendingUserIds.current.has(id)) return;
    pendingUserIds.current.add(id);
    setPendingUserIdsSnapshot(new Set(pendingUserIds.current));
    toggle.mutate({ id, enabled });
  };

  const content = data?.content ?? [];

  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[60px]">ID</TableHead>
            <TableHead>用户名</TableHead>
            <TableHead>邮箱</TableHead>
            <TableHead>昵称</TableHead>
            <TableHead>注册时间</TableHead>
            <TableHead className="w-[120px]">状态</TableHead>
            <TableHead className="w-[130px]">角色</TableHead>
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
              <TableCell colSpan={7}>暂无用户数据</TableCell>
            </TableRow>
          )}
          {!isLoading && content.map((rec: UserVO) => {
            const loading = pendingUserIdsSnapshot.has(rec.id);
            const control = (
              <Switch
                checked={rec.enabled}
                aria-label={`${rec.enabled ? '禁用' : '启用'}用户 ${rec.username}`}
                disabled={loading}
                onCheckedChange={rec.enabled ? undefined : () => setUserEnabled(rec.id, true)}
              />
            );
            return (
              <TableRow key={rec.id}>
                <TableCell>{rec.id}</TableCell>
                <TableCell>{rec.username}</TableCell>
                <TableCell>{rec.email}</TableCell>
                <TableCell>{rec.nickname}</TableCell>
                <TableCell>{rec.createdAt}</TableCell>
                <TableCell>
                  {rec.enabled ? (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>{control}</AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>禁用用户</AlertDialogTitle>
                          <AlertDialogDescription>
                            禁用后，该用户将在所有设备上立即退出。确定继续吗？
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>取消</AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-destructive text-white hover:bg-destructive/90"
                            onClick={() => setUserEnabled(rec.id, false)}
                          >
                            确定
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  ) : control}
                </TableCell>
                {/* ponytail: Select 变更即 mutate，不包确认弹窗 —— 与 antd 版一致，避免确认框取值脆弱 */}
                <TableCell>
                  <Select value={rec.role} onValueChange={(role) => change.mutate({ id: rec.id, role: role as UserRole })}>
                    <SelectTrigger aria-label={`用户 ${rec.username} 的角色`} className="w-[110px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USER">USER</SelectItem>
                      <SelectItem value="ADMIN">ADMIN</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      <div className="flex items-center justify-end gap-3">
        <span className="text-sm text-muted-foreground">
          共 {data?.total ?? 0} 条
        </span>
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
