import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { antdTheme, AuthGate, useBootstrapAuth } from '@shared';
// 实测（2026-09-21）：antd 的 reset.css 只有 3.6KB，且不含 h1–h6 / ul / ol 规则，
// 因此没有任何东西能挡住 Tailwind preflight —— 它的 h1–h6 字号与 ul/ol 列表样式确实会在
// admin 页面上生效。加载顺序调换无效，本阶段的做法是：遇到 preflight 破坏处就地补偿
// （见 components/charts.tsx 的 h3、pages/Dashboard.tsx 的 ol）。新增裸 h*/ul/ol 时需同样处理。
import './index.css';
import 'antd/dist/reset.css';
import { router } from './router';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

function Shell() {
  useBootstrapAuth();
  return (
    <ConfigProvider theme={antdTheme}>
      <AuthGate><RouterProvider router={router} /></AuthGate>
      <Toaster richColors position="top-right" />
    </ConfigProvider>
  );
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={queryClient}><Shell /></QueryClientProvider></React.StrictMode>,
);
