import { useState } from 'react';
import { Layout, Input, Button, Dropdown, Avatar, Space } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth';
import { getCurrentQuarter } from '@/utils';

const { Header: AntHeader } = Layout;

const QUARTER_LABELS: Record<string, string> = {
  spring: '春',
  summer: '夏',
  autumn: '秋',
  winter: '冬',
};

export default function AppHeader() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isLoggedIn } = useAuthStore();
  const { logout } = useAuth();
  const [searchValue, setSearchValue] = useState('');

  const onSearch = (value: string) => {
    if (value.trim()) {
      navigate(`/anime?q=${encodeURIComponent(value.trim())}`);
    }
  };

  const baseNav = [
    { path: '/', label: '今日', index: '01' },
    { path: '/schedule', label: '放送表', index: '02' },
    { path: '/anime', label: '索引', index: '03' },
  ];
  const navItems = baseNav;

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  const todayText = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(new Date());
  const issueLabel = `${new Date().getFullYear()} 年 ${QUARTER_LABELS[getCurrentQuarter()] || ''}季刊`;

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心', onClick: () => navigate('/profile') },
    { key: 'agent', label: 'AI 助手', onClick: () => navigate('/agent') },
    { key: 'collections', label: '我的收藏', onClick: () => navigate('/my-collections') },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout },
  ];

  return (
    <AntHeader className="masthead">
      <div className="masthead-top">
        <span>ANIME TRACKER / 手账</span>
        <span className="issue-note">{todayText} · {issueLabel}</span>
      </div>
      <div className="masthead-main">
        <Link to="/" className="masthead-brand">
          <span className="brand-cn">番组手账</span>
          <span className="brand-en">ANIMETRACKER</span>
        </Link>
        <nav className="masthead-nav">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={isActive(item.path) ? 'active' : ''}
            >
              <span className="nav-index">{item.index}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <Input.Search
          className="masthead-search"
          placeholder="搜索番剧..."
          value={searchValue}
          onChange={e => setSearchValue(e.target.value)}
          onSearch={onSearch}
        />
        {isLoggedIn ? (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space className="masthead-user" style={{ cursor: 'pointer' }}>
              <Avatar src={user?.avatar} icon={<UserOutlined />} />
              <span>{user?.nickname || user?.username}</span>
            </Space>
          </Dropdown>
        ) : (
          <Button type="primary" onClick={() => navigate('/login')}>登录</Button>
        )}
      </div>
    </AntHeader>
  );
}
