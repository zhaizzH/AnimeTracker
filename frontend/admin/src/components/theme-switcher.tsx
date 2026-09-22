import { Monitor, Moon, Sun } from 'lucide-react';
import { useThemeStore } from '@shared';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useResolvedAdminTheme } from './theme-bridge';

export function ThemeSwitcher() {
  const mode = useThemeStore((state) => state.mode);
  const followSystem = useThemeStore((state) => state.followSystem);
  const setMode = useThemeStore((state) => state.setMode);
  const toggleFollowSystem = useThemeStore((state) => state.toggleFollowSystem);
  const resolved = useResolvedAdminTheme();
  const selected = followSystem ? 'system' : mode;

  const onThemeChange = (value: string) => {
    if (value === 'system') {
      if (!followSystem) toggleFollowSystem();
      return;
    }
    if (value === 'light' || value === 'dark') setMode(value);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label={resolved === 'dark' ? '当前深色模式' : '当前浅色模式'}
        className="inline-flex size-8 items-center justify-center rounded-md text-sm font-medium outline-none hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring"
      >
        {resolved === 'dark' ? <Moon /> : <Sun />}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>主题</DropdownMenuLabel>
        <DropdownMenuRadioGroup value={selected} onValueChange={onThemeChange}>
          <DropdownMenuRadioItem value="light"><Sun />浅色</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="dark"><Moon />深色</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="system"><Monitor />跟随系统</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
