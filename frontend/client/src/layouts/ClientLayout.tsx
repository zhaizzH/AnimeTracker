import { Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@shared';
import { AgentChatProvider } from '@/components/AgentChat';
import AIAssistantFloat from '@/components/AIAssistantFloat';
import { AppShell } from '@/components/app-shell';

export function ClientLayout() {
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  return (
    <AgentChatProvider key={user?.id ?? 'anonymous'}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:bg-background focus:px-3 focus:py-2 focus:ring-2 focus:ring-ring"
      >
        跳到主内容
      </a>
      <AppShell path={location.pathname} user={user}>
        <main id="main" tabIndex={-1} className="outline-none">
          <Outlet />
        </main>
        {user && <AIAssistantFloat />}
      </AppShell>
    </AgentChatProvider>
  );
}
