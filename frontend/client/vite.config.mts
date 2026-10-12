import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Vite 的别名匹配要求 importee 等于键或以 `<key>/` 开头，因此 `@` 不会误匹配 `@shared`。
    alias: {
      '@shared': path.resolve(__dirname, '../packages/shared/src'),
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Pre-bundle current lazy-route dependencies to avoid late optimizer generations and mixed React runtimes.
  optimizeDeps: {
    include: [
      '@tanstack/react-query',
      'axios',
      'react',
      'react-dom',
      'react-dom/client',
      'react-markdown',
      'react-router-dom',
      'remark-gfm',
      'sonner',
      'zustand',
      'zustand/middleware',
    ],
  },
  server: { port: 5173, proxy: { '/api': { target: 'http://localhost:8080', changeOrigin: true }, '/media': { target: 'http://localhost:9000/anime-tracker', changeOrigin: true, rewrite: (p) => p.replace(/^\/media/, '') } } },
  build: {
    // Framework chunks stay below 560 kB minified and 186 kB gzip; larger regressions still warn.
    chunkSizeWarningLimit: 560,
    rollupOptions: {
      output: {
        onlyExplicitManualChunks: true,
        manualChunks(id) {
          if (!id.includes('/node_modules/')) return;
          if (/\/node_modules\/(?:react|react-dom|react-router|react-router-dom|scheduler)\//.test(id)) return 'vendor-react';
          if (/\/node_modules\/(?:@tanstack|axios|zustand)\//.test(id)) return 'vendor-data';
          // radix-ui 与 sonner 是全局使用的 UI 基元，独立成 vendor-ui 避免被各页面 chunk 重复包含。
          if (/\/node_modules\/(?:radix-ui|@radix-ui|sonner)\//.test(id)) return 'vendor-ui';
        },
      },
    },
  },
});
