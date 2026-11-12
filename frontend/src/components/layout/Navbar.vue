<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between shadow-xs">
    <!-- Breadcrumb / Titulo de Sección -->
    <div class="flex items-center space-x-3">
      <div class="flex items-center text-slate-500 text-sm">
        <span class="font-medium text-slate-400">Sistema</span>
        <span class="mx-2 text-slate-300">/</span>
        <span class="font-semibold text-slate-800">{{ currentRouteName }}</span>
      </div>
    </div>

    <!-- Acciones y Estado del Dispositivo -->
    <div class="flex items-center space-x-3">
      <!-- Indicador real del K20 (no se pone verde solo por la IP) -->
      <div
        class="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full border text-xs"
        :class="estadoClase"
      >
        <span class="relative flex h-2 w-2">
          <span class="relative inline-flex rounded-full h-2 w-2" :class="puntoClase"></span>
        </span>
        <span class="font-medium">{{ estadoTexto }}</span>
        <span class="font-mono text-[10px] opacity-70">4370</span>
      </div>

      <!-- Reloj en tiempo real -->
      <div class="hidden md:flex items-center space-x-1.5 text-xs text-slate-500 font-mono bg-slate-50 px-2.5 py-1.5 rounded border border-slate-200">
        <span>{{ liveTime }}</span>
      </div>

      <!-- Boton Sincronizar CSV (existente) -->
      <button
        @click="$emit('open-import-modal')"
        class="inline-flex items-center px-3.5 py-1.5 border border-transparent text-xs font-semibold rounded-lg shadow-xs text-white bg-blue-600 hover:bg-blue-700 transition-colors focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer"
      >
        <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
        </svg>
        Sincronizar CSV
      </button>

      <!-- Boton Sincronizar con K20 (Fase 2) -->
      <button
        @click="$emit('open-sync-modal')"
        class="inline-flex items-center px-3.5 py-1.5 border border-slate-300 text-xs font-semibold rounded-lg text-slate-700 bg-white hover:bg-slate-50 transition-colors cursor-pointer"
      >
        <svg class="w-3.5 h-3.5 mr-1.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        Sincronizar con K20
      </button>

      <!-- Cerrar sesion -->
      <button
        @click="$emit('logout')"
        class="inline-flex items-center px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
        title="Cerrar sesión"
      >
        Salir
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../services/api'

defineEmits(['open-import-modal', 'open-sync-modal', 'logout'])

const route = useRoute()
const currentRouteName = computed(() => route.meta.title || route.name || 'Dashboard')

const liveTime = ref('')
let timer = null
let estadoTimer = null

const estadoConexion = ref('configurado') // configurado | comprobada | sin_conexion
const ultimoError = ref(null)

const estadoClase = computed(() => {
  if (estadoConexion.value === 'comprobada') return 'bg-emerald-50 border-emerald-200 text-emerald-800'
  if (estadoConexion.value === 'sin_conexion') return 'bg-rose-50 border-rose-200 text-rose-800'
  return 'bg-slate-100 border-slate-200 text-slate-700'
})

const puntoClase = computed(() => {
  if (estadoConexion.value === 'comprobada') return 'bg-emerald-500'
  if (estadoConexion.value === 'sin_conexion') return 'bg-rose-500'
  return 'bg-slate-400'
})

const estadoTexto = computed(() => {
  if (estadoConexion.value === 'comprobada') return 'K20: Conexión comprobada'
  if (estadoConexion.value === 'sin_conexion') return 'K20: Sin conexión'
  return 'K20: Configurado'
})

async function refrescarEstado() {
  try {
    const res = await api.getK20Status()
    estadoConexion.value = res.data.estado || (res.data.conectado ? 'comprobada' : 'configurado')
    ultimoError.value = res.data.detalles?.ultimo_error || null
  } catch (e) {
    estadoConexion.value = 'sin_conexion'
  }
}

function updateTime() {
  const now = new Date()
  liveTime.value = now.toLocaleDateString('es-PE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' ' + now.toLocaleTimeString('es-PE', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  refrescarEstado()
  estadoTimer = setInterval(refrescarEstado, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (estadoTimer) clearInterval(estadoTimer)
})
</script>
