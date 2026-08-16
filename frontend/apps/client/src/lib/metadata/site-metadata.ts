import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';

/** 站点根地址（去掉尾部斜杠），来自 NEXT_PUBLIC_SITE_URL；未配置时为空串。 */
export function getSiteUrl(): string {
  return (process.env.NEXT_PUBLIC_SITE_URL ?? '').replace(/\/+$/, '');
}

/** 拼接绝对 URL：base 去掉尾部斜杠，path 补前导斜杠。 */
export function buildCanonicalUrl(base: string, path: string): string {
  const baseUrl = base.replace(/\/+$/, '');
  const pathname = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${pathname}`;
}

/** 未配置站点根地址时省略 canonical，避免输出无效的相对 canonical。 */
export function canonicalMeta(path: string): Pick<Metadata, 'alternates'> {
  const siteUrl = getSiteUrl();
  return siteUrl ? { alternates: { canonical: buildCanonicalUrl(siteUrl, path) } } : {};
}

/** 全局默认 metadata：标题、描述、Open Graph 默认值与站点根地址 canonical。 */
export function baseMetadata(): Metadata {
  const siteUrl = getSiteUrl();
  return {
    title: copy.brand,
    description: copy.home.tagline,
    openGraph: {
      siteName: copy.brand,
      title: copy.brand,
      description: copy.home.tagline,
      type: 'website',
    },
    twitter: {
      card: 'summary',
      title: copy.brand,
      description: copy.home.tagline,
    },
    ...(siteUrl ? { metadataBase: new URL(siteUrl) } : {}),
    ...canonicalMeta('/'),
  };
}
