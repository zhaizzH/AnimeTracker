import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import './styles/theme.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          locale={zhCN}
          theme={{
            token: {
              colorPrimary: '#c13a24',
              colorInfo: '#c13a24',
              colorBgLayout: '#f3eee3',
              colorBgContainer: '#faf7f0',
              colorBorder: '#cbbfa8',
              colorText: '#201d18',
              colorTextSecondary: '#4f4a40',
              borderRadius: 2,
              fontSize: 15,
              fontFamily: '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Segoe UI", sans-serif',
            },
            components: {
              Card: { borderRadiusLG: 2 },
              Table: { headerBg: '#e8e0d0', rowHoverBg: '#faf7f0' },
              Tabs: { inkBarColor: '#c13a24', itemSelectedColor: '#201d18' },
            },
          }}
        >
          <ErrorBoundary>
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 48 }}>加载中...</div>}>
              <App />
            </Suspense>
          </ErrorBoundary>
        </ConfigProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>
);
