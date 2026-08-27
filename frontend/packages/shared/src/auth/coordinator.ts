import axios, { type AxiosError } from 'axios';
import type { ApiResult, LoginVO } from '../types';
import { useAuthStore } from '../store/auth';

export const sessionHttp = axios.create({ baseURL: '/api', timeout: 20000, withCredentials: true });

type AuthEvent = { type: 'session-available' } | { type: 'signed-out' };
const channel = typeof window !== 'undefined' && (import.meta as ImportMeta & { env?: { MODE?: string } }).env?.MODE !== 'test' && 'BroadcastChannel' in window
  ? new BroadcastChannel('animetracker-auth-events')
  : null;
let inTabRefresh: Promise<boolean> | null = null;
let bootstrapPromise: Promise<boolean> | null = null;

function applyFailure(error: unknown): boolean {
  const status = (error as AxiosError)?.response?.status;
  if (status === 401 || status === 403) useAuthStore.getState().setUnauthenticated();
  else useAuthStore.getState().setRetryableError();
  return false;
}

async function performRefresh(): Promise<boolean> {
  try {
    const response = await sessionHttp.post<ApiResult<LoginVO>>('/client/auth/refresh');
    if (response.data.code !== 200 || !response.data.data) {
      return applyFailure({ response: { status: response.data.code } } as AxiosError);
    }
    useAuthStore.getState().setAuthenticated(response.data.data);
    return true;
  } catch (error) {
    return applyFailure(error);
  }
}

export async function refreshWithLock(): Promise<boolean> {
  if (inTabRefresh) return inTabRefresh;
  const run = async () => {
    if (typeof navigator !== 'undefined' && navigator.locks) {
      return navigator.locks.request('animetracker-refresh', performRefresh);
    }
    return performRefresh();
  };
  inTabRefresh = run().finally(() => { inTabRefresh = null; });
  return inTabRefresh;
}

export function bootstrapAuth(): Promise<boolean> {
  bootstrapPromise ??= refreshWithLock();
  return bootstrapPromise;
}

export function retryBootstrapAuth(): Promise<boolean> {
  bootstrapPromise = null;
  useAuthStore.getState().setChecking();
  return bootstrapAuth();
}

export function resetBootstrap(): void {
  bootstrapPromise = null;
  inTabRefresh = null;
}
export async function completeLogout(request: () => Promise<unknown>): Promise<boolean> {
  try {
    await request();
    useAuthStore.getState().setUnauthenticated();
    publishSignedOut();
    resetBootstrap();
    return true;
  } catch {
    return false;
  }
}

export function publishSessionAvailable(): void {
  channel?.postMessage({ type: 'session-available' } satisfies AuthEvent);
}

export function publishSignedOut(): void {
  channel?.postMessage({ type: 'signed-out' } satisfies AuthEvent);
}

if (channel) {
  channel.onmessage = ({ data }: MessageEvent<AuthEvent>) => {
    if (data?.type === 'signed-out') useAuthStore.getState().setUnauthenticated();
    if (data?.type === 'session-available') {
      useAuthStore.getState().setChecking();
      void refreshWithLock();
    }
  };
}