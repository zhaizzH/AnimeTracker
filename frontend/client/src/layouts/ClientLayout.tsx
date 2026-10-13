import { Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@shared';
import { AgentChatProvider } from '@/components/AgentChat';
import AIAssistantFloat from '@/components/AIAssistantFloat';
import { Footer } from '@/components/footer';
import { AppShell } from '@/components/app-shell';

// 对话页是全高布局（页面自持 calc(100vh-*)），页脚进入会撑出滚动条，故排除。
const FOOTERLESS_PATHS = new Set(['/agent']);

export function ClientLayout() {
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const showFooter = !FOOTERLESS_PATHS.has(location.pathname);
  return (
    <AgentChatProvider key={user?.id ?? 'anonymous'}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:bg-background focus:px-3 focus:py-2 focus:ring-2 focus:ring-ring"
      >
        跳到主内容
      </a>
      <AppShell path={location.pathname} user={user}>
        <main id="main" tabIndex={-1} className="flex-1 outline-none">
          <Outlet />
        </main>
        {showFooter && <Footer />}
        {user && <AIAssistantFloat />}
      </AppShell>
    </AgentChatProvider>
  );
}
