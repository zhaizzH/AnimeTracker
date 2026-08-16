import { copy } from '@/content/zh-CN';
import styles from './feedback.module.css';

export type SubjectGridSkeletonProps = {
  count?: number;
};

/** 番剧网格加载骨架：占位卡片数可配，读屏以 status 区域提示加载中。 */
export function SubjectGridSkeleton({ count = 8 }: SubjectGridSkeletonProps) {
  return (
    <div className={styles.grid} role="status" aria-label={copy.common.loading}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={styles.skeleton} aria-hidden="true" />
      ))}
    </div>
  );
}
