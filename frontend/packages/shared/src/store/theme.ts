import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeMode = 'light' | 'dark';

interface ThemeState {
  mode: ThemeMode;
  /** 'system' 时跟随 prefers-color-scheme，重写向到 light/dark 由 resolveMode 处理 */
  followSystem: boolean;
  setMode: (mode: ThemeMode) => void;
  toggleFollowSystem: () => void;
}

export const useThemeStore = create<ThemeState>()(persist(
  (set) => ({
    mode: 'light',
    followSystem: true,
    setMode: (mode) => set({ mode, followSystem: false }),
    toggleFollowSystem: () => set((s) => ({ followSystem: !s.followSystem })),
  }),
  { name: 'animetracker-theme' },
));

/** followSystem 时读取系统偏好，否则直接用 mode */
export function resolveMode(mode: ThemeMode, followSystem: boolean): ThemeMode {
  if (followSystem && typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return mode;
}
