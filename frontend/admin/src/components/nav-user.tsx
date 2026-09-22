import { LogOut, UserRound } from 'lucide-react';
import { useAuthStore } from '@shared';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface NavUserProps {
  isLoggingOut: boolean;
  onLogout: () => void;
}

export function NavUser({ isLoggingOut, onLogout }: NavUserProps) {
  const user = useAuthStore((state) => state.user);
  const username = user?.username ?? '';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-md p-1.5 text-left text-sm outline-none hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring" aria-label={`打开用户菜单：${username}`}>
          <Avatar size="sm"><AvatarFallback>{username.slice(0, 1).toUpperCase() || <UserRound />}</AvatarFallback></Avatar>
          <span className="hidden max-w-32 truncate sm:inline">{username}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel className="font-normal">
          <span className="block truncate">{username}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled={isLoggingOut} onSelect={(event) => {
          event.preventDefault();
          if (!isLoggingOut) onLogout();
        }}>
          <LogOut />
          {isLoggingOut ? '退出中…' : '退出'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
