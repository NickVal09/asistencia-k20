<template>
  <div class="flex flex-col items-center justify-center p-8 space-y-3">
    <div class="relative w-10 h-10">
      <div class="w-10 h-10 rounded-full border-3 border-blue-100"></div>
      <div class="w-10 h-10 rounded-full border-3 border-blue-600 border-t-transparent animate-spin absolute top-0 left-0"></div>
    </div>
    <p v-if="text" class="text-xs font-medium text-slate-500 animate-pulse">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: 'Cargando registros...',
  },
})
</script>

