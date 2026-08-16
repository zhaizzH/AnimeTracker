import Link from 'next/link';
import { copy } from '@/content/zh-CN';
import { ThemeToggle } from '@/components/theme/theme-toggle';
import styles from './site-header.module.css';

/**
 * 未登录用户菜单：<details> 无需 JS 即可展开。
 * 本阶段仅含登录与注册；追番等登录态入口在后续阶段加入。
 */
export function UserMenu() {
  return (
    <details className={styles.userMenu}>
      <summary className={styles.menuTrigger}>{copy.navigation.userMenu}</summary>
      <div className={styles.menuPanel}>
        <Link href="/auth/login">{copy.navigation.login}</Link>
        <Link href="/auth/register">{copy.navigation.register}</Link>
        <ThemeToggle />
      </div>
    </details>
  );
}
