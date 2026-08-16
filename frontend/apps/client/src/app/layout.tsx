import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';
import { ThemeScript } from '@/components/theme/theme-script';
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
        {children}
      </body>
    </html>
  );
}
