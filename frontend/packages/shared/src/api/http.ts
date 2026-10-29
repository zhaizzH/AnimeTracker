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

// 这些端点把 401/403 当作业务结果（凭据错误、邮箱未验证、验证码错误）直接返回，
// 不应触发静默刷新重试；logout 不在列内，令牌过期时仍应先刷新再重放。
const AUTH_ENDPOINT = /^\/client\/auth\/(login|register|verify-email|resend-code|refresh|forgot-password|reset-password)$/;

/** 优先暴露后端 Result.message，避免 axios 的 “Request failed with status code 401” 掩盖真实原因 */
function toError(error: AxiosError): Error {
  const body = error.response?.data as ApiResult<unknown> | undefined;
  // status / data 供调用方分支：409 冲突的 active_run_id 在 data 里，不在 message 里。
  // 只有真的存在才挂键，避免 `'data' in err` 在网络错误下误判。
  return Object.assign(new Error(body?.message || error.message || '请求失败'), {
    ...(error.response?.status !== undefined && { status: error.response.status }),
    ...(body?.data !== undefined && { data: body.data }),
  });
}

http.interceptors.response.use(
  (res) => {
    const body = res.data as ApiResult<unknown>;
    if (body.code === 200) return body.data as never;
    return Promise.reject(
      Object.assign(new Error(body.message || '请求失败'), { status: res.status, data: body.data }),
    );
  },
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    const url = original?.url ?? '';
    if (error.response?.status === 401 && original && !original._retried && !AUTH_ENDPOINT.test(url)) {
      original._retried = true;
      if (await refreshWithLock()) return http(original);
    }
    return Promise.reject(toError(error));
  },
);

export const get = <T>(url: string, params?: object) => http.get(url, { params }) as Promise<T>;
export const post = <T>(url: string, data?: unknown) => http.post(url, data) as Promise<T>;
export const postForm = <T>(url: string, form: FormData) => http.post(url, form) as Promise<T>;