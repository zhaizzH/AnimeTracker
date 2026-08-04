import axios, { type AxiosRequestConfig } from 'axios';
import type { ApiResult } from '@/types';

const instance = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  // 数组参数序列化为重复键（tag=2003 而非 tag[]=2003），匹配 Spring @RequestParam List 绑定
  paramsSerializer: { indexes: null },
});

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
      // 尝试 refresh
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const res = await axios.post('/api/user/auth/refresh', { refreshToken });
          const data = res.data.data;
          if (data) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('refreshToken', data.refreshToken);
            error.config.headers.Authorization = `Bearer ${data.token}`;
            return instance(error.config);
          }
        } catch {
          // refresh 失败，清除登录状态
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
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
