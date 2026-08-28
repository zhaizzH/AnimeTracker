import { Layout, Menu, Input, Dropdown, Avatar, Grid, theme, Button, Tooltip, message } from 'antd';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { MoonOutlined, SunOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useAuthStore, authApi, completeLogout, useThemeStore, resolveMode } from '@shared';

const { Header } = Layout;
export function ClientLayout() {
  const navigate = useNavigate();
  const screens = Grid.useBreakpoint();
  const { token } = theme.useToken();
  const user = useAuthStore((s) => s.user);
  const mode = useThemeStore((s) => s.mode);
  const followSystem = useThemeStore((s) => s.followSystem);
  const setMode = useThemeStore((s) => s.setMode);
  const resolved = resolveMode(mode, followSystem);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const onLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      if (await completeLogout(authApi.logout)) navigate('/login');
      else message.error('退出失败，请重试');
    } finally {
      setIsLoggingOut(false);
    }
  };
  const menu = {
    items: [
      { key: 'profile', label: <Link to="/profile">个人中心</Link> },
      { key: 'collections', label: <Link to="/my-collections">我的追番</Link> },
      { key: 'agent', label: <Link to="/agent">AI 助手</Link> },
      { key: 'logout', label: isLoggingOut ? '退出中…' : '退出登录', disabled: isLoggingOut },
    ].filter(Boolean) as any[], onClick: ({ key }: { key: string }) => { if (key === 'logout') void onLogout(); }
  };
  return (
    <Layout>
      <a href="#main" className="od-skip-link">跳到主内容</a>
      <Header className="od-header">
        <Link to="/" className="od-brand" style={{ fontWeight: 700, color: token.colorText, fontSize: 20 }}>AnimeTracker</Link>
        <Menu mode="horizontal" items={[{ key: 'home', label: <Link to="/">首页</Link> }, { key: 'schedule', label: <Link to="/schedule">每周日程</Link> }, { key: 'anime', label: <Link to="/anime">番剧索引</Link> }]} style={{ flex: 1, borderBottom: 'none' }} />
        {screens.md && <Input.Search placeholder="搜索番剧" onSearch={(q) => navigate(`/anime?q=${encodeURIComponent(q)}`)} style={{ width: 220 }} />}
        <Tooltip title={resolved === 'dark' ? '切换到浅色' : '切换到深色'}>
          <Button
            type="text"
            aria-label={resolved === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
            icon={resolved === 'dark' ? <SunOutlined /> : <MoonOutlined />}
            onClick={() => setMode(resolved === 'dark' ? 'light' : 'dark')}
          />
        </Tooltip>
        {user ? <Dropdown menu={menu}><Avatar style={{ background: token.colorPrimary, cursor: 'pointer' }}>{user.nickname ?? user.username?.slice(0, 1)}</Avatar></Dropdown> : <Link to="/login">登录</Link>}
      </Header>
      <main id="main" tabIndex={-1} style={{ outline: 'none' }}>
        <Outlet />
      </main>
    </Layout>
  );
}
