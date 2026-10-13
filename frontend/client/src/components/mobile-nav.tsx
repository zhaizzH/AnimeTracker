import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Portal, PortalBackdrop } from '@/components/portal';
import { memberNavItems, publicNavItems, useShellUser } from '@/components/app-shared';
import { authApi, completeLogout } from '@shared';
import { toast } from 'sonner';
import { XIcon, MenuIcon } from 'lucide-react';

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const user = useShellUser();
  const navigate = useNavigate();

  const onLogout = async () => {
    setOpen(false);
    if (await completeLogout(authApi.logout)) navigate('/login');
    else toast.error('退出失败，请重试');
  };

  return (
    <div className="md:hidden">
      <Button
        aria-controls="mobile-menu"
        aria-expanded={open}
        aria-label="切换菜单"
        size="icon"
        variant="outline"
        onClick={() => setOpen(!open)}
      >
        {open ? <XIcon className="size-4.5" /> : <MenuIcon className="size-4.5" />}
      </Button>
      {open && (
        <Portal className="top-14" id="mobile-menu">
          <PortalBackdrop />
          <div
            className={cn(
              'data-[slot=open]:zoom-in-97 ease-out data-[slot=open]:animate-in',
              'size-full p-4',
            )}
            data-slot={open ? 'open' : 'closed'}
          >
            <div className="grid gap-y-2">
              {publicNavItems.map((item) => (
                <Button asChild className="justify-start" key={item.title} variant="ghost">
                  <Link onClick={() => setOpen(false)} to={item.path ?? '/'}>
                    {item.icon}
                    {item.title}
                  </Link>
                </Button>
              ))}
              {user &&
                memberNavItems.map((item) => (
                  <Button asChild className="justify-start" key={item.title} variant="ghost">
                    <Link onClick={() => setOpen(false)} to={item.path ?? '/'}>
                      {item.icon}
                      {item.title}
                    </Link>
                  </Button>
                ))}
            </div>
            <div className="mt-12 flex flex-col gap-2">
              {user ? (
                <Button className="w-full" variant="outline" onClick={() => void onLogout()}>
                  退出登录
                </Button>
              ) : (
                <Button asChild className="w-full" variant="outline">
                  <Link onClick={() => setOpen(false)} to="/login">
                    登录
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </Portal>
      )}
    </div>
  );
}
