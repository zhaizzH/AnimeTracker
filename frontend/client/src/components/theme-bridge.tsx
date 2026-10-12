import { useEffect, useState } from 'react';
import { resolveMode, useThemeStore } from '@shared';

export function useResolvedTheme() {
  const mode = useThemeStore((state) => state.mode);
  const followSystem = useThemeStore((state) => state.followSystem);
  const [resolved, setResolved] = useState(() => resolveMode(mode, followSystem));

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    const apply = () => setResolved(resolveMode(mode, followSystem));
    apply();

    if (!followSystem || !media) return undefined;
    if (media.addEventListener) media.addEventListener('change', apply);
    else media.addListener(apply);
    return () => {
      if (media.removeEventListener) media.removeEventListener('change', apply);
      else media.removeListener(apply);
    };
  }, [mode, followSystem]);

  return resolved;
}

export function ThemeBridge() {
  const resolved = useResolvedTheme();

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', resolved === 'dark');
    root.style.colorScheme = resolved;
    // 移动端地址栏取色跟随主题（shadcn neutral 的 background 取值）。
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.setAttribute('content', resolved === 'dark' ? '#0A0A0A' : '#FFFFFF');
  }, [resolved]);

  return null;
}
