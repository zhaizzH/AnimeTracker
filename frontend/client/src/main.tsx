import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider, theme as antdThemeApi } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { antdTheme, antdThemeDark, AuthGate, useBootstrapAuth, useThemeStore, resolveMode } from '@shared';
import 'antd/dist/reset.css';
import './index.css';
import { router } from './router';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

function Shell() {
  useBootstrapAuth();
  const mode = useThemeStore((s) => s.mode);
  const followSystem = useThemeStore((s) => s.followSystem);
  const resolved = resolveMode(mode, followSystem);
  // 同步到 <html> 供 index.css 的 .dark 变量覆盖使用
  const root = document.documentElement;
  root.classList.toggle('dark', resolved === 'dark');
  root.style.colorScheme = resolved === 'dark' ? 'dark' : 'light';
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) metaTheme.setAttribute('content', resolved === 'dark' ? '#1A1D17' : '#F7F5F0');
  return (
    <ConfigProvider theme={{ ...(resolved === 'dark' ? antdThemeDark : antdTheme), algorithm: resolved === 'dark' ? antdThemeApi.darkAlgorithm : antdThemeApi.defaultAlgorithm }}>
      <AuthGate className="od-auth-gate"><RouterProvider router={router} /></AuthGate>
    </ConfigProvider>
  );
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={queryClient}><Shell /></QueryClientProvider></React.StrictMode>,
);
