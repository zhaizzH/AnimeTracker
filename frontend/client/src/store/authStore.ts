import { create } from 'zustand';
import type { UserVO } from '@/types';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: UserVO | null;
  isLoggedIn: boolean;
  login: (token: string, refreshToken: string, user: UserVO) => void;
  logout: () => void;
  setUser: (user: UserVO) => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  refreshToken: null,
  user: null,
  isLoggedIn: false,

  login: (token, refreshToken, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refreshToken', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
    set({ token, refreshToken, user, isLoggedIn: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    set({ token: null, refreshToken: null, user: null, isLoggedIn: false });
  },

  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user));
    set({ user });
  },

  hydrate: () => {
    const token = localStorage.getItem('token');
    const refreshToken = localStorage.getItem('refreshToken');
    const userStr = localStorage.getItem('user');
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as UserVO;
        set({ token, refreshToken, user, isLoggedIn: true });
      } catch {
        set({ token: null, refreshToken: null, user: null, isLoggedIn: false });
      }
    }
  },
}));
