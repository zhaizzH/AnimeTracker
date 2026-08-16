import type { MetadataRoute } from 'next';
import { getPublicApi } from '@/lib/api/public-client';
import { buildCanonicalUrl, getSiteUrl } from '@/lib/metadata/site-metadata';

/**
 * sitemap.xml：静态公开路由 + 有界的热门番剧集合。
 * 绝不遍历全部分页番剧（只取第一页热门数据），避免单次请求放大后端负载。
 */
const SITEMAP_SUBJECT_LIMIT = 100;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const siteUrl = getSiteUrl();

  // 未配置站点根地址时无法生成绝对 URL，直接返回空 sitemap。
  if (!siteUrl) return [];

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: buildCanonicalUrl(siteUrl, '/'), changeFrequency: 'daily', priority: 1 },
    { url: buildCanonicalUrl(siteUrl, '/discover'), changeFrequency: 'daily', priority: 0.8 },
    { url: buildCanonicalUrl(siteUrl, '/schedule'), changeFrequency: 'daily', priority: 0.9 },
  ];

  let subjectRoutes: MetadataRoute.Sitemap = [];
  try {
    const page = await getPublicApi().listSubjects({ sort: 'score', order: 'desc', page: 1, size: SITEMAP_SUBJECT_LIMIT });
    const items = (page as unknown as { content?: Array<{ id?: number }> }).content ?? [];
    subjectRoutes = items
      .filter((item): item is { id: number } => typeof item.id === 'number' && Number.isInteger(item.id) && item.id > 0)
      .map((item) => ({
        url: buildCanonicalUrl(siteUrl, `/subjects/${item.id}`),
        changeFrequency: 'weekly' as const,
        priority: 0.6,
      }));
  } catch {
    // 后端不可用时仅输出静态路由：sitemap 绝不因上游失败而 500。
  }

  return [...staticRoutes, ...subjectRoutes];
}
