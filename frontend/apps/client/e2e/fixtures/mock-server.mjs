/**
 * 公开 API 的确定性 mock 服务（零依赖，node:http）。
 *
 * 为什么需要它：本应用所有公开数据都在 Next.js 服务端渲染阶段 fetch
 * （Server Component 直接调用 adapter），Playwright 的 page.route 只能拦截
 * 浏览器发出的请求，拦不到服务端 fetch。因此把 mock 起在 adapter 默认的
 * http://localhost:8080（见 src/lib/api/public-client.ts 的 DEFAULT_BASE_URL），
 * 让 next build 预渲染与 next start 的运行时 SSR 都能取到确定性数据。
 *
 * 数据与 e2e/fixtures/api.ts 共享同一实现（api.ts 从本文件导入）。
 * 直接运行 `node e2e/fixtures/mock-server.mjs` 即监听 8080。
 */
import { createServer } from 'node:http';
import { pathToFileURL } from 'node:url';

const PORT = Number(process.env.MOCK_PORT || 8080);

/** 公开 API 的番剧条目（字段子集，对应 api-contract 的条目列表视图）。 */
export function makeSubject(id, overrides = {}) {
  return {
    id,
    name: `Subject ${id}`,
    nameCn: `番剧 ${id}`,
    score: 7.5,
    rank: 100 + id,
    eps: 12,
    airDate: '2023-10-01',
    type: 2,
    airWeekday: 1,
    collectionTotal: 1000 + id,
    ...overrides,
  };
}

/** 种子数据：覆盖搜索、年份筛选、详情页与时间表分桶所需的确定性数据。 */
export const ALL_SUBJECTS = [
  makeSubject(7, {
    name: '葬送的芙莉莲',
    nameCn: '葬送的芙莉莲',
    score: 9.2,
    rank: 3,
    eps: 28,
    airDate: '2023-09-29',
    airWeekday: 6,
    collectionTotal: 23456,
  }),
  makeSubject(1, { nameCn: '迷宫饭', airDate: '2024-01-04', airWeekday: 3 }),
  makeSubject(2, { nameCn: '药屋少女的呢喃', airDate: '2023-10-21', airWeekday: 5 }),
  makeSubject(3, { nameCn: '咒术回战 第二季', airDate: '2023-07-06', airWeekday: 3 }),
  makeSubject(4, { nameCn: '我推的孩子', airDate: '2023-04-12', airWeekday: 2 }),
  makeSubject(5, { nameCn: '间谍过家家 第二季', airDate: '2023-10-07', airWeekday: 5 }),
  makeSubject(6, { nameCn: '无职转生 第二季', airDate: '2023-07-02', airWeekday: 6 }),
];

export const TAG_LIST = [
  { id: 1, name: '奇幻', count: 12 },
  { id: 2, name: '日常', count: 8 },
];

export const EPISODES_BY_SUBJECT = {
  7: [
    { id: 71, subjectId: 7, type: 0, sort: 1, name: 'Episode 1', nameCn: '启程', duration: '24m', airdate: '2023-09-29', status: 'Air' },
    { id: 72, subjectId: 7, type: 0, sort: 2, name: 'Episode 2', nameCn: '重逢', duration: '24m', airdate: '2023-10-06', status: 'Air' },
  ],
};

const JSON_HEADERS = { 'content-type': 'application/json' };

function ok(data) {
  return JSON.stringify({ code: 200, message: 'success', data });
}

function paged(content) {
  return { content, total: content.length, page: 1, size: content.length };
}

function subjectDetail(subject) {
  return {
    ...subject,
    summary: `《${subject.nameCn}》是一部由 fixture 提供的确定性剧情简介，用于详情页渲染。`,
    tags: TAG_LIST,
    relations: [],
    createdAt: '2023-09-01T00:00:00',
    updatedAt: '2023-09-01T00:00:00',
  };
}

/** 按搜索词/年份过滤，模拟后端 searchSubjects 行为。 */
function filterBy(params) {
  const q = params.get('q')?.trim();
  const year = params.get('year');
  return ALL_SUBJECTS.filter((s) => {
    if (q && !(s.nameCn ?? '').includes(q) && !s.name.includes(q)) return false;
    if (year && s.airDate?.slice(0, 4) !== year) return false;
    return true;
  });
}

/**
 * 按请求 URL 返回 { status, headers, body }。
 * page.route 与 node:http 服务器共用，保证两边行为一致。
 */
export function handleApiRequest(url) {
  const { pathname } = url;
  const params = url.searchParams;

  // 健康检查：供 Playwright webServer.url 探测。
  if (pathname === '/__health') {
    return { status: 200, headers: JSON_HEADERS, body: 'ok' };
  }

  if (pathname === '/api/client/tags') {
    return { status: 200, headers: JSON_HEADERS, body: ok(TAG_LIST) };
  }

  if (pathname.startsWith('/api/client/subjects')) {
    // 业务错误模拟：搜索词为 error 时返回后端业务失败（含 x-request-id）。
    if (params.get('q') === 'error') {
      return {
        status: 200,
        headers: { ...JSON_HEADERS, 'x-request-id': 'req-err-001' },
        body: JSON.stringify({ code: 400, message: '模拟业务错误', data: null }),
      };
    }

    const episodeMatch = pathname.match(/^\/api\/client\/subjects\/(\d+)\/episodes$/);
    if (episodeMatch) {
      const id = Number(episodeMatch[1]);
      return { status: 200, headers: JSON_HEADERS, body: ok(EPISODES_BY_SUBJECT[id] ?? []) };
    }

    const detailMatch = pathname.match(/^\/api\/client\/subjects\/(\d+)$/);
    if (detailMatch) {
      const subject = ALL_SUBJECTS.find((s) => s.id === Number(detailMatch[1]));
      if (!subject) {
        return { status: 404, headers: JSON_HEADERS, body: JSON.stringify({ code: 404, message: '条目不存在', data: null }) };
      }
      return { status: 200, headers: JSON_HEADERS, body: ok(subjectDetail(subject)) };
    }

    if (pathname.endsWith('/search')) {
      return { status: 200, headers: JSON_HEADERS, body: ok(paged(filterBy(params))) };
    }

    if (pathname.endsWith('/season')) {
      // 本季新番：返回全部种子，保证首页三板块有内容。
      return { status: 200, headers: JSON_HEADERS, body: ok(paged(ALL_SUBJECTS)) };
    }

    if (pathname.endsWith('/schedule')) {
      const weekday = params.get('weekday');
      const list =
        weekday === null || weekday === ''
          ? ALL_SUBJECTS
          : ALL_SUBJECTS.filter((s) => s.airWeekday === Number(weekday));
      return { status: 200, headers: JSON_HEADERS, body: ok(paged(list)) };
    }

    // /api/client/subjects（无筛选列表）与其它未知子路径：全部种子。
    return { status: 200, headers: JSON_HEADERS, body: ok(paged(ALL_SUBJECTS)) };
  }

  return { status: 404, headers: JSON_HEADERS, body: ok(null) };
}

/** 创建可独立启动的 HTTP 服务。 */
export function createMockServer() {
  return createServer((req, res) => {
    const url = new URL(req.url ?? '/', `http://${req.headers.host ?? 'localhost'}`);
    const { status, headers, body } = handleApiRequest(url);
    res.writeHead(status, headers);
    res.end(body);
  });
}

// 直接运行本文件时启动服务。
const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  createMockServer().listen(PORT, () => {
    console.log(`[mock-api] listening on http://localhost:${PORT}`);
  });
}
