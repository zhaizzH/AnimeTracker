import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { App, Button, Tooltip } from 'antd';
import {
  DashboardOutlined,
  FileSearchOutlined,
  ImportOutlined,
  LogoutOutlined,
  PlaySquareOutlined,
  ReloadOutlined,
  RobotOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAuthStore } from '../store/authStore';
import ThemeToggle from '../components/ThemeToggle';

interface NavItem {
  key: string;
  label: string;
  index: string;
  icon: ReactNode;
}

const navItems: NavItem[] = [
  { key: 'dashboard', label: '仪表盘', index: '01', icon: <DashboardOutlined /> },
  { key: 'subjects', label: '番剧管理', index: '02', icon: <PlaySquareOutlined /> },
  { key: 'users', label: '用户管理', index: '03', icon: <TeamOutlined /> },
  { key: 'import', label: '数据导入', index: '04', icon: <ImportOutlined /> },
  { key: 'logs', label: '操作日志', index: '05', icon: <FileSearchOutlined /> },
  { key: 'agent', label: 'Agent 配置', index: '06', icon: <RobotOutlined /> },
];

const titleMap: Record<string, string> = {
  dashboard: '总览',
  subjects: '番剧管理',
  users: '用户管理',
  import: '数据导入',
  logs: '操作日志',
  agent: 'Agent 配置',
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const username = useAuthStore((s) => s.username);
  const signOut = useAuthStore((s) => s.signOut);
  const [now, setNow] = useState(dayjs());
  const [syncing, setSyncing] = useState(false);
  const active = location.pathname.replace('/', '') || 'dashboard';

  useEffect(() => {
    const timer = setInterval(() => setNow(dayjs()), 1000);
    return () => clearInterval(timer);
  }, []);

  const openNav = (item: NavItem) => {
    navigate(`/${item.key}`);
  };

  const sync = () => {
    setSyncing(true);
    setTimeout(() => {
      setSyncing(false);
      message.success('数据已刷新');
    }, 700);
  };

  const logout = () => {
    signOut();
    navigate('/login');
  };

  const initial = username?.slice(0, 1).toUpperCase() ?? 'A';

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="sidebar-brand">
          <span className="sidebar-brand-mark">AT</span>
          <div>
            <div className="sidebar-brand-name">ANIMETRACKER</div>
          <div className="sidebar-brand-sub">管理端</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <div
              key={item.key}
              className={`nav-item${active === item.key ? ' active' : ''}`}
              onClick={() => openNav(item)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') openNav(item);
              }}
              role="button"
              tabIndex={0}
            >
              <span className="nav-index">{item.index}</span>
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </div>
          ))}
        </nav>
      </aside>
      <div className="admin-main">
        <header className="admin-header">
          <div className="admin-header-title">
            <h2>{titleMap[active] ?? '总览'}</h2>
            <span className="crumb">{titleMap[active] ?? '总览'}</span>
          </div>
          <div className="admin-header-right">
            <span className="header-status">
              <span className="status-dot" />
            </span>
            <span className="header-clock">{now.format('YYYY-MM-DD HH:mm:ss')}</span>
            <ThemeToggle />
            <Tooltip title="刷新数据">
              <Button type="text" icon={<ReloadOutlined spin={syncing} />} onClick={sync} />
            </Tooltip>
            <div className="header-user">
              <span className="foot-avatar">{initial}</span>
              {username ?? 'admin'}
            </div>
            <Tooltip title="退出登录">
              <Button type="text" icon={<LogoutOutlined />} onClick={logout} />
            </Tooltip>
          </div>
        </header>
        <main className="admin-content">{children}</main>
      </div>
    </div>
  );
}
