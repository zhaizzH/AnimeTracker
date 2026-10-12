import {
  Bot,
  Clapperboard,
  LayoutDashboard,
  MessagesSquare,
  ScrollText,
  Upload,
  Users,
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';

// 管理端生产部署在独立端口 :8081 的站点根（见 docs/deploy/nginx/animetracker.conf），
// 路径不含 /admin 前缀；此处 path 同时用于导航跳转与 AdminLayout 的面包屑查找。
export const ADMIN_NAV_ITEMS = [
  { path: '/dashboard', label: '看板', icon: LayoutDashboard },
  { path: '/subjects', label: '番剧管理', icon: Clapperboard },
  { path: '/users', label: '用户管理', icon: Users },
  { path: '/import', label: '导入管理', icon: Upload },
  { path: '/logs', label: '日志审计', icon: ScrollText },
  { path: '/agent-config', label: 'Agent 配置', icon: Bot },
  { path: '/agent-chat', label: 'Agent 对话', icon: MessagesSquare },
] as const;

export function isAdminNavItemActive(pathname: string, path: string): boolean {
  return pathname === path;
}

export function AppSidebar() {
  const { pathname } = useLocation();

  return (
    <Sidebar variant="inset">
      <SidebarHeader>
        <Link className="flex items-center gap-2 rounded-md px-2 py-2 text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-ring" to="/dashboard">
          <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">A</span>
          <span>AnimeTracker 后台</span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>管理</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {ADMIN_NAV_ITEMS.map(({ path, label, icon: Icon }) => (
                <SidebarMenuItem key={path}>
                  <SidebarMenuButton asChild isActive={isAdminNavItemActive(pathname, path)} tooltip={label}>
                    <Link to={path} aria-current={pathname === path ? 'page' : undefined}>
                      <Icon />
                      <span>{label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
