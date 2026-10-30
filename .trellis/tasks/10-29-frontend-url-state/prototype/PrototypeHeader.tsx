// 顶栏：结构、尺寸、类名与生产 app-header.tsx 对齐（原型只保留形状，不接导航）。
import { ChevronDownIcon } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Separator } from '@/components/ui/separator';

const NAV = [
  { title: '首页', view: 'home' },
  { title: '每周日程', view: 'schedule' },
  { title: '番剧索引', view: 'anime' },
] as const;

export function PrototypeHeader({
  view,
  compact,
  onNavigate,
}: {
  view: string;
  /** 手机外框内模拟 <768px：隐藏导航项，与生产 md: 行为一致 */
  compact?: boolean;
  onNavigate: (v: 'anime' | 'collections') => void;
}) {
  return (
    <header className="sticky top-0 z-50 h-14 w-full border-b bg-background/95 backdrop-blur-sm">
      <nav className="mx-auto flex h-14 w-full max-w-[1400px] items-center justify-between gap-2 px-4 md:px-6">
        <div className="flex items-center gap-2">
          <span className="rounded-md px-1 text-sm font-semibold tracking-tight">AnimeTracker</span>
          <Separator className="h-4 data-[orientation=vertical]:self-center" orientation="vertical" />
          <div className={compact ? 'hidden' : 'flex items-center gap-1'}>
            {NAV.map((item) => (
              <Button
                key={item.title}
                size="sm"
                variant={view === item.view ? 'secondary' : 'ghost'}
                onClick={() => item.view === 'anime' && onNavigate('anime')}
              >
                {item.title}
              </Button>
            ))}
            <Button size="sm" variant={view === 'collections' ? 'secondary' : 'ghost'} onClick={() => onNavigate('collections')}>
              我的收藏
            </Button>
          </div>
        </div>
        <div className={compact ? 'flex items-center gap-1' : 'hidden'}>
          <Button size="sm" variant="ghost">菜单</Button>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button type="button" aria-label="账号菜单：zhaizzH" className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="size-8">
                <AvatarFallback>Z</AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel className="flex items-center justify-between">
              zhaizzH
              <ChevronDownIcon className="size-3 text-muted-foreground" />
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => onNavigate('collections')}>我的追番</DropdownMenuItem>
            <DropdownMenuItem>个人中心</DropdownMenuItem>
            <DropdownMenuItem>退出登录</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </nav>
    </header>
  );
}
