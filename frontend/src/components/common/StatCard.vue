<template>
  <div class="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs transition-all hover:shadow-md">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">{{ title }}</p>
        <h3 class="text-2xl font-bold tracking-tight text-slate-900 font-mono">{{ value }}</h3>
      </div>
      <div :class="['w-11 h-11 rounded-xl flex items-center justify-center shrink-0', colorClass]">
        <slot name="icon">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </slot>
      </div>
    </div>
    <div v-if="subtitle || $slots.footer" class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
      <span v-if="subtitle">{{ subtitle }}</span>
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  colorClass: {
    type: String,
    default: 'bg-blue-50 text-blue-600',
  },
})
</script>

