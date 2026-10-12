import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { DecorIcon } from '@/components/decor-icon';
import { AppBreadcrumbs } from '@/components/app-breadcrumbs';
import { CustomSidebarTrigger } from '@/components/custom-sidebar-trigger';
import { NavUser } from '@/components/nav-user';
import { ThemeSwitcher } from '@/components/theme-switcher';
import { useAppPath, titleForPath } from '@/components/app-shared';
import { useShellUser } from '@/components/app-shared';
import { Link, useNavigate } from 'react-router-dom';
import { SearchIcon } from 'lucide-react';

export function AppHeader() {
  const path = useAppPath();
  const user = useShellUser();
  const navigate = useNavigate();
  const title = titleForPath(path);

  return (
    <header
      className={cn(
        'sticky top-0 z-50 flex h-14 shrink-0 items-center justify-between gap-2 border-b px-4 md:px-6',
        'bg-background/95 backdrop-blur-sm supports-backdrop-filter:bg-background/50',
      )}
    >
      <DecorIcon className="hidden md:block" position="bottom-left" />
      <div className="flex items-center gap-3">
        <CustomSidebarTrigger />
        <Separator className="mr-2 h-4 data-[orientation=vertical]:self-center" orientation="vertical" />
        <AppBreadcrumbs page={title ? { title } : null} />
      </div>
      <div className="flex items-center gap-2">
        <form
          className="relative hidden md:block"
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            const value = new FormData(event.currentTarget).get('q');
            const q = typeof value === 'string' ? value.trim() : '';
            if (q) navigate(`/anime?q=${encodeURIComponent(q)}`);
          }}
        >
          <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input name="q" type="search" aria-label="搜索番剧" placeholder="搜索番剧" className="w-56 pl-8" />
        </form>
        <ThemeSwitcher />
        <Separator className="h-4 data-[orientation=vertical]:self-center" orientation="vertical" />
        {user ? (
          <NavUser />
        ) : (
          <Button asChild size="sm" variant="outline">
            <Link to="/login">登录</Link>
          </Button>
        )}
      </div>
    </header>
  );
}
