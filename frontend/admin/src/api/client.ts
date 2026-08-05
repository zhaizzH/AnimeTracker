import axios, { type AxiosRequestConfig } from 'axios';
import type { ApiResult } from '../types/api';
import { useAuthStore } from '../store/authStore';

const instance = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  paramsSerializer: { indexes: null },
});

export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) {
    useAuthStore.getState().signOut();
    return null;
  }
  try {
    const res = await axios.post('/api/user/auth/refresh', { refreshToken });
    const data = res.data?.data as { token?: string; refreshToken?: string } | undefined;
    if (data?.token && data?.refreshToken) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('refreshToken', data.refreshToken);
      useAuthStore.getState().setTokens(data.token, data.refreshToken);
      return data.token;
    }
  } catch {
    // refresh 失败，统一清理登录状态
  }
  useAuthStore.getState().signOut();
  return null;
}

instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

instance.interceptors.response.use(
  (response) => {
    const result = response.data as ApiResult<unknown>;
    if (result.code !== 0 && result.code !== 200) {
      return Promise.reject(new Error(result.message || '请求失败'));
    }
    return result.data as never;
  },
  async (error) => {
    const status = error.response?.status;
    const message =
      error.response?.data?.message ?? error.response?.data?.error ?? error.message ?? '请求失败';

    if (status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (isLoginRequest) {
        return Promise.reject(new Error(message));
      }
      const newToken = await refreshAccessToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return instance(error.config);
      }
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(new Error(message));
  },
);

const http = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    instance.get(url, config) as Promise<T>,
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
    instance.post(url, data, config) as Promise<T>,
};

export default http;
