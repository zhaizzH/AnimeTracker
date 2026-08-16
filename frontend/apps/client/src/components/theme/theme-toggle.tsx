'use client';

import { useEffect, useState } from 'react';
import { copy } from '@/content/zh-CN';

export type ThemeMode = 'light' | 'dark' | 'system';

const COOKIE = 'at-theme';
const COOKIE_OPTIONS = 'Path=/; SameSite=Lax; Max-Age=31536000';

function resolve(mode: ThemeMode): 'light' | 'dark' {
  if (mode !== 'system') return mode;
  return typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

function applyTheme(mode: ThemeMode) {
  document.documentElement.dataset.theme = resolve(mode);
  document.cookie = `${COOKIE}=${mode}; ${COOKIE_OPTIONS}`;
}

export function ThemeToggle({ initialMode = 'system' }: { initialMode?: ThemeMode }) {
  const [mode, setMode] = useState<ThemeMode>(initialMode);

  useEffect(() => {
    applyTheme(mode);
    if (mode !== 'system' || typeof window.matchMedia !== 'function') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => applyTheme('system');
    media.addEventListener?.('change', onChange);
    return () => media.removeEventListener?.('change', onChange);
  }, [mode]);

  return (
    <label>
      {copy.common.theme}
      <select value={mode} onChange={(e) => setMode(e.target.value as ThemeMode)}>
        <option value="light">{copy.common.light}</option>
        <option value="dark">{copy.common.dark}</option>
        <option value="system">{copy.common.system}</option>
      </select>
    </label>
  );
}
