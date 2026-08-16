'use client';

import { copy } from '@/content/zh-CN';
import { ErrorState } from '@/components/feedback/error-state';

/**
 * 首页路由级错误边界：公开页绝不允许 500，兜底展示安全错误态并允许重试。
 * 各板块数据缺失已在 page.tsx 内以空态消化，这里只处理非预期异常。
 */
export default function Error({ reset }: { reset: () => void }) {
  return (
    <main style={{ padding: 'var(--space-6) var(--space-4)' }}>
      <ErrorState message={copy.home.loadError} />
      <button onClick={reset}>{copy.common.retry}</button>
    </main>
  );
}
