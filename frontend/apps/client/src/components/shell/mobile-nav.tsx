import Link from 'next/link';
import { copy } from '@/content/zh-CN';
import styles from './site-header.module.css';

/**
 * 移动端底部主导航：只保留首页与放送时间表。
 */
export function MobileNav() {
  return (
    <nav className={styles.mobileNav} aria-label={copy.navigation.mobile}>
      <Link href="/">{copy.navigation.home}</Link>
      <Link href="/schedule">{copy.navigation.schedule}</Link>
    </nav>
  );
}
