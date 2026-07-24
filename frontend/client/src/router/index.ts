import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('@/pages/Home.vue') },
      { path: 'search', name: 'Search', component: () => import('@/pages/Search.vue') },
      { path: 'season/:year?/:quarter?', name: 'Season', component: () => import('@/pages/Season.vue') },
      { path: 'subject/:id', name: 'SubjectDetail', component: () => import('@/pages/SubjectDetail.vue') },
      { path: 'tags', name: 'Tags', component: () => import('@/pages/Tags.vue') },
      { path: 'tags/:tag', name: 'TagSubjects', component: () => import('@/pages/TagSubjects.vue') },
      { path: 'profile', name: 'Profile', component: () => import('@/pages/Profile.vue'), meta: { requiresAuth: true } },
      { path: 'collections', name: 'Collections', component: () => import('@/pages/Collections.vue'), meta: { requiresAuth: true } },
    ],
  },
  {
    path: '/',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      { path: 'login', name: 'Login', component: () => import('@/pages/Login.vue'), meta: { guest: true } },
      { path: 'register', name: 'Register', component: () => import('@/pages/Register.vue'), meta: { guest: true } },
      { path: 'verify-email', name: 'VerifyEmail', component: () => import('@/pages/VerifyEmail.vue'), meta: { guest: true } },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/Home.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})

router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  if (to.meta.guest && token) {
    return next({ name: 'Home' })
  }

  if (token && to.matched.length > 0) {
    const authStore = useAuthStore()
    if (!authStore.user) {
      await authStore.fetchMe()
    }
  }

  next()
})

export default router
