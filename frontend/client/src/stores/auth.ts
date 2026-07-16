import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserVO, LoginRequest, RegisterRequest, UpdateProfileRequest, VerifyEmailRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserVO | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const res = await authApi.login(data)
      token.value = res.data.data.token
      user.value = res.data.data.user
      localStorage.setItem('token', res.data.data.token)
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      await authApi.register(data)
      // register no longer returns token; user must verify email
    } finally {
      loading.value = false
    }
  }

  async function verifyEmail(data: VerifyEmailRequest) {
    loading.value = true
    try {
      const res = await authApi.verifyEmail(data)
      token.value = res.data.data.token
      user.value = res.data.data.user
      localStorage.setItem('token', res.data.data.token)
    } finally {
      loading.value = false
    }
  }

  async function resendCode(email: string) {
    loading.value = true
    try {
      await authApi.resendCode(email)
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await authApi.getMe()
      user.value = res.data.data
    } catch {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
    }
  }

  async function updateProfile(data: UpdateProfileRequest) {
    const res = await authApi.updateProfile(data)
    user.value = res.data.data
  }

  return {
    token, user, loading,
    isAuthenticated, isAdmin,
    login, register, resendCode, verifyEmail, logout, fetchMe, updateProfile,
  }
})
