import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';
import { AdminLayout } from './layouts/AdminLayout';
import { RequireAdmin } from './guards';
import AdminLogin from './pages/AdminLogin';
const withLoading = (el: React.ReactNode) => <Suspense fallback={<Spin style={{ display: 'block', margin: 40 }} />}>{el}</Suspense>;
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Subjects = lazy(() => import('./pages/Subjects'));
const Users = lazy(() => import('./pages/Users'));
const ImportPage = lazy(() => import('./pages/Import'));
const Logs = lazy(() => import('./pages/Logs'));
const AgentConfig = lazy(() => import('./pages/AgentConfig'));
const AgentChat = lazy(() => import('./pages/AgentChat'));

export const router = createBrowserRouter([
  { path: '/admin/login', element: <AdminLogin /> },
  { path: '/admin', element: <RequireAdmin><AdminLayout /></RequireAdmin>, children: [
    { index: true, element: <Navigate to="/admin/dashboard" replace /> },
    { path: 'dashboard', element: withLoading(<Dashboard />) },
    { path: 'subjects', element: withLoading(<Subjects />) },
    { path: 'users', element: withLoading(<Users />) },
    { path: 'import', element: withLoading(<ImportPage />) },
    { path: 'logs', element: withLoading(<Logs />) },
    { path: 'agent-config', element: withLoading(<AgentConfig />) },
    { path: 'agent-chat', element: withLoading(<AgentChat />) },
  ]},
  { path: '*', element: <Navigate to="/admin/login" replace /> },
]);
