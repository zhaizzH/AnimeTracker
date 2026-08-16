import type { MetadataRoute } from 'next';
import { getSiteUrl } from '@/lib/metadata/site-metadata';

/** robots.txt：仅当配置了 NEXT_PUBLIC_SITE_URL 时才输出 sitemap 与 host。 */
export default function robots(): MetadataRoute.Robots {
  const siteUrl = getSiteUrl();
  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    ...(siteUrl ? { sitemap: `${siteUrl}/sitemap.xml`, host: siteUrl } : {}),
  };
}
