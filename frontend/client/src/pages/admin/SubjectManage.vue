<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Pencil, Trash2, Plus, Search, X, Film } from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import { adminApi } from '@/api/admin'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { SubjectListItem, CreateSubjectRequest, UpdateSubjectRequest } from '@/types'
import { SUBJECT_TYPES } from '@/types'

const loading = ref(true)
const subjects = ref<SubjectListItem[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20
const searchQuery = ref('')

// Modal state
const showModal = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const saving = ref(false)

// Delete confirmation
const showDeleteConfirm = ref(false)
const deletingId = ref<number | null>(null)
const deletingName = ref('')
const deleting = ref(false)

// Form data
const form = ref({
  name: '',
  nameCn: '',
  bangumiId: '',
  summary: '',
  type: '',
  eps: '',
  airDate: '',
  image: '',
})

function resetForm() {
  form.value = {
    name: '',
    nameCn: '',
    bangumiId: '',
    summary: '',
    type: '',
    eps: '',
    airDate: '',
    image: '',
  }
}

function openCreateModal() {
  modalMode.value = 'create'
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEditModal(subject: SubjectListItem) {
  modalMode.value = 'edit'
  editingId.value = subject.id
  form.value = {
    name: subject.name,
    nameCn: subject.nameCn || '',
    bangumiId: '',
    summary: '',
    type: subject.type ? String(subject.type) : '',
    eps: subject.eps ? String(subject.eps) : '',
    airDate: subject.airDate || '',
    image: subject.image || '',
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingId.value = null
  resetForm()
}

async function fetchSubjects() {
  loading.value = true
  try {
    const res = await subjectsApi.getList({
      page: currentPage.value,
      size: pageSize,
    })
    const data = res.data.data
    subjects.value = data.content
    totalPages.value = Math.ceil(data.total / data.size) || 1
  } catch (e) {
    console.error('Failed to fetch subjects', e)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!form.value.name.trim()) return

  saving.value = true
  try {
    const payload: CreateSubjectRequest | UpdateSubjectRequest = {
      name: form.value.name.trim(),
      nameCn: form.value.nameCn.trim() || undefined,
      summary: form.value.summary.trim() || undefined,
      type: form.value.type ? Number(form.value.type) : undefined,
      eps: form.value.eps ? Number(form.value.eps) : undefined,
      airDate: form.value.airDate || undefined,
      image: form.value.image.trim() || undefined,
    }

    if (modalMode.value === 'create') {
      const createPayload = payload as CreateSubjectRequest
      if (form.value.bangumiId) {
        createPayload.bangumiId = Number(form.value.bangumiId)
      }
      await adminApi.createSubject(createPayload)
    } else if (editingId.value !== null) {
      await adminApi.updateSubject(editingId.value, payload)
    }

    closeModal()
    await fetchSubjects()
  } catch (e) {
    console.error('Failed to save subject', e)
  } finally {
    saving.value = false
  }
}

function confirmDelete(subject: SubjectListItem) {
  deletingId.value = subject.id
  deletingName.value = subject.nameCn || subject.name
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (deletingId.value === null) return
  deleting.value = true
  try {
    await adminApi.deleteSubject(deletingId.value)
    showDeleteConfirm.value = false
    deletingId.value = null
    await fetchSubjects()
  } catch (e) {
    console.error('Failed to delete subject', e)
  } finally {
    deleting.value = false
  }
}

function onPageChange(page: number) {
  currentPage.value = page
}

function handleSearch() {
  currentPage.value = 1
  fetchSubjects()
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

watch(currentPage, fetchSubjects)
onMounted(fetchSubjects)
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div>
      <h1 class="page-title">番剧管理</h1>
      <p class="page-subtitle mt-1">管理所有番剧条目数据</p>
    </div>

    <!-- Toolbar -->
    <div class="app-card p-4 md:p-5">
      <div class="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div class="relative flex-1">
          <Search :size="16" class="absolute left-3.5 top-1/2 -translate-y-1/2" style="color: var(--color-text-secondary)" />
          <input
            v-model="searchQuery"
            type="text"
            class="input-field pl-10"
            placeholder="搜索番剧名称..."
            @keyup.enter="handleSearch"
          />
        </div>
        <button class="btn-primary whitespace-nowrap" @click="openCreateModal">
          <Plus :size="16" />
          新建番剧
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="app-card overflow-hidden">
      <!-- Loading Skeletons -->
      <template v-if="loading">
        <div class="p-5 md:p-6 space-y-4">
          <div v-for="i in 6" :key="i" class="flex items-center gap-4">
            <div class="app-skeleton h-5 w-10"></div>
            <div class="app-skeleton h-12 w-10 rounded"></div>
            <div class="app-skeleton h-5 flex-1"></div>
            <div class="app-skeleton h-5 w-12"></div>
            <div class="app-skeleton h-5 w-10"></div>
            <div class="app-skeleton h-5 w-24"></div>
            <div class="app-skeleton h-5 w-20"></div>
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <template v-else-if="subjects.length === 0">
        <EmptyState
          :icon="Film"
          title="暂无番剧数据"
          description="点击「新建番剧」添加第一条记录"
          actionText="新建番剧"
          @click="openCreateModal"
        />
      </template>

      <!-- Data Table -->
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr style="background: var(--color-hover)">
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">ID</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">封面</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">名称</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">评分</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">集数</th>
                <th class="text-left px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">播出日期</th>
                <th class="text-right px-5 py-3 font-medium whitespace-nowrap" style="color: var(--color-text-secondary)">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(subject, index) in subjects"
                :key="subject.id"
                class="border-t transition-colors"
                :style="{
                  borderColor: 'var(--color-border)',
                  background: index % 2 === 1 ? 'var(--color-hover)' : 'transparent',
                }"
                @mouseover="$event.currentTarget.style.background = 'var(--color-hover)'"
                @mouseleave="$event.currentTarget.style.background = index % 2 === 1 ? 'var(--color-hover)' : 'transparent'"
              >
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ subject.id }}
                </td>
                <td class="px-5 py-3.5">
                  <div class="w-10 h-14 rounded-lg overflow-hidden flex-shrink-0" style="background: var(--color-hover)">
                    <img
                      v-if="subject.image"
                      :src="subject.image"
                      :alt="subject.nameCn || subject.name"
                      class="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <Film :size="16" style="color: var(--color-text-secondary)" class="opacity-40" />
                    </div>
                  </div>
                </td>
                <td class="px-5 py-3.5">
                  <div class="max-w-[260px]">
                    <p class="font-medium truncate" style="color: var(--color-text)">
                      {{ subject.nameCn || subject.name }}
                    </p>
                    <p
                      v-if="subject.nameCn && subject.name !== subject.nameCn"
                      class="text-xs truncate mt-0.5"
                      style="color: var(--color-text-secondary)"
                    >
                      {{ subject.name }}
                    </p>
                  </div>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span v-if="subject.score" class="badge-score">{{ subject.score.toFixed(1) }}</span>
                  <span v-else style="color: var(--color-text-secondary)">-</span>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text)">
                  {{ subject.eps || '-' }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap" style="color: var(--color-text-secondary)">
                  {{ formatDate(subject.airDate) }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      class="btn-ghost p-2 rounded-lg"
                      title="编辑"
                      @click="openEditModal(subject)"
                    >
                      <Pencil :size="15" />
                    </button>
                    <button
                      class="btn-ghost p-2 rounded-lg text-red-500 hover:text-red-600"
                      title="删除"
                      @click="confirmDelete(subject)"
                    >
                      <Trash2 :size="15" />
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

    <!-- Create / Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>

        <!-- Modal Content -->
        <div
          class="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl p-6 md:p-8 animate-slide-up"
          style="background: var(--color-card)"
        >
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold" style="color: var(--color-text)">
              {{ modalMode === 'create' ? '新建番剧' : '编辑番剧' }}
            </h2>
            <button class="btn-ghost p-2 rounded-lg" @click="closeModal">
              <X :size="18" />
            </button>
          </div>

          <form class="space-y-4" @submit.prevent="handleSave">
            <!-- Name -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                名称 <span class="text-red-500">*</span>
              </label>
              <input v-model="form.name" type="text" class="input-field" placeholder="日文原名" required />
            </div>

            <!-- Name CN -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                中文名称
              </label>
              <input v-model="form.nameCn" type="text" class="input-field" placeholder="中文译名" />
            </div>

            <!-- Bangumi ID (create only) -->
            <div v-if="modalMode === 'create'">
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                Bangumi ID
              </label>
              <input v-model="form.bangumiId" type="number" class="input-field" placeholder="Bangumi 条目 ID" />
            </div>

            <!-- Summary -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                简介
              </label>
              <textarea
                v-model="form.summary"
                class="input-field min-h-[80px] resize-y"
                placeholder="番剧简介"
              ></textarea>
            </div>

            <!-- Type & Eps row -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                  类型
                </label>
                <select v-model="form.type" class="input-field">
                  <option value="">请选择</option>
                  <option v-for="(label, val) in SUBJECT_TYPES" :key="val" :value="val">
                    {{ label }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                  集数
                </label>
                <input v-model="form.eps" type="number" class="input-field" placeholder="集数" min="0" />
              </div>
            </div>

            <!-- Air Date -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                播出日期
              </label>
              <input v-model="form.airDate" type="date" class="input-field" />
            </div>

            <!-- Image URL -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">
                封面图片 URL
              </label>
              <input v-model="form.image" type="url" class="input-field" placeholder="https://..." />
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-3 pt-2">
              <button type="button" class="btn-secondary" @click="closeModal">取消</button>
              <button type="submit" class="btn-primary" :disabled="saving || !form.name.trim()">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="showDeleteConfirm = false"
      >
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        <div
          class="relative w-full max-w-sm rounded-2xl p-6 md:p-8 animate-slide-up text-center"
          style="background: var(--color-card)"
        >
          <div class="w-14 h-14 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <Trash2 :size="24" class="text-red-500" />
          </div>
          <h3 class="text-lg font-bold mb-2" style="color: var(--color-text)">确认删除</h3>
          <p class="text-sm mb-6" style="color: var(--color-text-secondary)">
            确定要删除「{{ deletingName }}」吗？此操作不可撤销。
          </p>
          <div class="flex items-center justify-center gap-3">
            <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
            <button class="btn-danger" :disabled="deleting" @click="handleDelete">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
