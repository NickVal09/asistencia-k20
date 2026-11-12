<template>
  <div class="space-y-6">
    <!-- Header del Dispositivo -->
    <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <div class="flex items-center space-x-2">
          <h2 class="text-xl font-bold text-slate-900 tracking-tight">Biométrico ZKTeco K20</h2>
          <span
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
            :class="badgeClase"
          >
            {{ badgeTexto }}
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Estado real de conexión, última sincronización y auditoría de ejecuciones.
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <button
          @click="probarConexion"
          :disabled="probando"
          class="inline-flex items-center px-3.5 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors cursor-pointer disabled:opacity-50"
        >
          <svg class="w-4 h-4 mr-1.5 text-slate-500" :class="{ 'animate-spin': probando }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Probar conexión
        </button>
        <button
          @click="iniciarSync"
          :disabled="syncEnCurso"
          class="inline-flex items-center px-3.5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-xs transition-colors cursor-pointer disabled:opacity-50"
        >
          {{ syncEnCurso ? 'Sincronizando...' : 'Sincronizar con K20' }}
        </button>
      </div>
    </div>

    <!-- Ficha Técnica del K20 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <p class="text-slate-400 text-[11px] font-semibold uppercase">Dirección IP</p>
        <p class="text-lg font-bold font-mono text-slate-900 mt-0.5">{{ estado?.dispositivo?.ip || '192.168.10.69' }}</p>
        <p class="text-[11px] text-slate-500 mt-1">Red local Ethernet</p>
      </div>
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <p class="text-slate-400 text-[11px] font-semibold uppercase">Puerto SDK / Daemon</p>
        <p class="text-lg font-bold font-mono text-slate-900 mt-0.5">{{ estado?.dispositivo?.puerto || 4370 }}</p>
        <p class="text-[11px] text-slate-500 mt-1">Protocolo ZKTeco</p>
      </div>
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <p class="text-slate-400 text-[11px] font-semibold uppercase">Plataforma / Firmware</p>
        <p class="text-lg font-bold font-mono text-slate-900 mt-0.5">{{ estado?.dispositivo?.plataforma || 'ZLM60_TFT' }}</p>
        <p class="text-[11px] text-slate-500 mt-1">Linux Embedded K20</p>
      </div>
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
        <p class="text-slate-400 text-[11px] font-semibold uppercase">Última conexión OK</p>
        <p class="text-sm font-bold font-mono text-slate-900 mt-0.5">{{ formatDateTime(estado?.dispositivo?.ultima_conexion_ok) }}</p>
        <p class="text-[11px] text-slate-500 mt-1">{{ estado?.dispositivo?.ultimo_error || 'Sin errores recientes' }}</p>
      </div>
    </div>

    <!-- Detalle de sincronizacion -->
    <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
      <h3 class="text-sm font-bold text-slate-900">Última sincronización completada</h3>
      <div v-if="estado?.ultima_sincronizacion_completada" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Modo</span>
          <span class="font-semibold text-slate-800">{{ estado.ultima_sincronizacion_completada.modo || '-' }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Leídas</span>
          <span class="font-semibold text-slate-800">{{ estado.ultima_sincronizacion_completada.total_leidos }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Nuevas</span>
          <span class="font-semibold text-emerald-700">{{ estado.ultima_sincronizacion_completada.nuevos_registros }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Duplicadas</span>
          <span class="font-semibold text-slate-800">{{ estado.ultima_sincronizacion_completada.duplicados_omitidos }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Errores</span>
          <span class="font-semibold text-rose-700">{{ estado.ultima_sincronizacion_completada.errores }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Duración</span>
          <span class="font-semibold text-slate-800">{{ estado.ultima_sincronizacion_completada.duracion_segundos || '-' }}s</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Última marcación válida</span>
          <span class="font-semibold text-slate-800">{{ formatDateTime(estado.ultima_sincronizacion_completada.ultima_marcacion) }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
          <span class="text-slate-500 block mb-1">Finalizada</span>
          <span class="font-semibold text-slate-800">{{ formatDateTime(estado.ultima_sincronizacion_completada.finalizado_el) }}</span>
        </div>
      </div>
      <p v-else class="text-xs text-slate-500">Aún no se ha sincronizado con el K20.</p>

      <div v-if="syncEnCurso" class="flex items-center space-x-3 text-sm text-blue-600 bg-blue-50/50 p-3 rounded-lg border border-blue-100">
        <svg class="animate-spin w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span>Sincronizando... {{ syncFase }}</span>
      </div>
      <div v-if="syncResultado" class="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 text-xs">
        Resultado: {{ syncResultado.estado }} | Leídos: {{ syncResultado.total_leidos }} |
        Nuevos: {{ syncResultado.nuevos_registros }} | Duplicados: {{ syncResultado.duplicados_omitidos }} |
        Errores: {{ syncResultado.errores }}
      </div>
    </div>

    <!-- Historial de sincronizaciones -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-slate-900">Historial de Sincronizaciones con K20</h3>
          <p class="text-xs text-slate-500">Auditoría de descargas y omisiones de duplicados</p>
        </div>
        <button @click="fetchHistory" class="text-xs text-blue-600 hover:text-blue-800 font-medium">Actualizar Lista</button>
      </div>

      <div v-if="history.length === 0" class="p-10 text-center text-xs text-slate-500">
        No hay sincronizaciones registradas.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <th class="py-3 px-4 font-mono">ID</th>
              <th class="py-3 px-4">Modo</th>
              <th class="py-3 px-4 text-center">Estado</th>
              <th class="py-3 px-4 text-right">Leídos</th>
              <th class="py-3 px-4 text-right">Nuevos</th>
              <th class="py-3 px-4 text-right">Duplicados</th>
              <th class="py-3 px-4 text-right">Errores</th>
              <th class="py-3 px-4 text-right">Duración</th>
              <th class="py-3 px-4">Finalizada</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 font-mono text-[11px]">
            <tr v-for="h in history" :key="h.id" class="hover:bg-slate-50/70">
              <td class="py-2.5 px-4 text-slate-400">{{ h.id }}</td>
              <td class="py-2.5 px-4 font-sans font-medium text-slate-700">{{ h.modo || h.origen }}</td>
              <td class="py-2.5 px-4 text-center">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase font-sans"
                  :class="h.estado === 'completado' ? 'bg-emerald-100 text-emerald-800' : (h.estado === 'fallido' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800')"
                >
                  {{ h.estado }}
                </span>
              </td>
              <td class="py-2.5 px-4 text-right text-slate-800">{{ h.total_leidos }}</td>
              <td class="py-2.5 px-4 text-right font-bold text-emerald-600">{{ h.nuevos_registros }}</td>
              <td class="py-2.5 px-4 text-right text-slate-500">{{ h.duplicados_omitidos }}</td>
              <td class="py-2.5 px-4 text-right text-rose-600 font-bold">{{ h.errores }}</td>
              <td class="py-2.5 px-4 text-right text-slate-500">{{ h.duracion_segundos || '-' }}s</td>
              <td class="py-2.5 px-4 text-slate-500 font-sans text-xs">{{ formatDateTime(h.finalizado_el || h.iniciado_el) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { api } from '../services/api'

const showToast = inject('showToast', (type, title, message) => {
  console.log(type, title, message)
})

const estado = ref(null)
const history = ref([])
const syncEnCurso = ref(false)
const syncFase = ref('')
const syncResultado = ref(null)
const probando = ref(false)

const badgeTexto = computed(() => {
  const e = estado.value?.estado_conexion
  if (e === 'comprobada') return 'Conexión comprobada'
  if (e === 'sin_conexion') return 'Sin conexión'
  return 'Configurado'
})

const badgeClase = computed(() => {
  const e = estado.value?.estado_conexion
  if (e === 'comprobada') return 'bg-emerald-100 text-emerald-800'
  if (e === 'sin_conexion') return 'bg-rose-100 text-rose-800'
  return 'bg-slate-100 text-slate-700'
})

async function refrescarEstado() {
  try {
    const res = await api.getEstadoSincronizacion()
    estado.value = res.data
  } catch (e) {
    estado.value = { estado_conexion: 'sin_conexion', dispositivo: null }
  }
}

async function fetchHistory() {
  try {
    const res = await api.getHistorialSincronizacion()
    history.value = res.data
  } catch (e) {
    console.error('Error al obtener historial:', e)
  }
}

async function probarConexion() {
  probando.value = true
  try {
    const res = await api.probarConexionK20()
    showToast(res.data.conexion_ok ? 'success' : 'error', res.data.conexion_ok ? 'Conexión OK' : 'Sin conexión', res.data.mensaje)
    await refrescarEstado()
  } catch (err) {
    showToast('error', 'Error', err.response?.data?.detail || err.message)
  } finally {
    probando.value = false
  }
}

let pollTimer = null
async function iniciarSync() {
  syncResultado.value = null
  syncFase.value = 'Iniciando...'
  try {
    const res = await api.iniciarSincronizacionK20()
    syncEnCurso.value = true
    syncFase.value = res.data.mensaje
    pollTimer = setInterval(async () => {
      const r = await api.getEstadoSincronizacion()
      estado.value = r.data
      const actual = r.data.ejecucion_actual
      if (actual) {
        syncFase.value = actual.mensaje_detalle || 'Procesando...'
        if (actual.estado !== 'en_progreso') {
          syncResultado.value = actual
          syncEnCurso.value = false
          clearInterval(pollTimer)
          pollTimer = null
          await fetchHistory()
          window.dispatchEvent(new CustomEvent('records-imported'))
        }
      } else {
        syncEnCurso.value = false
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
      }
    }, 2000)
    if (!res.data.iniciado) {
      showToast('info', 'Sincronización', res.data.mensaje)
    }
  } catch (err) {
    showToast('error', 'Error al Sincronizar', err.response?.data?.detail || err.message)
    syncEnCurso.value = false
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return d.toLocaleString('es-PE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

onMounted(() => {
  refrescarEstado()
  fetchHistory()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>
