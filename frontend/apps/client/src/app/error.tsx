'use client';

import { copy } from '@/content/zh-CN';
import { ErrorState } from '@/components/feedback/error-state';

/**
 * 路由级错误边界：公开页绝不允许 500，兜底展示安全错误态并允许重试。
 * 与公共适配器共用同一套诊断泄漏过滤器：堆栈痕迹（java.lang./Traceback/ at top.）
 * 一律替换为通用兜底文案，绝不把后端内部信息下发给公开页面。
 */
const UNSAFE_MESSAGE_RE = /java\.lang\.|Traceback| at top\./;

export default function RouteError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const message = error.message && !UNSAFE_MESSAGE_RE.test(error.message) ? error.message : copy.error.unsafeFallback;
  return (
    <main id="main" style={{ padding: 'var(--space-6) var(--space-4)' }}>
      <ErrorState message={message} />
      <button onClick={reset}>{copy.common.retry}</button>
    </main>
  );
}
