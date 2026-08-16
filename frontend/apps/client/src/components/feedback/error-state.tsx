import { copy } from '@/content/zh-CN';
import styles from './feedback.module.css';

export type ErrorStateProps = {
  /** 业务错误使用后端返回的 message */
  message: string;
  /** 可选的请求编号，便于排查 */
  requestId?: string;
  /** 可选的重试链接（如跳回发现页） */
  retryHref?: string;
};

/** 可复用的安全错误态：读屏可感知、可选展示 requestId 与重试入口。 */
export function ErrorState({ message, requestId, retryHref }: ErrorStateProps) {
  return (
    <section role="alert" className={styles.block}>
      <p className={styles.title}>{copy.common.error}</p>
      <p className={styles.message}>{message}</p>
      {requestId ? (
        <p className={styles.detail}>
          {copy.common.requestId}: {requestId}
        </p>
      ) : null}
      {retryHref ? (
        <p>
          <a className={styles.retry} href={retryHref}>
            {copy.common.retry}
          </a>
        </p>
      ) : null}
    </section>
  );
}
