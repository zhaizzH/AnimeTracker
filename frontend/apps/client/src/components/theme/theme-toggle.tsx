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

function readSavedMode(): ThemeMode | null {
  const m = document.cookie.match(/(?:^|;\s*)at-theme=(light|dark|system)/);
  return m ? (m[1] as ThemeMode) : null;
}

function persist(mode: ThemeMode) {
  document.cookie = `${COOKIE}=${mode}; ${COOKIE_OPTIONS}`;
}

function syncDom(mode: ThemeMode) {
  document.documentElement.dataset.theme = resolve(mode);
}

export function ThemeToggle({ initialMode = 'system' }: { initialMode?: ThemeMode }) {
  // 服务端预渲染时无 document，必须回退到 initialMode
  const [mode, setMode] = useState<ThemeMode>(() =>
    typeof document === 'undefined' ? initialMode : readSavedMode() ?? initialMode,
  );

  useEffect(() => {
    syncDom(mode);
    if (mode !== 'system' || typeof window.matchMedia !== 'function') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => syncDom('system');
    media.addEventListener?.('change', onChange);
    return () => media.removeEventListener?.('change', onChange);
  }, [mode]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const next = e.target.value as ThemeMode;
    setMode(next);
    persist(next);
    syncDom(next);
  };

  return (
    <label>
      {copy.common.theme}
      <select value={mode} onChange={handleChange}>
        <option value="light">{copy.common.light}</option>
        <option value="dark">{copy.common.dark}</option>
        <option value="system">{copy.common.system}</option>
      </select>
    </label>
  );
}
