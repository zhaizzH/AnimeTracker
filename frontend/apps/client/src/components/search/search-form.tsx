import { copy } from '@/content/zh-CN';
import styles from './search-form.module.css';

export type SearchFormProps = {
  initialQuery?: string;
  compact?: boolean;
};

/**
 * 常驻搜索表单：GET 提交到 /discover，无需客户端 JS 即可工作。
 */
export function SearchForm({ initialQuery = '', compact = false }: SearchFormProps) {
  return (
    <form role="search" action="/discover" method="get" className={compact ? styles.compact : styles.form}>
      <input
        className={styles.input}
        type="text"
        inputMode="search"
        name="q"
        aria-label={copy.search.label}
        placeholder={copy.search.placeholder}
        defaultValue={initialQuery}
      />
      <button className={styles.submit} type="submit">
        {copy.search.submit}
      </button>
    </form>
  );
}
