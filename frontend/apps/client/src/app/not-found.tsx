import Link from 'next/link';
import { copy } from '@/content/zh-CN';

/** 全局 404：未知路由统一在此展示，提供返回首页的出口。 */
export default function NotFound() {
  return (
    <main id="main" style={{ padding: 'var(--space-6) var(--space-4)' }}>
      <h1>{copy.notFound.title}</h1>
      <p>{copy.notFound.message}</p>
      <p>
        <Link href="/">{copy.notFound.backHome}</Link>
      </p>
    </main>
  );
}
