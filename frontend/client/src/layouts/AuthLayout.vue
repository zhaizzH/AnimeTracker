<script setup lang="ts">
import Header from './Header.vue'
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden" style="background: var(--color-bg);">
    <Header />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>
