import axios, { type AxiosRequestConfig } from 'axios';
import type { ApiResult } from '@/types';
import { useAuthStore } from '@/store/authStore';

const instance = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  // 数组参数序列化为重复键（tag=2003 而非 tag[]=2003），匹配 Spring @RequestParam List 绑定
  paramsSerializer: { indexes: null },
});

/**
 * 用 refreshToken 换取新的 token 对，并同步 localStorage 与登录状态。
 * 返回新的 access token；失败返回 null。
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) {
    useAuthStore.getState().logout();
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
  useAuthStore.getState().logout();
  return null;
}

// 请求拦截器 — 自动附加 token
instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 — 自动解包 data
instance.interceptors.response.use(
  (response) => {
    const result = response.data as ApiResult<unknown>;
    if (result.code !== 0 && result.code !== 200) {
      return Promise.reject(new Error(result.message || '请求失败'));
    }
    return result.data as any;
  },
  async (error) => {
    if (error.response?.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return instance(error.config);
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// 包装类型以匹配拦截器解包行为 — 运行时已解包，仅修正 TS 类型
const http = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    instance.get(url, config) as Promise<T>,
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
    instance.post(url, data, config) as Promise<T>,
};

export default http;
