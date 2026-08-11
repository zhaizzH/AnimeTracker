import { useEffect, useMemo, useState } from 'react';
import { App, Avatar, Button, Input, Modal, Select, Table, Tooltip } from 'antd';
import type { TablePaginationConfig, TableProps } from 'antd';
import { ReloadOutlined, SearchOutlined, SwapOutlined } from '@ant-design/icons';
import { adminUsersApi } from '../api/adminUsers';
import type { UserVO } from '../types/api';

function hueOf(id: number): number {
  return Math.abs(Math.sin(id * 12.9898) * 43758.5453) % 360;
}

function roleLabel(role: UserVO['role']): string {
  return role === 'ADMIN' ? '管理员' : '普通用户';
}

export default function Users() {
  const { message } = App.useApp();
  const [list, setList] = useState<UserVO[]>([]);
  const [keyword, setKeyword] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | UserVO['role']>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [roleTarget, setRoleTarget] = useState<UserVO | null>(null);
  const [nextRole, setNextRole] = useState<UserVO['role'] | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async (nextPage = page, nextSize = pageSize) => {
    setLoading(true);
    try {
      const result = await adminUsersApi.list({ page: nextPage, size: nextSize });
      setList(result.content ?? []);
      setTotal(result.total ?? 0);
      setPage(result.page ?? nextPage);
      setPageSize(result.size ?? nextSize);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '用户列表加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refresh = () => load(page, pageSize);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    const nextPage = pagination.current ?? 1;
    const nextSize = pagination.pageSize ?? pageSize;
    setPage(nextPage);
    setPageSize(nextSize);
    load(nextPage, nextSize);
  };

  const filtered = useMemo(() => {
    const kw = keyword.trim().toLowerCase();
    return list.filter((user) => {
      const hitKeyword =
        !kw ||
        user.username.toLowerCase().includes(kw) ||
        user.nickname.toLowerCase().includes(kw) ||
        user.email.toLowerCase().includes(kw);
      const hitRole = roleFilter === 'all' || user.role === roleFilter;
      return hitKeyword && hitRole;
    });
  }, [list, keyword, roleFilter]);

  const todayNewCount = list.filter((u) => u.createdAt.startsWith('2026-08-05')).length;

  const openRoleModal = (user: UserVO) => {
    setRoleTarget(user);
    setNextRole(user.role);
  };

  const handleRoleChange = async () => {
    if (!roleTarget || !nextRole || nextRole === roleTarget.role) return;
    setSaving(true);
    try {
      await adminUsersApi.updateRole(roleTarget.id, nextRole);
      message.success(`${roleTarget.username} 角色已调整为 ${nextRole}`);
      setRoleTarget(null);
      setNextRole(null);
      refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '角色调整失败');
    } finally {
      setSaving(false);
    }
  };

  const columns: TableProps<UserVO>['columns'] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
      className: 'num',
      render: (value: number) => `#${value}`,
    },
    {
      title: '用户',
      dataIndex: 'username',
      render: (_, user) => (
        <div className="rank-cell">
          <Avatar
            size={30}
            style={{
              flex: 'none',
              color: '#ffffff',
              fontFamily: 'var(--mono)',
              fontSize: 12,
              background: `linear-gradient(135deg, hsl(${hueOf(user.id)} 45% 40%), hsl(${(hueOf(user.id) + 45) % 360} 52% 22%))`,
            }}
          >
            {user.username.slice(0, 1).toUpperCase()}
          </Avatar>
          <span className="subject-name">
            <b>{user.nickname}</b>
            <span>@{user.username}</span>
          </span>
        </div>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      width: 220,
      render: (value: string) => <span className="cell-muted">{value || '-'}</span>,
    },
    {
      title: '角色',
      dataIndex: 'role',
      width: 96,
      render: (value: UserVO['role']) => (
        <span className={`status-tag ${value === 'ADMIN' ? 'admin' : 'neutral'}`}>
          <span className="status-dot" />
          {roleLabel(value)}
        </span>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'createdAt',
      width: 170,
      className: 'num',
      render: (value: string) => value || '-',
    },
    {
      title: '操作',
      width: 120,
      render: (_, user) => (
        <Button type="link" size="small" icon={<SwapOutlined />} onClick={() => openRoleModal(user)}>
          调整角色
        </Button>
      ),
    },
  ];

  return (
    <div className="dash-stack">
      <div className="dash-toolbar">
        <div>
          <div className="dash-toolbar-sub">接口 · GET /api/admin/users?page=1&size=20</div>
        </div>
        <div className="dash-toolbar-actions">
          <Tooltip title="刷新用户数据">
            <Button icon={<ReloadOutlined spin={loading} />} onClick={refresh} />
          </Tooltip>
        </div>
      </div>

      <div className="mini-stats">
        <div className="mini-stat tone-cyan">
          <div>
            <div className="mini-stat-label">用户总数</div>
            <div className="mini-stat-value">{total.toLocaleString()}</div>
          </div>
        </div>
        <div className="mini-stat tone-green">
          <div>
            <div className="mini-stat-label">今日新增</div>
            <div className="mini-stat-value">{todayNewCount}</div>
          </div>
        </div>
      </div>

      <div className="filter-panel">
        <div className="filter-item">
          <span>关键词</span>
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="用户名 / 昵称 / 邮箱"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 260 }}
          />
        </div>
        <div className="filter-item">
          <span>角色</span>
          <Select
            value={roleFilter}
            onChange={setRoleFilter}
            style={{ width: 150 }}
            options={[
              { value: 'all', label: '全部角色' },
              { value: 'ADMIN', label: '管理员' },
              { value: 'USER', label: '普通用户' },
            ]}
          />
        </div>
        <div className="filter-spacer" />
        <span className="filter-count">匹配 {filtered.length} / {list.length}</span>
      </div>

      <section className="panel table-panel">
        <div className="panel-head">
          <div>
            <h3 className="panel-title">
              <span className="seq">01</span>用户列表
            </h3>
            <div className="panel-sub">角色变更接口 POST /api/admin/users/{'{id}'}/update-role</div>
          </div>
          <span className="panel-note">第 {page}/{Math.max(1, Math.ceil(total / pageSize))} 页</span>
        </div>
        <Table<UserVO>
          rowKey="id"
          columns={columns}
          dataSource={filtered}
          loading={loading}
          size="middle"
          onChange={handleTableChange}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            pageSizeOptions: [10, 20, 50, 100],
            showTotal: (count) => `共 ${count} 条`,
          }}
          scroll={{ x: 900 }}
        />
      </section>

      <Modal
        title={roleTarget ? `调整角色 · ${roleTarget.username}` : '调整角色'}
        open={!!roleTarget}
        onCancel={() => {
          setRoleTarget(null);
          setNextRole(null);
        }}
        onOk={handleRoleChange}
        okButtonProps={{ disabled: !roleTarget || !nextRole || nextRole === roleTarget.role }}
        confirmLoading={saving}
        okText="确认调整"
        cancelText="取消"
      >
        <p className="modal-desc">
          将 <b>{roleTarget?.nickname ?? ''}</b>（@{roleTarget?.username ?? ''}）的角色从{' '}
          <b>{roleTarget ? roleLabel(roleTarget.role) : '-'}</b> 调整为：
        </p>
        <Select
          value={nextRole}
          onChange={setNextRole}
          style={{ width: '100%' }}
          options={[
            { value: 'USER', label: '普通用户' },
            { value: 'ADMIN', label: '管理员' },
          ]}
        />
      </Modal>
    </div>
  );
}
