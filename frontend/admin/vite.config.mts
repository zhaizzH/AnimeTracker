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
  server: { port: 5174, proxy: { '/api': { target: 'http://localhost:8080', changeOrigin: true } } },
  build: {
    // Framework chunks stay below 560 kB minified and 186 kB gzip; larger regressions still warn.
    chunkSizeWarningLimit: 560,
    rollupOptions: {
      output: {
        onlyExplicitManualChunks: true,
        manualChunks(id) {
          if (!id.includes('/node_modules/')) return;
          if (/\/node_modules\/(?:@ant-design\/|rc-|@rc-component\/)/.test(id)) return 'vendor-antd-deps';
          if (id.includes('/node_modules/antd/')) return 'vendor-antd';
          if (/\/node_modules\/(?:react|react-dom|react-router|react-router-dom|scheduler)\//.test(id)) return 'vendor-react';
          if (/\/node_modules\/(?:@tanstack|axios|zustand)\//.test(id)) return 'vendor-data';
        },
      },
    },
  },
});
