import { createRouter, createWebHistory } from 'vue-router'
import { getActivePinia } from 'pinia'
import MainLayout from '@/layouts/MainLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'Home', component: () => import('@/pages/Home.vue') },
      { path: 'login', name: 'Login', component: () => import('@/pages/Login.vue') },
      { path: 'register', name: 'Register', component: () => import('@/pages/Register.vue') },
      { path: 'search', name: 'Search', component: () => import('@/pages/Search.vue') },
      { path: 'season/:year?/:quarter?', name: 'Season', component: () => import('@/pages/Season.vue') },
      { path: 'subject/:id', name: 'SubjectDetail', component: () => import('@/pages/SubjectDetail.vue') },
      { path: 'tags', name: 'Tags', component: () => import('@/pages/Tags.vue') },
      { path: 'tags/:tag', name: 'TagSubjects', component: () => import('@/pages/TagSubjects.vue') },
      { path: 'profile', name: 'Profile', component: () => import('@/pages/Profile.vue'), meta: { requiresAuth: true } },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('@/pages/admin/Dashboard.vue') },
      { path: 'subjects', name: 'SubjectManage', component: () => import('@/pages/admin/SubjectManage.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('@/pages/admin/Users.vue') },
      { path: 'import', name: 'ImportStatus', component: () => import('@/pages/admin/ImportStatus.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  // 延迟获取 auth store 避免循环依赖
  const pinia = getActivePinia()
  if (!pinia) {
    next()
    return
  }
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore(pinia)

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
