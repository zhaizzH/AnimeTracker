import Link from 'next/link';
import { copy } from '@/content/zh-CN';
import { SearchForm } from '@/components/search/search-form';
import { MobileNav } from '@/components/shell/mobile-nav';
import { UserMenu } from '@/components/shell/user-menu';
import styles from './site-header.module.css';

/**
 * 响应式应用外壳：桌面与移动共用同一棵路由树，
 * 展示差异完全由 CSS 媒体查询控制。
 */
export function SiteHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link className={styles.brand} href="/">
          {copy.brand}
        </Link>

        <nav className={styles.nav} aria-label={copy.navigation.primary}>
          <Link href="/">{copy.navigation.home}</Link>
          <Link href="/schedule">{copy.navigation.schedule}</Link>
        </nav>

        <div className={styles.desktopSearch}>
          <SearchForm />
        </div>

        {/* 移动端搜索入口：<details> 展开后露出紧凑搜索条，无需 JS */}
        <details className={styles.mobileSearch}>
          <summary className={styles.menuTrigger}>{copy.search.trigger}</summary>
          <SearchForm compact />
        </details>

        <UserMenu />
      </div>

      <MobileNav />
    </header>
  );
}
