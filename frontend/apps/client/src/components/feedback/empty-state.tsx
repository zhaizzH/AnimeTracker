import { copy } from '@/content/zh-CN';
import styles from './feedback.module.css';

export type EmptyStateProps = {
  message?: string;
};

/** 空态：列表无内容时展示的温和提示。 */
export function EmptyState({ message = copy.common.empty }: EmptyStateProps) {
  return (
    <section className={styles.block}>
      <p>{message}</p>
    </section>
  );
}
