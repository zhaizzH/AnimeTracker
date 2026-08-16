import type { paths } from '@animetracker/api-contract';
import { ApiError } from './errors';

const DEFAULT_BASE_URL = 'http://localhost:8080';
const UNSAFE_MESSAGE_FALLBACK = '服务暂时不可用，请稍后重试';
const UNSAFE_MESSAGE_RE = /java\.lang\.|Traceback| at top\./;

/** Next.js 服务端 fetch 缓存配置（next.revalidate / next.tags / cache）。 */
type NextFetchRequestConfig = { revalidate?: number | false; tags?: string[] };
type CacheOptions = { next?: NextFetchRequestConfig; cache?: RequestCache };

type GetOp<P extends keyof paths> = NonNullable<paths[P]['get']>;
type QueryParams<P extends keyof paths> = NonNullable<GetOp<P>['parameters']>['query'];
type Data<P extends keyof paths> = NonNullable<
  NonNullable<GetOp<P>['responses'][200]>['content']['application/json']
>['data'];

/** 后端统一响应信封 { code, message, data }。 */
type Envelope = { code?: number; message?: string; data?: unknown };

function isUnsafeMessage(message: string): boolean {
  return UNSAFE_MESSAGE_RE.test(message);
}

function buildUrl(baseUrl: string, path: string, params?: object): URL {
  const url = new URL(path, baseUrl);
  if (params) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null) continue;
      if (Array.isArray(value)) {
        for (const item of value) search.append(key, String(item));
      } else {
        search.set(key, String(value));
      }
    }
    const query = search.toString();
    if (query) url.search = query;
  }
  return url;
}

/** 统一的请求边界：设置 accept 头、透传 Next 缓存选项、解析一次信封、校验 code。 */
async function request<T>(url: URL, cache: CacheOptions): Promise<T> {
  const res = await fetch(url, {
    ...cache,
    headers: { accept: 'application/json' },
  } as RequestInit);
  const requestId = res.headers.get('x-request-id') ?? undefined;
  const body = (await res.json().catch(() => null)) as Envelope | null;
  const message = body?.message ?? '';
  const safeMessage = isUnsafeMessage(message) ? UNSAFE_MESSAGE_FALLBACK : message;
  if (!res.ok || body === null || body.code !== 200) {
    throw new ApiError(res.status, safeMessage, body?.code, requestId);
  }
  return body.data as T;
}

export function createPublicApi(baseUrl: string) {
  const call = <T>(
    url: string,
    params: object | undefined,
    cache: CacheOptions,
  ) => request<T>(buildUrl(baseUrl, url, params), cache);

  const callWithTags =
    (tags?: string[]) =>
    <T>(url: string, params: object | undefined, cache: CacheOptions) =>
      call<T>(url, params, { next: { ...cache.next, tags } });

  return {
    listSubjects: (params?: QueryParams<'/api/client/subjects'>, tags?: string[]) =>
      callWithTags(tags)<Data<'/api/client/subjects'>>('/api/client/subjects', params, {
        next: { revalidate: 300 },
      }),
    searchSubjects: (params?: QueryParams<'/api/client/subjects/search'>) =>
      call<Data<'/api/client/subjects/search'>>('/api/client/subjects/search', params, { next: { revalidate: 60 } }),
    getSeason: (params?: QueryParams<'/api/client/subjects/season'>, tags?: string[]) =>
      callWithTags(tags)<Data<'/api/client/subjects/season'>>('/api/client/subjects/season', params, {
        next: { revalidate: 3600 },
      }),
    getSchedule: (params?: QueryParams<'/api/client/subjects/schedule'>, tags?: string[]) =>
      callWithTags(tags)<Data<'/api/client/subjects/schedule'>>('/api/client/subjects/schedule', params, {
        next: { revalidate: 300 },
      }),
    getSubject: (id: number) =>
      call<Data<'/api/client/subjects/{id}'>>(`/api/client/subjects/${id}`, undefined, { next: { revalidate: 3600 } }),
    getEpisodes: (id: number) =>
      call<Data<'/api/client/subjects/{id}/episodes'>>(`/api/client/subjects/${id}/episodes`, undefined, { next: { revalidate: 300 } }),
    listTags: () =>
      call<Data<'/api/client/tags'>>('/api/client/tags', undefined, { next: { revalidate: 3600 } }),
  };
}

/**
 * 读取 BUSINESS_API_URL，非生产环境默认本地后端。
 * 各方法可单独传入 Next 缓存标签（tags），写入该次请求的 fetch 缓存。
 */
export function getPublicApi() {
  return createPublicApi(process.env.BUSINESS_API_URL || DEFAULT_BASE_URL);
}
