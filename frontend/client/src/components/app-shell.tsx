import { cn } from '@/lib/utils';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { AppHeader } from '@/components/app-header';
import { AppSidebar } from '@/components/app-sidebar';
import { AppPathContext, ShellUserContext, type ShellUser } from '@/components/app-shared';

/**
 * 应用外壳。不直接依赖 react-router，便于在测试与不同路由形态下复用；
 * 由 `path` / `user` 注入路由与登录态。
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
        <SidebarProvider className={cn('[--app-wrapper-max-width:80rem]')}>
          <AppSidebar />
          <SidebarInset>
            <AppHeader />
            <div className={cn('flex flex-1 flex-col p-4 md:p-6', 'mx-auto w-full max-w-(--app-wrapper-max-width)')}>
              {children}
            </div>
          </SidebarInset>
        </SidebarProvider>
      </AppPathContext.Provider>
    </ShellUserContext.Provider>
  );
}
