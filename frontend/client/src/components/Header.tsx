import { useState } from 'react';
import { Layout, Input, Button, Dropdown, Avatar, Space } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth';

const { Header: AntHeader } = Layout;

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

  const navItems = [
    { path: '/', label: '首页' },
    { path: '/schedule', label: '每周日程' },
    { path: '/anime', label: '番剧索引' },
  ];

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心', onClick: () => navigate('/profile') },
    { key: 'agent', label: 'AI 助手', onClick: () => navigate('/agent') },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout },
  ];

  return (
    <AntHeader style={{ display: 'flex', alignItems: 'center', padding: '0 24px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
      <Link to="/" style={{ fontWeight: 'bold', fontSize: 18, marginRight: 24, color: 'inherit', whiteSpace: 'nowrap' }}>
        AnimeTracker
      </Link>
      <Space size="middle" style={{ flex: 1 }}>
        {navItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            style={{ color: location.pathname === item.path ? '#1677ff' : '#666' }}
          >
            {item.label}
          </Link>
        ))}
      </Space>
      <Input.Search
        placeholder="搜索番剧..."
        value={searchValue}
        onChange={e => setSearchValue(e.target.value)}
        onSearch={onSearch}
        style={{ maxWidth: 240, marginRight: 16 }}
      />
      {isLoggedIn ? (
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Avatar src={user?.avatar} icon={<UserOutlined />} />
            <span>{user?.nickname || user?.username}</span>
          </Space>
        </Dropdown>
      ) : (
        <Button type="primary" onClick={() => navigate('/login')}>登录</Button>
      )}
    </AntHeader>
  );
}
