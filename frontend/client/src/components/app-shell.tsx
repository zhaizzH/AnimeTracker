import { AppHeader } from '@/components/app-header';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AppPathContext, ShellUserContext, type ShellUser } from '@/components/app-shared';

/**
 * 应用外壳。不直接依赖 react-router，便于在测试与不同路由形态下复用；
 * 由 `path` / `user` 注入路由与登录态。外壳只提供吸顶顶栏与布局栈，
 * 页面容器（宽度与内边距）由各页面自持。
 *
 * `TooltipProvider` 挂在根部：原 `SidebarProvider` 曾隐式提供，去侧栏后需显式补回，
 * 供全局悬浮 AI 助手等外壳内组件使用。
 */
export function AppShell({
  children,
  path = '',
  user = null,
}: {
  children: React.ReactNode;
  path?: string;
  user?: ShellUser;
}) {
  return (
    <ShellUserContext.Provider value={user}>
      <AppPathContext.Provider value={path}>
        <TooltipProvider delayDuration={0}>
          <div className="flex min-h-svh w-full flex-col">
            <AppHeader />
            {children}
          </div>
        </TooltipProvider>
      </AppPathContext.Provider>
    </ShellUserContext.Provider>
  );
}
