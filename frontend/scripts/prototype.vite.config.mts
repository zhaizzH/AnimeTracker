// 原型构建配置：本文件位于 frontend/ 下，能正常解析 vite / @vitejs/plugin-react 等裸包；
// 只把 root 指向任务目录里的原型。原型不进生产构建，与 client/admin 互不干扰。
//
// 用途：
//   cd frontend && npx vite build --config scripts/prototype.vite.config.mts   # 验证能构建
//   cd frontend && npx vite --config scripts/prototype.vite.config.mts         # 本地跑原型
// 默认输出到 frontend/.prototype-dist（已被 .gitignore 忽略）。
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');                                    // frontend/
const NM = (p: string) => path.resolve(ROOT, 'node_modules', p);
const PROTOTYPE = path.resolve(ROOT, '../.trellis/tasks/10-29-frontend-url-state/prototype');

export default defineConfig({
  root: PROTOTYPE,
  plugins: [react(), tailwindcss()],
  // 原型目录在 frontend/ 之外，裸模块解析从原型目录向上找不到 node_modules，
  // 因此运行时依赖全部显式别名到 frontend/node_modules。
  resolve: {
    alias: [
      { find: '@shared', replacement: path.resolve(ROOT, 'packages/shared/src') },
      { find: /^@\//, replacement: path.resolve(ROOT, 'client/src') + '/' },
      { find: /^react\/jsx-runtime$/, replacement: NM('react/jsx-runtime') },
      { find: /^react\/jsx-dev-runtime$/, replacement: NM('react/jsx-dev-runtime') },
      { find: /^react-dom\/client$/, replacement: NM('react-dom/client') },
      { find: /^react-dom$/, replacement: NM('react-dom') },
      { find: /^react$/, replacement: NM('react') },
      { find: /^lucide-react$/, replacement: NM('lucide-react') },
    ],
  },
  server: { port: 5174, open: '/index.html' },
  build: {
    outDir: path.resolve(ROOT, '.prototype-dist'),
    emptyOutDir: true,
  },
});
