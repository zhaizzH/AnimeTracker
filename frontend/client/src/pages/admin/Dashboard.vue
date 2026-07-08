<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Film, Users, Clock, CheckCircle, AlertCircle, Loader } from '@lucide/vue'
import { adminApi } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import type { ImportStatusVO, ImportRecordVO } from '@/types'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const importStatus = ref<ImportStatusVO | null>(null)
const userCount = ref(0)
const runningImport = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const [statusRes, usersRes] = await Promise.all([
      adminApi.getImportStatus(),
      adminApi.getUsers({ page: 1, size: 1 }),
    ])
    importStatus.value = statusRes.data.data
    userCount.value = usersRes.data.data.total
  } catch (e) {
    console.error('Failed to load dashboard data', e)
  } finally {
    loading.value = false
  }
}

async function handleRunImport() {
  runningImport.value = true
  try {
    await adminApi.runImport()
    await fetchData()
  } catch (e) {
    console.error('Failed to run import', e)
  } finally {
    runningImport.value = false
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '从未导入'
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'RUNNING': return 'text-blue-500'
    case 'COMPLETED': return 'text-green-500'
    case 'FAILED': return 'text-red-500'
    default: return ''
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'RUNNING': return '运行中'
    case 'COMPLETED': return '已完成'
    case 'FAILED': return '失败'
    default: return status
  }
}

function getLatestStatus(): string | null {
  if (!importStatus.value?.recentRecords?.length) return null
  return importStatus.value.recentRecords[0].status
}

