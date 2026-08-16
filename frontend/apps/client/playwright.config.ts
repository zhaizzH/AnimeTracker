import { defineConfig, devices } from '@playwright/test';

/**
 * 公开流程 E2E：生产构建 + 确定性 mock 后端。
 *
 * 公开数据全部在 Next.js 服务端渲染阶段 fetch（Server Component 直接调用
 * adapter），page.route 拦不到服务端请求。因此额外注册一个零依赖 mock 服务
 * 在 adapter 默认的 http://localhost:8080（见 src/lib/api/public-client.ts），
 * 覆盖 /api/client/subjects* 与 /api/client/tags；next build 预渲染与 next start
 * 运行时 SSR 都从它取数。页面文档与静态资源仍走真实生产构建。
 * 浏览器侧兜底拦截见 e2e/fixtures/api.ts。
 */
const PORT = 3000;
const baseURL = `http://localhost:${PORT}`;
const MOCK_BASE = 'http://localhost:8080';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list']],
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'mobile',
      use: { ...devices['Mobile Chrome'], viewport: { width: 390, height: 844 } },
    },
  ],
  webServer: [
    {
      command: 'node e2e/fixtures/mock-server.mjs',
      url: `${MOCK_BASE}/__health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: 'pnpm build && pnpm start',
      url: baseURL,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
    },
  ],
});
