import type { Page, Route } from '@playwright/test';
import { handleApiRequest } from './mock-server.mjs';

/**
 * 公开 API 的浏览器层拦截 fixture。
 *
 * 本应用公开数据在 Next.js 服务端渲染阶段 fetch（Server Component 直接调用
 * adapter），page.route 拦不到服务端请求 —— 那部分由 e2e/fixtures/mock-server.mjs
 * 起在 E2E 专用的 http://127.0.0.1:18080 提供确定性数据（playwright.config.ts
 * 里注册了该 webServer）。这里的 page.route 覆盖浏览器侧任何 /api/client/* 请求
 * 作为兜底，与 mock 服务共用同一 handler，保证行为一致。
 *
 * 调用时机：必须在 page.goto 之前安装。
 */
export async function installPublicApiFixtures(page: Page): Promise<void> {
  await page.route(/\/api\/client\/(subjects|tags)/, (route: Route) => {
    const { status, headers, body } = handleApiRequest(new URL(route.request().url()));
    void route.fulfill({ status, headers, body });
  });
}
