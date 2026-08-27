import { create } from 'zustand';
import type { LoginVO, UserVO } from '../types';

export type AuthStatus = 'checking' | 'authenticated' | 'unauthenticated' | 'retryable-error';

export interface AuthState {
  status: AuthStatus;
  token: string | null;
  user: UserVO | null;
  setChecking: () => void;
  setAuthenticated: (login: LoginVO) => void;
  setUnauthenticated: () => void;
  setRetryableError: () => void;
}

const LEGACY_STORAGE_KEY = 'animetracker-auth';
if (typeof window !== 'undefined') window.localStorage.removeItem(LEGACY_STORAGE_KEY);

export const useAuthStore = create<AuthState>((set) => ({
  status: 'checking',
  token: null,
  user: null,
  setChecking: () => set({ status: 'checking' }),
  setAuthenticated: (login) => set({ status: 'authenticated', token: login.token, user: login.user }),
  setUnauthenticated: () => set({ status: 'unauthenticated', token: null, user: null }),
  setRetryableError: () => set({ status: 'retryable-error' }),
}));