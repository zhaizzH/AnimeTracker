<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t mt-auto" style="border-color: var(--color-border);">
    <div class="app-container py-8">
      <div class="flex flex-col items-center gap-3 sm:gap-4 text-center">
        <!-- Branding -->
        <div class="text-base font-bold select-none">
          <span class="text-primary-500">Anime</span><span style="color: var(--color-text);">Tracker</span>
        </div>

        <!-- Links -->
        <div class="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-sm" style="color: var(--color-text-secondary);">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            class="transition-colors duration-200 hover:text-primary-500"
          >
            GitHub
          </a>
          <span class="w-px h-3" style="background: var(--color-border);"></span>
          <a
            href="https://bgm.tv"
            target="_blank"
            rel="noopener noreferrer"
            class="transition-colors duration-200 hover:text-primary-500"
          >
            Bangumi API
          </a>
          <span class="w-px h-3" style="background: var(--color-border);"></span>
          <span class="transition-colors duration-200">About</span>
        </div>

        <!-- Copyright -->
        <p class="text-xs" style="color: var(--color-text-secondary); opacity: 0.7;">
          &copy; {{ year }} AnimeTracker. Powered by Bangumi.
        </p>
      </div>
    </div>
  </footer>
</template>
