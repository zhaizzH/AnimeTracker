import { useEffect, useState } from 'react';
import { resolveMode, useThemeStore } from '@shared';

export function useResolvedAdminTheme() {
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
  const resolved = useResolvedAdminTheme();

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', resolved === 'dark');
    root.style.colorScheme = resolved;
  }, [resolved]);

  return null;
}
