import { Layout, Menu, Button, message, theme } from 'antd';
import type { MenuProps } from 'antd';
import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { authApi, completeLogout, useAuthStore } from '@shared';

const { Sider, Header, Content } = Layout;
const MENU: MenuProps['items'] = [
  { key: '/admin/dashboard', label: '看板' }, { key: '/admin/subjects', label: '番剧管理' }, { key: '/admin/users', label: '用户管理' },
  { key: '/admin/import', label: '导入管理' }, { key: '/admin/logs', label: '日志审计' }, { key: '/admin/agent-config', label: 'Agent 配置' }, { key: '/admin/agent-chat', label: 'Agent 对话' },
];
export function AdminLayout() {
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const user = useAuthStore((s) => s.user);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const onLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      if (await completeLogout(authApi.logout)) navigate('/admin/login');
      else message.error('退出失败，请重试');
    } finally {
      setIsLoggingOut(false);
    }
  };
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={200} style={{ borderRight: `1px solid ${token.colorBorderSecondary}` }}>
        <div style={{ padding: 16, fontWeight: 700 }}>AnimeTracker 后台</div>
        <Menu mode="inline" items={MENU} onClick={({ key }) => navigate(key)} />
      </Sider>
      <Layout>
        <Header style={{ background: token.colorBgContainer, borderBottom: `1px solid ${token.colorBorderSecondary}`, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <span style={{ marginRight: 12 }}>{user?.username}</span>
          <Button size="small" loading={isLoggingOut} disabled={isLoggingOut} onClick={() => void onLogout()}>{isLoggingOut ? '退出中…' : '退出'}</Button>
        </Header>
        <Content style={{ padding: 24 }}><Outlet /></Content>
      </Layout>
    </Layout>
  );
}
