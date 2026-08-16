import { SubjectGridSkeleton } from '@/components/feedback/subject-grid-skeleton';
import styles from '@/features/subjects/subject-detail.module.css';

/** 详情页流式渲染占位：标题区骨架。 */
export default function Loading() {
  return (
    <main className={styles.page}>
      <SubjectGridSkeleton count={1} />
    </main>
  );
}
