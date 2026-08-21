import { Layout, Menu, Input, Dropdown, Avatar, Grid, theme } from 'antd';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore, authApi } from '@shared';

const { Header } = Layout;
export function ClientLayout() {
  const navigate = useNavigate();
  const screens = Grid.useBreakpoint();
  const { token } = theme.useToken();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const onLogout = async () => { try { await authApi.logout(); } finally { logout(); navigate('/login'); } };
  const menu = {
    items: [
      { key: 'profile', label: <Link to="/profile">个人中心</Link> },
      { key: 'collections', label: <Link to="/my-collections">我的追番</Link> },
      { key: 'agent', label: <Link to="/agent">AI 助手</Link> },
      user?.role === 'ADMIN' ? { key: 'admin', label: <a href="/admin">管理后台</a> } : null,
      { key: 'logout', label: '退出登录' },
    ].filter(Boolean) as any[], onClick: ({ key }: { key: string }) => { if (key === 'logout') onLogout(); }
  };
  return (
    <Layout>
      <Header className="od-header">
        <Link to="/" className="od-brand" style={{ fontWeight: 700, color: token.colorText, fontSize: 20 }}>AnimeTracker</Link>
        <Menu mode="horizontal" items={[{ key: 'home', label: <Link to="/">首页</Link> }, { key: 'schedule', label: <Link to="/schedule">每周日程</Link> }, { key: 'anime', label: <Link to="/anime">番剧索引</Link> }]} style={{ flex: 1, borderBottom: 'none' }} />
        {screens.md && <Input.Search placeholder="搜索番剧" onSearch={(q) => navigate(`/anime?q=${encodeURIComponent(q)}`)} style={{ width: 220 }} />}
        {user ? <Dropdown menu={menu}><Avatar style={{ background: token.colorPrimary, cursor: 'pointer' }}>{user.nickname ?? user.username?.slice(0, 1)}</Avatar></Dropdown> : <Link to="/login">登录</Link>}
      </Header>
      <Outlet />
    </Layout>
  );
}
