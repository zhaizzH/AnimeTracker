import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AuthGate, useBootstrapAuth } from '@shared';
import './index.css';
import { router } from './router';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

function Shell() {
  useBootstrapAuth();
  return (
    <><AuthGate><RouterProvider router={router} /></AuthGate><Toaster richColors position="top-right" /></>
  );
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={queryClient}><Shell /></QueryClientProvider></React.StrictMode>,
);
