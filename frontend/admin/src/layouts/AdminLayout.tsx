import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { authApi, completeLogout } from '@shared';
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage } from '@/components/ui/breadcrumb';
import { Separator } from '@/components/ui/separator';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar, ADMIN_NAV_ITEMS } from '@/components/app-sidebar';
import { NavUser } from '@/components/nav-user';
import { ThemeBridge } from '@/components/theme-bridge';
import { ThemeSwitcher } from '@/components/theme-switcher';
import { toastError } from '@/lib/toast';

export function AdminLayout() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const currentLabel = ADMIN_NAV_ITEMS.find((item) => item.path === pathname)?.label;

  const onLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      if (await completeLogout(authApi.logout)) navigate('/admin/login');
      else toastError('退出失败，请重试');
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <SidebarProvider>
      <ThemeBridge />
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem><BreadcrumbPage>{currentLabel ?? '管理后台'}</BreadcrumbPage></BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <div className="ml-auto flex items-center gap-1">
            <ThemeSwitcher />
            <NavUser isLoggingOut={isLoggingOut} onLogout={() => void onLogout()} />
          </div>
        </header>
        <div className="min-w-0 flex-1 p-4 md:p-6"><Outlet /></div>
      </SidebarInset>
    </SidebarProvider>
  );
}
