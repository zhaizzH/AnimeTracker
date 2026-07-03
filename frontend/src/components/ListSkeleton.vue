<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 animate-pulse">
    <div v-for="i in 10" :key="i" class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div class="aspect-[3/4] bg-gray-200" />
      <div class="p-2.5 space-y-2">
        <div class="h-4 bg-gray-200 rounded w-3/4" />
        <div class="h-3 bg-gray-200 rounded w-1/4" />
      </div>
    </div>
  </div>
</template>
