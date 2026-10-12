import { useNavigate } from 'react-router-dom';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { UserIcon, LayoutGridIcon, LogOutIcon } from 'lucide-react';
import { authApi, completeLogout, useAuthStore } from '@shared';
import { toast } from 'sonner';

export function NavUser() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const displayName = user?.nickname ?? user?.username ?? '用户';
  const initial = displayName.slice(0, 1);

  const onLogout = async () => {
    if (await completeLogout(authApi.logout)) navigate('/login');
    else toast.error('退出失败，请重试');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={`账号菜单：${displayName}`}
          className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Avatar className="size-8">
            <AvatarImage src="" alt="" />
            <AvatarFallback>{initial}</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="pointer-events-none flex items-center gap-2">
            <Avatar className="isolate size-8">
              <AvatarFallback>{initial}</AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <span className="font-medium text-foreground">{displayName}</span>
            </div>
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem onSelect={() => navigate('/profile')}>
            <UserIcon />
            个人中心
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => navigate('/my-collections')}>
            <LayoutGridIcon />
            我的追番
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem variant="destructive" onSelect={() => void onLogout()}>
            <LogOutIcon />
            退出登录
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
