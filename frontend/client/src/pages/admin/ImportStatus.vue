<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Download, RefreshCw, CheckCircle, AlertCircle, Loader, Clock } from '@lucide/vue'
import { adminApi } from '@/api/admin'
import type { ImportStatusVO, ImportRecordVO } from '@/types'

const loading = ref(true)
const importStatus = ref<ImportStatusVO | null>(null)
const runningImport = ref(false)
const importError = ref('')
let refreshTimer: ReturnType<typeof setInterval> | null = null

const hasRunningImport = computed(() => {
  return importStatus.value?.recentRecords?.some(r => r.status === 'RUNNING') ?? false
})

async function fetchStatus() {
  try {
    const res = await adminApi.getImportStatus()
    importStatus.value = res.data.data
  } catch (e) {
    console.error('Failed to fetch import status', e)
  } finally {
    loading.value = false
  }
}

async function handleRunImport() {
  runningImport.value = true
  importError.value = ''
  try {
    await adminApi.runImport()
    await fetchStatus()
    startAutoRefresh()
  } catch (e: any) {
    importError.value = e?.response?.data?.message || '导入启动失败，请稍后重试'
    console.error('Failed to run import', e)
  } finally {
    runningImport.value = false
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(async () => {
    await fetchStatus()
    if (!hasRunningImport.value) {
      stopAutoRefresh()
    }
  }, 5000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
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

function getStatusBg(status: string): string {
  switch (status) {
    case 'RUNNING': return 'bg-blue-500/10'
    case 'COMPLETED': return 'bg-green-500/10'
    case 'FAILED': return 'bg-red-500/10'
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

const latestRecord = computed<ImportRecordVO | null>(() => {
  if (!importStatus.value?.recentRecords?.length) return null
  return importStatus.value.recentRecords[0]
})

onMounted(async () => {
  await fetchStatus()
  if (hasRunningImport.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div>
      <h1 class="page-title">数据导入</h1>
      <p class="page-subtitle mt-1">从 Bangumi 导入番剧数据</p>
    </div>

    <!-- Import Action Card -->
    <div class="app-card p-5 md:p-6">
      <div class="flex flex-col md:flex-row md:items-center gap-4 md:gap-6">
        <div class="flex-1">
          <h2 class="text-lg font-bold mb-1" style="color: var(--color-text)">运行导入</h2>
          <p class="text-sm" style="color: var(--color-text-secondary)">
            从 Bangumi 数据源导入当季番剧数据。导入过程可能需要几分钟，请勿关闭页面。
          </p>
          <p class="text-sm mt-2" style="color: var(--color-text-secondary)">
            <Clock :size="14" class="inline mr-1 -mt-0.5" />
            上次导入：{{ formatDate(importStatus?.lastImportedAt ?? null) }}
          </p>
        </div>
        <div class="flex-shrink-0">
          <button
            class="btn-primary w-full md:w-auto"
            :disabled="runningImport || hasRunningImport"
            @click="handleRunImport"
          >
            <Loader v-if="runningImport || hasRunningImport" :size="16" class="animate-spin" />
            <Download v-else :size="16" />
            {{ runningImport || hasRunningImport ? '导入中...' : '运行导入' }}
          </button>
        </div>
      </div>

      <!-- Error message -->
      <div
        v-if="importError"
        class="mt-4 p-3 rounded-xl bg-red-500/10 text-red-500 text-sm flex items-center gap-2"
      >
        <AlertCircle :size="16" />
        {{ importError }}
      </div>
    </div>

    <!-- Current Status Indicator -->
    <div v-if="latestRecord" class="app-card p-5 md:p-6">
      <h2 class="section-title mb-4">当前状态</h2>
      <div class="flex items-center gap-4">
        <div
          class="w-12 h-12 rounded-xl flex items-center justify-center"
          :class="{
            'bg-blue-500/10': latestRecord.status === 'RUNNING',
            'bg-green-500/10': latestRecord.status === 'COMPLETED',
            'bg-red-500/10': latestRecord.status === 'FAILED',
          }"
        >
          <Loader v-if="latestRecord.status === 'RUNNING'" :size="22" class="animate-spin text-blue-500" />
          <CheckCircle v-else-if="latestRecord.status === 'COMPLETED'" :size="22" class="text-green-500" />
          <AlertCircle v-else-if="latestRecord.status === 'FAILED'" :size="22" class="text-red-500" />
        </div>
        <div>
          <p class="font-semibold" :class="getStatusColor(latestRecord.status)">
            {{ getStatusLabel(latestRecord.status) }}
            <span v-if="latestRecord.status === 'RUNNING'" class="text-sm font-normal" style="color: var(--color-text-secondary)">
              &mdash; 正在导入 {{ latestRecord.season }} 数据，每 5 秒自动刷新
            </span>
          </p>
          <p class="text-sm mt-0.5" style="color: var(--color-text-secondary)">
            {{ latestRecord.season }} &middot;
            已导入 {{ latestRecord.subjectCount }} 条 &middot;
            开始于 {{ formatDate(latestRecord.startedAt) }}
          </p>
          <p v-if="latestRecord.status === 'FAILED' && latestRecord.errorMessage" class="text-sm text-red-500 mt-1">
            {{ latestRecord.errorMessage }}
          </p>
        </div>
      </div>
    </div>

    <!-- Import History Table -->
    <div class="app-card overflow-hidden">
      <div class="p-5 md:p-6 border-b flex items-center justify-between" style="border-color: var(--color-border)">
        <h2 class="section-title">导入历史</h2>
        <button
          class="btn-ghost p-2 rounded-lg"
          title="刷新"
          @click="fetchStatus"
        >
          <RefreshCw :size="16" :class="{ 'animate-spin': loading }" />
        </button>
      </div>

      <!-- Loading -->
      <template v-if="loading">
        <div class="p-5 md:p-6 space-y-3">
          <div v-for="i in 4" :key="i" class="flex items-center gap-4">
            <div class="app-skeleton h-5 w-10"></div>
            <div class="app-skeleton h-5 w-24"></div>
            <div class="app-skeleton h-5 w-36"></div>
            <div class="app-skeleton h-5 w-36"></div>
            <div class="app-skeleton h-5 w-16"></div>
            <div class="app-skeleton h-5 w-14"></div>
            <div class="app-skeleton h-5 w-24"></div>
          </div>
        </div>
      </template>

      <!-- Empty -->
      <template v-else-if="!importStatus?.recentRecords?.length">
        <div class="p-10 text-center" style="color: var(--color-text-secondary)">
          <Download :size="40" class="mx-auto mb-3 opacity-30" />
          <p class="text-sm">暂无导入记录</p>
          <p class="text-xs mt-1">点击上方「运行导入」开始首次数据导入</p>
        </div>
      </template>

      <!-- Data Table -->
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: var(--color-hover)">
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">ID</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">Season</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">开始时间</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">完成时间</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">状态</th>
                <th class="text-right px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">导入数量</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">错误信息</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(record, index) in importStatus.recentRecords"
                :key="record.id"
                class="border-t transition-colors"
                :style="{
                  borderColor: 'var(--color-border)',
                  background: index % 2 === 1 ? 'var(--color-hover)' : 'transparent',
                }"
                @mouseover="$event.currentTarget.style.background = 'var(--color-hover)'"
                @mouseleave="$event.currentTarget.style.background = index % 2 === 1 ? 'var(--color-hover)' : 'transparent'"
              >
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ record.id }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap font-medium" style="color: var(--color-text)">
                  {{ record.season }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ formatDate(record.startedAt) }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ formatDate(record.completedAt) }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span
                    class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
                    :class="[getStatusBg(record.status), getStatusColor(record.status)]"
                  >
                    <Loader v-if="record.status === 'RUNNING'" :size="12" class="animate-spin" />
                    <CheckCircle v-else-if="record.status === 'COMPLETED'" :size="12" />
                    <AlertCircle v-else-if="record.status === 'FAILED'" :size="12" />
                    {{ getStatusLabel(record.status) }}
                  </span>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap text-right" style="color: var(--color-text)">
                  {{ record.subjectCount }}
                </td>
                <td class="px-5 py-3.5 max-w-[240px]">
                  <span
                    v-if="record.errorMessage"
                    class="text-xs text-red-500 truncate block"
                    :title="record.errorMessage"
                  >
                    {{ record.errorMessage }}
                  </span>
                  <span v-else style="color: var(--color-text-secondary)">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>
