/** 详情页纯逻辑：路由 id 归一化与元数据描述截断，独立成模块以便无后端单测。 */

const EXCERPT_MAX = 150;

/**
 * 解析路由 id：非正整数/非整数返回 NaN（路由据此 404）。
 */
export function parseSubjectId(raw: string): number {
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : NaN;
}

/**
 * 把简介截断到约 150 字符附近的句子边界；未超限则原样返回（含末位省略号）。
 */
export function detailExcerpt(summary: string): string {
  const trimmed = summary.trim();
  if (trimmed.length <= EXCERPT_MAX) return trimmed;
  const cut = trimmed.slice(0, EXCERPT_MAX);
  const lastBreak = Math.max(cut.lastIndexOf('。'), cut.lastIndexOf('！'), cut.lastIndexOf('？'), cut.lastIndexOf('…'));
  const index = lastBreak > EXCERPT_MAX * 0.5 ? lastBreak + 1 : EXCERPT_MAX;
  return `${trimmed.slice(0, index)}…`;
}
