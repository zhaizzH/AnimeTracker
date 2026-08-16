import { EmptyState } from '@/components/feedback/empty-state';
import { copy } from '@/content/zh-CN';

/** 未找到该番剧：返回全局布局，正文展示空态提示。 */
export default function NotFound() {
  return (
    <main id="main" style={{ padding: 'var(--space-6) var(--space-4)' }}>
      <EmptyState message={copy.common.empty} />
    </main>
  );
}
