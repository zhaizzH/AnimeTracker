import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type { ApiResult } from '../types';
import { useAuthStore } from '../store/auth';
import { refreshWithLock } from '../auth/coordinator';

export const http: AxiosInstance = axios.create({
  baseURL: '/api', timeout: 20000, withCredentials: true, paramsSerializer: { indexes: null },
});

http.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

http.interceptors.response.use(
  (res) => {
    const body = res.data as ApiResult<unknown>;
    if (body.code === 200) return body.data as never;
    return Promise.reject(new Error(body.message || '请求失败'));
  },
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    if (error.response?.status === 401 && original && !original._retried && original.url !== '/client/auth/refresh') {
      original._retried = true;
      if (await refreshWithLock()) return http(original);
    }
    return Promise.reject(error);
  },
);

export const get = <T>(url: string, params?: object) => http.get(url, { params }) as Promise<T>;
export const post = <T>(url: string, data?: unknown) => http.post(url, data) as Promise<T>;
export const postForm = <T>(url: string, form: FormData) => http.post(url, form) as Promise<T>;