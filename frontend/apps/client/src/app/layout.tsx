import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';
import { ThemeScript } from '@/components/theme/theme-script';
import { SiteHeader } from '@/components/shell/site-header';
import './globals.css';

export const metadata: Metadata = {
  title: copy.brand,
  description: copy.home.tagline,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <ThemeScript />
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
