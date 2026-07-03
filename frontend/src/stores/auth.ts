import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserVO } from '@/types'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserVO | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
  }

  async function register(username: string, password: string, email?: string) {
    const res = await authApi.register(username, password, email)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchProfile() {
    if (!token.value) return
    const res = await authApi.getProfile()
    user.value = res
  }

  async function updateProfile(data: { nickname?: string; avatar?: string; email?: string }) {
    const res = await authApi.updateProfile(data)
    user.value = res
  }

  return {
    token, user, isAuthenticated, isAdmin,
    login, register, logout, fetchProfile, updateProfile,
  }
})
