import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserVO, LoginRequest, RegisterRequest, UpdateProfileRequest, VerifyEmailRequest, SendEmailCodeRequest, VerifyEmailCodeRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const user = ref<UserVO | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const res = await authApi.login(data)
      token.value = res.data.data.token
      refreshToken.value = res.data.data.refreshToken
      user.value = res.data.data.user
      localStorage.setItem('token', res.data.data.token)
      localStorage.setItem('refreshToken', res.data.data.refreshToken)
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
      refreshToken.value = res.data.data.refreshToken
      user.value = res.data.data.user
      localStorage.setItem('token', res.data.data.token)
      localStorage.setItem('refreshToken', res.data.data.refreshToken)
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
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await authApi.getMe()
      user.value = res.data.data
    } catch {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
    }
  }

  async function updateProfile(data: UpdateProfileRequest) {
    const res = await authApi.updateProfile(data)
    user.value = res.data.data
  }

  async function sendEmailCode(newEmail: string) {
    loading.value = true
    try {
      await authApi.sendEmailCode({ newEmail })
    } finally {
      loading.value = false
    }
  }

  async function verifyEmailCode(newEmail: string, code: string) {
    loading.value = true
    try {
      await authApi.verifyEmailCode({ newEmail, code })
      // 更新本地 user.email，保持 UI 同步
      if (user.value) {
        user.value.email = newEmail
      }
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    if (!refreshToken.value) throw new Error('no refresh token')
    const res = await authApi.refresh(refreshToken.value)
    if (res.data.code !== 200) throw new Error(res.data.message || 'refresh failed')
    token.value = res.data.data.token
    refreshToken.value = res.data.data.refreshToken
    localStorage.setItem('token', res.data.data.token)
    localStorage.setItem('refreshToken', res.data.data.refreshToken)
    return res.data.data.token
  }

  return {
    token, refreshToken, user, loading,
    isAuthenticated, isAdmin,
    login, register, resendCode, verifyEmail, logout, fetchMe, updateProfile, sendEmailCode, verifyEmailCode, refresh,
  }
})
