import { copy } from '@/content/zh-CN';
import { SubjectGridSkeleton } from '@/components/feedback/subject-grid-skeleton';
import styles from '@/features/schedule/schedule-view.module.css';

/** 时间表流式渲染占位：标题 + 骨架。 */
export default function Loading() {
  return (
    <main id="main" className={styles.page}>
      <h1 className={styles.title}>{copy.schedule.title}</h1>
      <SubjectGridSkeleton count={7} />
    </main>
  );
}
