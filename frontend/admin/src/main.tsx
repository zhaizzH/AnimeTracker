import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { antdTheme, AuthGate, useBootstrapAuth } from '@shared';
import 'antd/dist/reset.css';
import { router } from './router';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

function Shell() {
  useBootstrapAuth();
  return <ConfigProvider theme={antdTheme}><AuthGate><RouterProvider router={router} /></AuthGate></ConfigProvider>;
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={queryClient}><Shell /></QueryClientProvider></React.StrictMode>,
);
