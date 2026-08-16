import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  esbuild: {
    jsx: 'automatic',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Playwright 的 e2e/*.spec.ts 是浏览器测试，必须排除在 vitest 之外。
    exclude: ['e2e/**', '**/node_modules/**', '**/dist/**'],
  },
});
