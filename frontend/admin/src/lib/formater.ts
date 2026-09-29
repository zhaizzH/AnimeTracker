/** 看板数字格式化：统一 zh-CN 分组，避免各处重复 Intl 配置。 */
const INTEGER = new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 });

export function formatInteger(value: number) {
  return INTEGER.format(value);
}

/** 图表 X 轴：≤7 天显示星期，否则显示月/日。 */
export function formatChartAxisTick(isoDate: string, periodDays: number) {
  const date = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return periodDays <= 7
    ? date.toLocaleDateString('zh-CN', { weekday: 'short' })
    : date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

/** 图表 tooltip 标签：月/日。 */
export function formatChartTooltipDate(isoDate: string) {
  const date = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}
