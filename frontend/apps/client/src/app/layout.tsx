import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';
import { baseMetadata } from '@/lib/metadata/site-metadata';
import { ThemeScript } from '@/components/theme/theme-script';
import { SiteHeader } from '@/components/shell/site-header';
import './globals.css';

export const metadata: Metadata = baseMetadata();

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <ThemeScript />
        <a className="skip-link" href="#main">
          {copy.a11y.skipToContent}
        </a>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
