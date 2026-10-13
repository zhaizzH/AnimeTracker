import { createContext, useContext, type ReactNode } from 'react';
import { BarChart3Icon, CalendarDaysIcon, LayoutGridIcon, MessageSquareIcon, UserIcon } from 'lucide-react';

export type NavItem = {
  title: string;
  path?: string;
  icon?: ReactNode;
};

// 顶栏公开入口（匿名与登录均可见）。
export const publicNavItems: NavItem[] = [
  { title: '首页', path: '/', icon: <LayoutGridIcon /> },
  { title: '每周日程', path: '/schedule', icon: <CalendarDaysIcon /> },
  { title: '番剧索引', path: '/anime', icon: <BarChart3Icon /> },
];

// 登录后的个人入口，收进头像菜单与移动抽屉。
export const memberNavItems: NavItem[] = [
  { title: '我的追番', path: '/my-collections', icon: <LayoutGridIcon /> },
  { title: 'AI 助手', path: '/agent', icon: <MessageSquareIcon /> },
  { title: '个人中心', path: '/profile', icon: <UserIcon /> },
];

// 导航项激活判定：冗余的尾斜杠视为同一路径（`/agent/` 与 `/agent`）。
export function isNavItemActive(pathname: string, path?: string): boolean {
  if (!path) return false;
  const normalize = (p: string) => (p.length > 1 ? p.replace(/\/+$/, '') : p);
  const current = normalize(pathname);
  const target = normalize(path);
  if (target === '/') return current === '/';
  return current === target || current.startsWith(`${target}/`);
}

/** 由 AppShell 提供，使顶栏能感知当前路径，而无需假设 Router 存在。 */
export const AppPathContext = createContext<string>('');
export const useAppPath = () => useContext(AppPathContext);

/** 由 AppShell 提供，使顶栏的账号菜单能读取当前登录用户。 */
export type ShellUser = { username?: string; nickname?: string | null } | null;
export const ShellUserContext = createContext<ShellUser>(null);
export const useShellUser = () => useContext(ShellUserContext);
