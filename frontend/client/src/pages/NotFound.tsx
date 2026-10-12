import { Compass, Home } from 'lucide-react';
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
 * 404 页。挂在两处：ClientLayout 内（保留侧栏/顶栏外壳）与 AuthShell 内（未登录时进入），
 * 因此高度用视口比例而非 min-h-screen，避免叠加外壳后溢出导致滚动条。
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
              <Link to="/">
                <Home data-icon="inline-start" />
                返回首页
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/anime">
                <Compass data-icon="inline-start" />
                浏览番剧
              </Link>
            </Button>
          </div>
        </EmptyContent>
      </Empty>
    </div>
  );
}
