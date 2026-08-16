import { SiteHeader } from '@/components/shell/site-header';
import { copy } from '@/content/zh-CN';

/**
 * 公开应用外壳的测试夹具：与根布局同构（跳过链接 + 顶栏 + 正文 main）。
 * 供无障碍扫描使用，必须始终无 axe 违规。
 */
export function TestPublicShell() {
  return (
    <>
      <a className="skip-link" href="#main">
        {copy.a11y.skipToContent}
      </a>
      <SiteHeader />
      <main id="main">
        <h1>{copy.brand}</h1>
        <p>{copy.home.tagline}</p>
      </main>
    </>
  );
}
