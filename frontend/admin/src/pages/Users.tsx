import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Popconfirm, Select, Switch, Table, message } from 'antd';
import { adminUsersApi, type UserRole, type UserVO } from '@shared';

export default function Users() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const pendingUserIds = useRef(new Set<number>());
  const [pendingUserIdsSnapshot, setPendingUserIdsSnapshot] = useState<ReadonlySet<number>>(() => new Set());
  const { data, isLoading } = useQuery({ queryKey: ['admin-users', page], queryFn: () => adminUsersApi.list({ page, size: 20 }) });
  const change = useMutation({
    mutationFn: ({ id, role }: { id: number; role: UserRole }) => adminUsersApi.updateRole(id, role),
    onSuccess: () => { message.success('角色已更新'); qc.invalidateQueries({ queryKey: ['admin-users'] }); },
    onError: (e) => message.error((e as Error).message),
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
    onSuccess: (_, vars) => { message.success(vars.enabled ? '用户已启用' : '用户已禁用'); qc.invalidateQueries({ queryKey: ['admin-users'] }); },
    onError: (e) => message.error((e as Error).message),
  });
  const setUserEnabled = (id: number, enabled: boolean) => {
    if (pendingUserIds.current.has(id)) return;
    pendingUserIds.current.add(id);
    setPendingUserIdsSnapshot(new Set(pendingUserIds.current));
    toggle.mutate({ id, enabled });
  };
  return (
    <Table<UserVO> rowKey="id" loading={isLoading} dataSource={data?.content ?? []} pagination={{ current: page, total: data?.total, pageSize: 20, onChange: setPage }} columns={[
      { title: 'ID', dataIndex: 'id', width: 60 }, { title: '用户名', dataIndex: 'username' }, { title: '邮箱', dataIndex: 'email' },
      { title: '昵称', dataIndex: 'nickname' }, { title: '注册时间', dataIndex: 'createdAt' },
      { title: '状态', dataIndex: 'enabled', width: 120, render: (enabled: boolean, rec: UserVO) => {
        const loading = pendingUserIdsSnapshot.has(rec.id);
        const control = (
          <Switch
            checked={enabled}
            checkedChildren="启用"
            unCheckedChildren="禁用"
            aria-label={`${enabled ? '禁用' : '启用'}用户 ${rec.username}`}
            loading={loading}
            disabled={loading}
            onChange={enabled ? undefined : () => setUserEnabled(rec.id, true)}
          />
        );
        return enabled ? (
          <Popconfirm
            title="禁用用户"
            description="禁用后，该用户将在所有设备上立即退出。确定继续吗？"
            okText="确定"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={() => setUserEnabled(rec.id, false)}
          >
            {control}
          </Popconfirm>
        ) : control;
      } },
      // ponytail: Select onChange 直接变更角色（变更即调用 + message 提示），避免 Popconfirm 包裹 Select 取值的脆弱交互
      { title: '角色', dataIndex: 'role', render: (r: UserRole, rec: UserVO) => (
        <Select value={r} onChange={(role: UserRole) => change.mutate({ id: rec.id, role })} options={[{ value: 'USER', label: 'USER' }, { value: 'ADMIN', label: 'ADMIN' }]} style={{ width: 110 }} />
      ) },
    ]} />
  );
}
