import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@shared': path.resolve(__dirname, '../packages/shared/src') } },
  test: {
    environment: 'jsdom',
    setupFiles: ['@testing-library/jest-dom/vitest', './src/test/matchMedia.ts'],
  },
});
