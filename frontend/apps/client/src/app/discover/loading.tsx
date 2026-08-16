import { copy } from '@/content/zh-CN';
import { SubjectGridSkeleton } from '@/components/feedback/subject-grid-skeleton';
import styles from '@/features/discovery/discovery.module.css';

/** 发现页流式渲染占位：标题 + 骨架网格。 */
export default function Loading() {
  return (
    <main id="main" className={styles.page}>
      <h1 className={styles.title}>{copy.discovery.title}</h1>
      <SubjectGridSkeleton count={8} />
    </main>
  );
}
