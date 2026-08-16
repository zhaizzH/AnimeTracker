import { test, expect } from '@playwright/test';
import { installPublicApiFixtures } from './fixtures/api';
import { copy } from '../src/content/zh-CN';

/**
 * 公开页面关键流程 E2E：首页、顶部搜索、发现筛选、详情导航、
 * 时间表选择、主题切换、404、后端业务错误与键盘导航。
 * 所有断言字符串取自 src/content/zh-CN.ts（唯一文案来源）。
 */
test.beforeEach(async ({ page }) => {
  await installPublicApiFixtures(page);
});

test('首页渲染三个板块', async ({ page }) => {
  await page.goto('/');
  for (const heading of [copy.home.seasonal, copy.home.popular, copy.home.todaySchedule]) {
    await expect(page.getByRole('heading', { level: 2, name: heading })).toBeVisible();
  }
});

test('从顶部搜索并打开条目详情', async ({ page }) => {
  await page.goto('/');
  // 移动端搜索入口折叠在 <details> 中，先展开再填充。
  const searchBox = page.getByRole('textbox', { name: copy.search.label });
  if ((await searchBox.count()) === 0) {
    await page.locator('summary', { hasText: copy.search.trigger }).click();
  }
  await searchBox.fill('芙莉莲');
  await searchBox.press('Enter');
  await expect(page).toHaveURL(/\/discover\?q=/);
  await page.getByRole('link', { name: /葬送的芙莉莲/ }).click();
  await expect(page.getByRole('heading', { level: 1 })).toContainText('葬送的芙莉莲');
});

test('发现页筛选：按年份筛选更新结果', async ({ page }) => {
  await page.goto('/discover');
  await page.getByLabel(copy.discovery.year).selectOption('2023');
  await page.getByRole('button', { name: copy.discovery.filter }).click();
  await expect(page).toHaveURL(/year=2023/);
  await expect(page.getByRole('link', { name: /葬送的芙莉莲/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /迷宫饭/ })).toBeHidden();
});

test('条目详情渲染标题与剧集', async ({ page }) => {
  await page.goto('/subjects/7');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('葬送的芙莉莲');
  await expect(page.getByRole('region', { name: copy.detail.episodes }).getByText('第 1 集')).toBeVisible();
});

test('时间表选择星期', async ({ page }) => {
  await page.goto('/schedule');
  const wednesday = page.getByRole('link', { name: copy.schedule.weekdays[2] });
  await wednesday.click();
  await expect(page).toHaveURL(/weekday=3/);
  await expect(wednesday).toHaveAttribute('aria-current', 'page');
});

test('主题切换写入深色', async ({ page }) => {
  await page.goto('/');
  await page.locator('summary', { hasText: copy.navigation.userMenu }).click();
  await page.getByLabel(copy.common.theme).selectOption(copy.common.dark);
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect.poll(() => page.evaluate(() => document.cookie)).toContain('at-theme=dark');
});

test('未知路由渲染全局 404', async ({ page }) => {
  await page.goto('/no-such-page-xyz');
  await expect(page.getByRole('heading', { level: 1 })).toContainText(copy.notFound.title);
  await expect(page.getByText(copy.notFound.message)).toBeVisible();
});

test('发现页展示后端业务错误与请求编号', async ({ page }) => {
  await page.goto('/discover?q=error');
  // Next.js 路由播报也有 role=alert，按业务错误文案过滤到错误态区域。
  const alert = page.getByRole('alert').filter({ hasText: '模拟业务错误' });
  await expect(alert).toContainText('模拟业务错误');
  await expect(alert).toContainText('请求编号: req-err-001');
});

test('键盘导航：首次 Tab 聚焦跳过链接', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: copy.a11y.skipToContent })).toBeFocused();
});
