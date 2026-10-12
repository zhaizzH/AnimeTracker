import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Skeleton } from './components/ui/skeleton';
import { AdminLayout } from './layouts/AdminLayout';
import { RequireAdmin } from './guards';
import AdminLogin from './components/auth/auth-page';
const withLoading = (el: React.ReactNode) => <Suspense fallback={<Skeleton className="mx-auto my-10 h-8 w-24" aria-hidden />}>{el}</Suspense>;
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Subjects = lazy(() => import('./pages/Subjects'));
const Users = lazy(() => import('./pages/Users'));
const ImportPage = lazy(() => import('./pages/Import'));
const Logs = lazy(() => import('./pages/Logs'));
const AgentConfig = lazy(() => import('./pages/AgentConfig'));
const AgentChat = lazy(() => import('./pages/AgentChat'));
const NotFound = lazy(() => import('./pages/NotFound'));

// 管理端部署在独立端口 :8081 的站点根（docs/deploy/nginx/animetracker.conf），
// 因此路由不带 /admin 前缀——带前缀会让本地与生产的可用路径不一致。
export const router = createBrowserRouter([
  { path: '/login', element: <AdminLogin /> },
  { path: '/', element: <RequireAdmin><AdminLayout /></RequireAdmin>, children: [
    { index: true, element: <Navigate to="/dashboard" replace /> },
    { path: 'dashboard', element: withLoading(<Dashboard />) },
    { path: 'subjects', element: withLoading(<Subjects />) },
    { path: 'users', element: withLoading(<Users />) },
    { path: 'import', element: withLoading(<ImportPage />) },
    { path: 'logs', element: withLoading(<Logs />) },
    { path: 'agent-config', element: withLoading(<AgentConfig />) },
    { path: 'agent-chat', element: withLoading(<AgentChat />) },
  ]},
  // 未知路径渲染 404 页，不再一律回登录页——未登录访问时用户根本分不清是路径错了还是要登录。
  { path: '*', element: withLoading(<NotFound />) },
]);
