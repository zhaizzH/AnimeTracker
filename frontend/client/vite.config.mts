import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@shared': path.resolve(__dirname, '../packages/shared/src') } },
  // Pre-bundle current lazy-route dependencies to avoid late optimizer generations and mixed React runtimes.
  optimizeDeps: {
    include: [
      '@ant-design/icons',
      '@tanstack/react-query',
      'antd',
      'axios',
      'react',
      'react-dom',
      'react-dom/client',
      'react-markdown',
      'react-router-dom',
      'zustand',
      'zustand/middleware',
    ],
  },
  server: { port: 5173, proxy: { '/api': { target: 'http://localhost:8080', changeOrigin: true } } },
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
