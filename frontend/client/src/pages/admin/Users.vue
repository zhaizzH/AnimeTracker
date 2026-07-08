<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Users, Shield, ShieldCheck } from '@lucide/vue'
import { adminApi } from '@/api/admin'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { UserVO } from '@/types'

const loading = ref(true)
const users = ref<UserVO[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20

// Role change confirmation
const showRoleConfirm = ref(false)
const targetUser = ref<UserVO | null>(null)
const targetRole = ref<'USER' | 'ADMIN'>('USER')
const updating = ref(false)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await adminApi.getUsers({ page: currentPage.value, size: pageSize })
    const data = res.data.data
    users.value = data.content
    totalPages.value = Math.ceil(data.total / data.size) || 1
  } catch (e) {
    console.error('Failed to fetch users', e)
  } finally {
    loading.value = false
  }
}

function confirmRoleChange(user: UserVO, newRole: 'USER' | 'ADMIN') {
  if (user.role === newRole) return
  targetUser.value = user
  targetRole.value = newRole
  showRoleConfirm.value = true
}

async function handleRoleChange() {
  if (!targetUser.value) return
  updating.value = true
  try {
    await adminApi.updateUserRole(targetUser.value.id, targetRole.value)
    showRoleConfirm.value = false
    targetUser.value = null
    await fetchUsers()
  } catch (e) {
    console.error('Failed to update user role', e)
  } finally {
    updating.value = false
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

function onPageChange(page: number) {
  currentPage.value = page
}

watch(currentPage, fetchUsers)
onMounted(fetchUsers)
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div>
      <h1 class="page-title">用户管理</h1>
      <p class="page-subtitle mt-1">查看和管理平台用户及权限</p>
    </div>

    <!-- Table Card -->
    <div class="app-card overflow-hidden">
      <!-- Loading Skeletons -->
      <template v-if="loading">
        <div class="p-5 md:p-6 space-y-4">
          <div v-for="i in 6" :key="i" class="flex items-center gap-4">
            <div class="app-skeleton h-5 w-10"></div>
            <div class="app-skeleton h-10 w-10 rounded-full"></div>
            <div class="app-skeleton h-5 flex-1"></div>
            <div class="app-skeleton h-5 w-24"></div>
            <div class="app-skeleton h-5 w-32"></div>
            <div class="app-skeleton h-5 w-16"></div>
            <div class="app-skeleton h-5 w-20"></div>
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <template v-else-if="users.length === 0">
        <EmptyState
          :icon="Users"
          title="暂无用户"
          description="还没有注册用户"
        />
      </template>

      <!-- Data Table -->
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: var(--color-hover)">
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">ID</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">头像</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">用户名</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">昵称</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">邮箱</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">角色</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">注册时间</th>
                <th class="text-right px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in users"
                :key="user.id"
                class="border-t transition-colors"
                style="border-color: var(--color-border)"
                @mouseover="$event.currentTarget.style.background = 'var(--color-hover)'"
                @mouseleave="$event.currentTarget.style.background = ''"
              >
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ user.id }}
                </td>
                <td class="px-5 py-3.5">
                  <div class="w-9 h-9 rounded-full overflow-hidden flex-shrink-0" style="background: var(--color-hover)">
                    <img
                      v-if="user.avatar"
                      :src="user.avatar"
                      :alt="user.nickname || user.username"
                      class="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <Users :size="16" style="color: var(--color-text-secondary)" class="opacity-40" />
                    </div>
                  </div>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap font-medium" style="color: var(--color-text)">
                  {{ user.username }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text)">
                  {{ user.nickname || '-' }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ user.email || '-' }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
                    :class="user.role === 'ADMIN'
                      ? 'bg-primary-500/10 text-primary-500'
                      : 'bg-surface-500/10'"
                    :style="user.role === 'USER' ? 'color: var(--color-text-secondary)' : ''"
                  >
                    <ShieldCheck v-if="user.role === 'ADMIN'" :size="12" />
                    <Shield v-else :size="12" />
                    {{ user.role === 'ADMIN' ? '管理员' : '用户' }}
                  </span>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ formatDate(user.createdAt) }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      v-if="user.role === 'USER'"
                      class="btn-ghost p-2 rounded-lg text-xs"
                      title="设为管理员"
                      @click="confirmRoleChange(user, 'ADMIN')"
                    >
                      <ShieldCheck :size="15" class="text-primary-500" />
                      <span class="ml-1">设为管理</span>
                    </button>
                    <button
                      v-else
                      class="btn-ghost p-2 rounded-lg text-xs"
                      title="取消管理员"
                      @click="confirmRoleChange(user, 'USER')"
                    >
                      <Shield :size="15" style="color: var(--color-text-secondary)" />
                      <span class="ml-1">取消管理</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="p-4 md:p-5 border-t" style="border-color: var(--color-border)">
          <Pagination
            :current-page="currentPage"
            :total-pages="totalPages"
            @update:page="onPageChange"
          />
        </div>
      </template>
    </div>

    <!-- Role Change Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showRoleConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="showRoleConfirm = false"
      >
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        <div
          class="relative w-full max-w-sm rounded-2xl p-6 md:p-8 animate-slide-up text-center"
          style="background: var(--color-card)"
        >
          <div
            class="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4"
            :class="targetRole === 'ADMIN' ? 'bg-primary-500/10' : 'bg-surface-500/10'"
          >
            <ShieldCheck v-if="targetRole === 'ADMIN'" :size="24" class="text-primary-500" />
            <Shield v-else :size="24" style="color: var(--color-text-secondary)" />
          </div>
          <h3 class="text-lg font-bold mb-2" style="color: var(--color-text)">确认更改角色</h3>
          <p class="text-sm mb-6" style="color: var(--color-text-secondary)">
            确定要将用户「{{ targetUser?.nickname || targetUser?.username }}」
            {{ targetRole === 'ADMIN' ? '设为管理员' : '取消管理员权限' }}吗？
          </p>
          <div class="flex items-center justify-center gap-3">
            <button class="btn-secondary" @click="showRoleConfirm = false">取消</button>
            <button class="btn-primary" :disabled="updating" @click="handleRoleChange">
              {{ updating ? '更新中...' : '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
