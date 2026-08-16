import { test, expect } from '@playwright/test';
import { installPublicApiFixtures } from './fixtures/api';
import { copy } from '../src/content/zh-CN';

/**
 * 响应式外壳 E2E：移动端无水平溢出、底部主导航两项；
 * 桌面端主导航两项。选择器名称取自 src/content/zh-CN.ts。
 */
test.beforeEach(async ({ page }) => {
  await installPublicApiFixtures(page);
});

test('移动端外壳无水平溢出且底部导航有两个链接', async ({ page }) => {
  test.skip(test.info().project.name !== 'mobile', '仅移动端项目');
  await page.goto('/');
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByRole('navigation', { name: copy.navigation.mobile, exact: true }).getByRole('link'),
  ).toHaveCount(2);
});

test('桌面端主导航有两个链接', async ({ page }) => {
  test.skip(test.info().project.name !== 'desktop', '仅桌面端项目');
  await page.goto('/');
  await expect(
    page.getByRole('navigation', { name: copy.navigation.primary, exact: true }).getByRole('link'),
  ).toHaveCount(2);
});
