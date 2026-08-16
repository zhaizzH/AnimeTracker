import type { components } from '@animetracker/api-contract';
import { copy } from '@/content/zh-CN';

// 后端返回的番剧列表项 —— 直接复用生成的 OpenAPI schema 类型，不手写 DTO。
export type SubjectListItem = components['schemas']['条目列表视图（摘要信息）'];

export type SubjectCardModel = {
  id: number;
  title: string;
  originalTitle?: string;
  imageUrl?: string;
  scoreLabel: string;
  seasonLabel: string;
  episodeLabel: string;
  href: string;
};

/** 从播出日期推导季度标签，如 "2023 秋"；无法解析时返回 undefined。 */
export function seasonFromAirDate(airDate?: string): string | undefined {
  if (!airDate) return undefined;
  const year = airDate.slice(0, 4);
  const month = Number(airDate.slice(5, 7));
  if (!year || Number.isNaN(month) || month < 1 || month > 12) return undefined;
  const seasons = copy.subject.seasons;
  let index: number;
  if (month >= 3 && month <= 5) index = 1;
  else if (month >= 6 && month <= 8) index = 2;
  else if (month >= 9 && month <= 11) index = 3;
  else index = 0;
  return `${year} ${seasons[index]}`;
}

/** 后端空值统一在此处理，JSX 不做空值判断。 */
export function toSubjectCardModel(subject: SubjectListItem): SubjectCardModel {
  const { id, name, nameCn, image, score, eps, airDate } = subject;
  const title = nameCn || name || copy.common.notAvailable;
  const originalTitle = nameCn ? name : undefined;

  return {
    // 列表语境下后端必返回 id；此处兜底 0 仅为满足严格类型。
    id: id ?? 0,
    title,
    originalTitle,
    imageUrl: image || undefined,
    scoreLabel: score != null ? `${score} ${copy.subject.scoreUnit}` : copy.common.notAvailable,
    seasonLabel: seasonFromAirDate(airDate) ?? copy.common.notAvailable,
    episodeLabel:
      eps != null ? copy.subject.episodesAll.replace('{{total}}', String(eps)) : copy.common.notAvailable,
    href: `/subjects/${id}`,
  };
}
