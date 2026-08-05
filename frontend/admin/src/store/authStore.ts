import { create } from 'zustand';
import type { UserVO } from '../types/api';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  username: string | null;
  role: 'ADMIN' | 'USER' | null;
  user: UserVO | null;
  signIn: (token: string, refreshToken: string, user: UserVO) => void;
  setTokens: (token: string, refreshToken: string) => void;
  signOut: () => void;
}

function loadUser(): UserVO | null {
  try {
    const raw = localStorage.getItem('adminUser');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const initToken = localStorage.getItem('token');
const initRefreshToken = localStorage.getItem('refreshToken');
const initUser = loadUser();

export const useAuthStore = create<AuthState>((set) => ({
  token: initToken,
  refreshToken: initRefreshToken,
  username: initUser?.username ?? null,
  role: initUser?.role ?? null,
  user: initUser,
  signIn: (token, refreshToken, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refreshToken', refreshToken);
    localStorage.setItem('adminUser', JSON.stringify(user));
    set({ token, refreshToken, user, username: user.username, role: user.role });
  },
  setTokens: (token, refreshToken) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refreshToken', refreshToken);
    set({ token, refreshToken });
  },
  signOut: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('adminUser');
    set({ token: null, refreshToken: null, username: null, role: null, user: null });
  },
}));
