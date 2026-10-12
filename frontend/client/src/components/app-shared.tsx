import { createContext, useContext, type ReactNode } from 'react';
import { BarChart3Icon, CalendarDaysIcon, LayoutGridIcon, MessageSquareIcon, UserIcon } from 'lucide-react';

export type SidebarNavItem = {
  title: string;
  path?: string;
  icon?: ReactNode;
  isActive?: boolean;
  subItems?: SidebarNavItem[];
};

export type SidebarNavGroup = {
  label?: string;
  items: SidebarNavItem[];
};

// 匿名（未登录）可见的公开入口。
export const guestNavGroups: SidebarNavGroup[] = [
  {
    label: '浏览',
    items: [
      { title: '首页', path: '/', icon: <LayoutGridIcon /> },
      { title: '每周日程', path: '/schedule', icon: <CalendarDaysIcon /> },
      { title: '番剧索引', path: '/anime', icon: <BarChart3Icon /> },
    ],
  },
];

// 登录后追加的个人入口。
export const memberNavGroup: SidebarNavGroup = {
  label: '我的',
  items: [
    { title: '我的追番', path: '/my-collections', icon: <LayoutGridIcon /> },
    { title: 'AI 助手', path: '/agent', icon: <MessageSquareIcon /> },
    { title: '个人中心', path: '/profile', icon: <UserIcon /> },
  ],
};

export const footerNavLinks: SidebarNavItem[] = [];

// 当前路径 → 面包屑标题。
const PATH_TITLES: Array<[RegExp, string]> = [
  [/^\/$/, '首页'],
  [/^\/schedule/, '每周日程'],
  [/^\/anime/, '番剧索引'],
  [/^\/subject\//, '番剧详情'],
  [/^\/my-collections/, '我的追番'],
  [/^\/agent/, 'AI 助手'],
  [/^\/profile/, '个人中心'],
  [/^\/verify-email/, '邮箱验证'],
  [/^\/forgot-password/, '找回密码'],
  [/^\/reset-password/, '重置密码'],
];

export function titleForPath(pathname: string): string | undefined {
  return PATH_TITLES.find(([re]) => re.test(pathname))?.[1];
}

// 导航项激活判定：冗余的尾斜杠视为同一路径（`/agent/` 与 `/agent`）。
export function isNavItemActive(pathname: string, path?: string): boolean {
  if (!path) return false;
  const normalize = (p: string) => (p.length > 1 ? p.replace(/\/+$/, '') : p);
  const current = normalize(pathname);
  const target = normalize(path);
  if (target === '/') return current === '/';
  return current === target || current.startsWith(`${target}/`);
}

/** 由 AppContent 提供，使 header 的面包屑能感知当前路径，而无需假设 Router 存在。 */
export const AppPathContext = createContext<string>('');
export const useAppPath = () => useContext(AppPathContext);

/** 由 AppContent 提供，使 header 的账号菜单能读取当前登录用户。 */
export type ShellUser = { username?: string; nickname?: string | null } | null;
export const ShellUserContext = createContext<ShellUser>(null);
export const useShellUser = () => useContext(ShellUserContext);
