import { Clapperboard, Home } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from '@/components/ui/empty';

/**
 * 管理端 404 页。与用户端同款版式，但跳转目标是管理端路由（不带 `/admin` 前缀）。
 * 路由表中 `*` 指向本页，因此只在未匹配任何管理页时渲染，不会叠加 AdminLayout。
 */
export default function NotFound() {
  return (
    <div className="relative flex min-h-[70vh] w-full items-center justify-center overflow-hidden">
      <Empty>
        <EmptyHeader>
          <EmptyTitle className="mask-b-from-20% mask-b-to-80% text-9xl font-extrabold">
            404
          </EmptyTitle>
          <EmptyDescription className="-mt-8 text-nowrap text-foreground/80">
            你要找的页面可能已被移动或不存在。
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <div className="flex gap-2">
            <Button asChild>
              <Link to="/dashboard">
                <Home data-icon="inline-start" />
                返回面板
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/subjects">
                <Clapperboard data-icon="inline-start" />
                番剧管理
              </Link>
            </Button>
          </div>
        </EmptyContent>
      </Empty>
    </div>
  );
}
