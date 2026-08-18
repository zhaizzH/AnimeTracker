import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Select, Table, message } from 'antd';
import { adminUsersApi, type UserRole } from '@shared';

export default function Users() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({ queryKey: ['admin-users', page], queryFn: () => adminUsersApi.list({ page, size: 20 }) });
  const change = useMutation({
    mutationFn: ({ id, role }: { id: number; role: UserRole }) => adminUsersApi.updateRole(id, role),
    onSuccess: () => { message.success('角色已更新'); qc.invalidateQueries({ queryKey: ['admin-users'] }); },
    onError: (e) => message.error((e as Error).message),
  });
  return (
    <Table rowKey="id" loading={isLoading} dataSource={data?.content ?? []} pagination={{ current: page, total: data?.total, pageSize: 20, onChange: setPage }} columns={[
      { title: 'ID', dataIndex: 'id', width: 60 }, { title: '用户名', dataIndex: 'username' }, { title: '邮箱', dataIndex: 'email' },
      { title: '昵称', dataIndex: 'nickname' }, { title: '注册时间', dataIndex: 'createdAt' },
      // ponytail: Select onChange 直接变更角色（变更即调用 + message 提示），避免 Popconfirm 包裹 Select 取值的脆弱交互
      { title: '角色', dataIndex: 'role', render: (r: UserRole, rec: { id: number }) => (
        <Select value={r} onChange={(role: UserRole) => change.mutate({ id: rec.id, role })} options={[{ value: 'USER', label: 'USER' }, { value: 'ADMIN', label: 'ADMIN' }]} style={{ width: 110 }} />
      ) },
    ]} />
  );
}
