import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type { ApiResult, LoginVO } from '../types';
import { useAuthStore } from '../store/auth';

export const http: AxiosInstance = axios.create({ baseURL: '/api', timeout: 20000, paramsSerializer: { indexes: null } });

http.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

let refreshing: Promise<boolean> | null = null;

http.interceptors.response.use(
  (res) => {
    const body = res.data as ApiResult<unknown>;
    if (body.code === 0) return body.data as never;
    return Promise.reject(new Error(body.message || '请求失败'));
  },
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
    if (error.response?.status === 401 && !original._retried && original.url !== '/client/auth/refresh') {
      original._retried = true;
      refreshing ??= refreshOnce().finally(() => { refreshing = null; });
      if (await refreshing) return http(original);
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

async function refreshOnce(): Promise<boolean> {
  const { refreshToken } = useAuthStore.getState();
  if (!refreshToken) return false;
  try {
    const res = await axios.post<ApiResult<LoginVO>>('/api/client/auth/refresh', { refreshToken });
    if (res.data.code !== 0) return false;
    useAuthStore.getState().setLogin(res.data.data);
    return true;
  } catch { return false; }
}

export const get = <T>(url: string, params?: Record<string, unknown>) => http.get(url, { params }) as Promise<T>;
export const post = <T>(url: string, data?: unknown) => http.post(url, data) as Promise<T>;
export const postForm = <T>(url: string, form: FormData) => http.post(url, form) as Promise<T>;
