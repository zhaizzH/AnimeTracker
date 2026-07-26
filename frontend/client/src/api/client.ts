import axios from 'axios';
import type { ApiResult } from '@/types';

const http = axios.create({
  baseURL: '/api',
  timeout: 30_000,
});

// 请求拦截器 — 自动附加 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 — 自动解包 data
http.interceptors.response.use(
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
            return http(error.config);
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

export default http;