onMounted(fetchData)
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <!-- Header -->
    <div>
      <h1 class="page-title">管理后台</h1>
      <p class="page-subtitle mt-1">
        欢迎回来，{{ auth.user?.nickname || auth.user?.username || '管理员' }}
      </p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
      <!-- Total Subjects -->
      <div class="app-card p-5 md:p-6">
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center">
            <Film :size="22" class="text-primary-500" />
          </div>
          <div class="min-w-0">
            <template v-if="loading">
              <div class="app-skeleton h-7 w-16 mb-1"></div>
            </template>
            <template v-else>
              <p class="text-2xl font-bold" style="color: var(--color-text)">
                {{ importStatus?.totalSubjects ?? 0 }}
              </p>
            </template>
            <p class="text-sm mt-0.5" style="color: var(--color-text-secondary)">番剧总数</p>
          </div>
        </div>
      </div>

      <!-- User Count -->
      <div class="app-card p-5 md:p-6">
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-accent-purple/10 flex items-center justify-center">
            <Users :size="22" class="text-accent-purple" />
          </div>
          <div class="min-w-0">
            <template v-if="loading">
              <div class="app-skeleton h-7 w-16 mb-1"></div>
            </template>
            <template v-else>
              <p class="text-2xl font-bold" style="color: var(--color-text)">
                {{ userCount }}
              </p>
            </template>
            <p class="text-sm mt-0.5" style="color: var(--color-text-secondary)">用户数量</p>
          </div>
        </div>
      </div>

      <!-- Last Import -->
      <div class="app-card p-5 md:p-6">
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-accent-orange/10 flex items-center justify-center">
            <Clock :size="22" class="text-accent-orange" />
          </div>
          <div class="min-w-0">
            <template v-if="loading">
              <div class="app-skeleton h-7 w-28 mb-1"></div>
            </template>
            <template v-else>
              <p class="text-sm font-semibold truncate" style="color: var(--color-text)">
                {{ formatDate(importStatus?.lastImportedAt ?? null) }}
              </p>
            </template>
            <p class="text-sm mt-0.5" style="color: var(--color-text-secondary)">最近导入</p>
          </div>
        </div>
      </div>

      <!-- Import Status -->
      <div class="app-card p-5 md:p-6">
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-accent-green/10 flex items-center justify-center">
            <CheckCircle :size="22" class="text-accent-green" />
          </div>
          <div class="min-w-0">
            <template v-if="loading">
              <div class="app-skeleton h-7 w-20 mb-1"></div>
            </template>
            <template v-else>
              <template v-if="getLatestStatus()">
                <span
                  class="inline-flex items-center gap-1.5 text-sm font-semibold"
                  :class="getStatusColor(getLatestStatus()!)"
                >
                  <Loader v-if="getLatestStatus() === 'RUNNING'" :size="14" class="animate-spin" />
                  <CheckCircle v-else-if="getLatestStatus() === 'COMPLETED'" :size="14" />
                  <AlertCircle v-else-if="getLatestStatus() === 'FAILED'" :size="14" />
                  {{ getStatusLabel(getLatestStatus()!) }}
                </span>
              </template>
              <template v-else>
                <p class="text-sm font-semibold" style="color: var(--color-text)">无记录</p>
              </template>
            </template>
            <p class="text-sm mt-0.5" style="color: var(--color-text-secondary)">导入状态</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="app-card p-5 md:p-6">
      <h2 class="section-title mb-4">快捷操作</h2>
      <div class="flex flex-wrap gap-3">
        <button
          class="btn-primary"
          :disabled="runningImport"
          @click="handleRunImport"
        >
          <Loader v-if="runningImport" :size="16" class="animate-spin" />
          <Film v-else :size="16" />
          {{ runningImport ? '导入中...' : '运行导入' }}
        </button>
        <button class="btn-secondary" @click="router.push({ name: 'AdminSubjects' })">
          <Film :size="16" />
          管理番剧
        </button>
        <button class="btn-secondary" @click="router.push({ name: 'AdminUsers' })">
          <Users :size="16" />
          管理用户
        </button>
      </div>
    </div>

    <!-- Recent Imports Table -->
    <div class="app-card overflow-hidden">
      <div class="p-5 md:p-6 border-b" style="border-color: var(--color-border)">
        <h2 class="section-title">最近导入记录</h2>
      </div>

      <template v-if="loading">
        <div class="p-5 md:p-6 space-y-3">
          <div v-for="i in 3" :key="i" class="flex items-center gap-4">
            <div class="app-skeleton h-5 w-12"></div>
            <div class="app-skeleton h-5 w-24"></div>
            <div class="app-skeleton h-5 w-32"></div>
            <div class="app-skeleton h-5 w-32"></div>
            <div class="app-skeleton h-5 w-16"></div>
          </div>
        </div>
      </template>

      <template v-else-if="importStatus?.recentRecords?.length">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: var(--color-hover)">
                <th class="text-left px-5 py-3 font-medium" style="color: var(--color-text-secondary)">ID</th>
                <th class="text-left px-5 py-3 font-medium" style="color: var(--color-text-secondary)">Season</th>
                <th class="text-left px-5 py-3 font-medium" style="color: var(--color-text-secondary)">开始时间</th>
                <th class="text-left px-5 py-3 font-medium" style="color: var(--color-text-secondary)">完成时间</th>
                <th class="text-left px-5 py-3 font-medium" style="color: var(--color-text-secondary)">状态</th>
                <th class="text-right px-5 py-3 font-medium" style="color: var(--color-text-secondary)">导入数量</th>
                <th class="text-left px-5 py-3 font-medium" style="color: var(--color-text-secondary)">错误信息</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in importStatus.recentRecords"
                :key="record.id"
                class="border-t transition-colors"
                style="border-color: var(--color-border)"
                @mouseover="$event.currentTarget.style.background = 'var(--color-hover)'"
                @mouseleave="$event.currentTarget.style.background = ''"
              >
                <td class="px-5 py-3.5" style="color: var(--color-text)">{{ record.id }}</td>
                <td class="px-5 py-3.5" style="color: var(--color-text)">{{ record.season }}</td>
                <td class="px-5 py-3.5" style="color: var(--color-text-secondary)">{{ formatDate(record.startedAt) }}</td>
                <td class="px-5 py-3.5" style="color: var(--color-text-secondary)">{{ formatDate(record.completedAt) }}</td>
                <td class="px-5 py-3.5">
                  <span
                    class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
                    :class="{
                      'bg-blue-500/10 text-blue-500': record.status === 'RUNNING',
                      'bg-green-500/10 text-green-500': record.status === 'COMPLETED',
                      'bg-red-500/10 text-red-500': record.status === 'FAILED',
                    }"
                  >
                    <Loader v-if="record.status === 'RUNNING'" :size="12" class="animate-spin" />
                    <CheckCircle v-else-if="record.status === 'COMPLETED'" :size="12" />
                    <AlertCircle v-else-if="record.status === 'FAILED'" :size="12" />
                    {{ getStatusLabel(record.status) }}
                  </span>
                </td>
                <td class="px-5 py-3.5 text-right" style="color: var(--color-text)">{{ record.subjectCount }}</td>
                <td class="px-5 py-3.5 max-w-[200px] truncate" style="color: var(--color-text-secondary)">
                  {{ record.errorMessage || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <template v-else>
        <div class="p-10 text-center" style="color: var(--color-text-secondary)">
          <Clock :size="40" class="mx-auto mb-3 opacity-30" />
          <p class="text-sm">暂无导入记录</p>
        </div>
      </template>
    </div>
  </div>
</template>
