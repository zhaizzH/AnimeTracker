import { Layout, Menu, Button } from 'antd';
import type { MenuProps } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import { authApi, useAuthStore } from '@shared';

const { Sider, Header, Content } = Layout;
const MENU: MenuProps['items'] = [
  { key: '/admin/dashboard', label: '看板' }, { key: '/admin/subjects', label: '番剧管理' }, { key: '/admin/users', label: '用户管理' },
  { key: '/admin/import', label: '导入管理' }, { key: '/admin/logs', label: '日志审计' }, { key: '/admin/agent-config', label: 'Agent 配置' }, { key: '/admin/agent-chat', label: 'Agent 对话' },
];
export function AdminLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const onLogout = async () => { try { await authApi.logout(); } finally { logout(); navigate('/admin/login'); } };
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={200} style={{ borderRight: '1px solid #eee' }}>
        <div style={{ padding: 16, fontWeight: 700 }}>AnimeTracker 后台</div>
        <Menu mode="inline" items={MENU} onClick={({ key }) => navigate(key)} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <span style={{ marginRight: 12 }}>{user?.username}</span>
          <Button size="small" onClick={onLogout}>退出</Button>
        </Header>
        <Content style={{ padding: 24 }}><Outlet /></Content>
      </Layout>
    </Layout>
  );
}
