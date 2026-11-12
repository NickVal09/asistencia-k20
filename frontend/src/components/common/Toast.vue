<template>
  <transition
    enter-active-class="transform ease-out duration-300 transition"
    enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
    enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
    leave-active-class="transition ease-in duration-100"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="show"
      class="fixed bottom-5 right-5 z-50 max-w-md w-full bg-white shadow-xl rounded-xl border pointer-events-auto p-4 flex items-start space-x-3"
      :class="borderClass"
    >
      <div :class="['w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5', iconBgClass]">
        <!-- Success Icon -->
        <svg v-if="type === 'success'" class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        <!-- Error Icon -->
        <svg v-else-if="type === 'error'" class="w-4 h-4 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        <!-- Warning Icon -->
        <svg v-else-if="type === 'warning'" class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
        <!-- Info Icon -->
        <svg v-else class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      </div>

      <div class="flex-1">
        <h4 class="text-sm font-semibold text-slate-900 leading-tight">{{ title }}</h4>
        <p class="text-xs text-slate-600 mt-0.5 whitespace-pre-line">{{ message }}</p>
      </div>

      <button
        @click="$emit('close')"
        class="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-md"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: Boolean,
  type: {
    type: String,
    default: 'info', // 'success', 'error', 'warning', 'info'
  },
  title: String,
  message: String,
})

defineEmits(['close'])

const borderClass = computed(() => {
  switch (props.type) {
    case 'success': return 'border-emerald-200'
    case 'error': return 'border-rose-200'
    case 'warning': return 'border-amber-200'
    default: return 'border-blue-200'
  }
})

const iconBgClass = computed(() => {
  switch (props.type) {
    case 'success': return 'bg-emerald-50'
    case 'error': return 'bg-rose-50'
    case 'warning': return 'bg-amber-50'
    default: return 'bg-blue-50'
  }
})
</script>

