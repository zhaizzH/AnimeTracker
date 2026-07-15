<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ChatWidget from '@/components/chat/ChatWidget.vue'

const auth = useAuthStore()

onMounted(() => {
  if (auth.token && !auth.user) {
    auth.fetchMe()
  }
})
</script>

<template>
  <router-view />
  <ChatWidget v-if="auth.token" />
</template>
