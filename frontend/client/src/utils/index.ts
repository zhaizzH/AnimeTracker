/** 获取当前季度 */
export function getCurrentQuarter(): string {
  const m = new Date().getMonth();
  if (m < 3) return 'spring';
  if (m < 6) return 'summer';
  if (m < 9) return 'autumn';
  return 'winter';
}

/** 收藏类型中文名 */
export const COLLECTION_TYPE_LABELS: Record<number, string> = {
  1: '想看',
  2: '看过',
  3: '在看',
  4: '搁置',
  5: '抛弃',
};
