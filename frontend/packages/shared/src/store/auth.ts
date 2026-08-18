import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LoginVO, UserVO } from '../types';

export interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: UserVO | null;
  isLoggedIn: boolean;
  setLogin: (login: LoginVO) => void;
  setUser: (user: UserVO) => void;
  logout: () => void;
}
export const useAuthStore = create<AuthState>()(persist(
  (set) => ({
    token: null, refreshToken: null, user: null, isLoggedIn: false,
    setLogin: (l) => set({ token: l.token, refreshToken: l.refreshToken, user: l.user, isLoggedIn: true }),
    setUser: (u) => set({ user: u }),
    logout: () => set({ token: null, refreshToken: null, user: null, isLoggedIn: false }),
  }),
  { name: 'animetracker-auth' },
));
