import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Logo } from '@/components/logo';
import { NavUser } from '@/components/nav-user';
import { MobileNav } from '@/components/mobile-nav';
import { ThemeSwitcher } from '@/components/theme-switcher';
import { isNavItemActive, publicNavItems, useAppPath, useShellUser } from '@/components/app-shared';
import { useScroll } from '@/hooks/use-scroll';
import { Link, useNavigate } from 'react-router-dom';
import { SearchIcon } from 'lucide-react';

export function AppHeader() {
  const path = useAppPath();
  const user = useShellUser();
  const scrolled = useScroll(10);
  const navigate = useNavigate();

  return (
    <header
      className={cn(
        'sticky top-0 z-50 w-full border-b border-transparent',
        scrolled && 'border-border bg-background/95 backdrop-blur-sm supports-backdrop-filter:bg-background/50',
      )}
    >
      <nav className="mx-auto flex h-14 w-full max-w-[1400px] items-center justify-between gap-2 px-4 md:px-6">
        <div className="flex items-center gap-2">
          <Link to="/" aria-label="AnimeTracker 首页" className="rounded-md p-1 hover:bg-muted dark:hover:bg-muted/50">
            <Logo className="h-4" />
          </Link>
          <Separator className="h-4 data-[orientation=vertical]:self-center" orientation="vertical" />
          <div className="hidden items-center gap-1 md:flex">
            {publicNavItems.map((item) => (
              <Button
                asChild
                key={item.title}
                size="sm"
                variant={isNavItemActive(path, item.path) ? 'secondary' : 'ghost'}
              >
                <Link to={item.path ?? '/'}>{item.title}</Link>
              </Button>
            ))}
          </div>
        </div>
        <div className="hidden items-center gap-2 md:flex">
          <form
            className="relative"
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
        <MobileNav />
      </nav>
    </header>
  );
}
