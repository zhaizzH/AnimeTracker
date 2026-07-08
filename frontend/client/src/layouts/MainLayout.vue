<script setup lang="ts">
import Header from './Header.vue'
import Footer from './Footer.vue'
</script>

<template>
  <div class="flex flex-col min-h-screen" style="background: var(--color-bg);">
    <Header />
    <main class="flex-1 py-8 md:py-10">
      <router-view />
    </main>
    <Footer />
  </div>
</template>
