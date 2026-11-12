<template>
  <div class="space-y-6">
    <!-- Header de Bienvenida y Dispositivo -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
      <div>
        <h2 class="text-xl font-bold text-slate-900 tracking-tight">Panel de Control de Asistencia</h2>
        <p class="text-xs text-slate-500 mt-1">
          Historial biométrico consolidado del reloj <strong class="text-slate-700">ZKTeco K20</strong> (Firmware: ZLM60_TFT).
        </p>
      </div>
      <div class="flex items-center space-x-2">
        <router-link
          to="/marcaciones"
          class="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
        >
          Ver Todas las Marcaciones
        </router-link>
        <router-link
          to="/exportaciones"
          class="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-xs transition-colors"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Exportar Datos
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-2xl border border-slate-200 p-12">
      <LoadingSpinner text="Consultando métricas desde MySQL Laragon..." />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center">
      <svg class="w-10 h-10 text-rose-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <h3 class="text-sm font-semibold text-rose-800">Error al cargar datos del Dashboard</h3>
      <p class="text-xs text-rose-600 mt-1">{{ error }}</p>
      <button
        @click="fetchDashboardData"
        class="mt-4 px-4 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-medium hover:bg-rose-700 transition-colors"
      >
        Reintentar conexión
      </button>
    </div>

    <!-- Contenido Principal cuando está cargado -->
    <div v-else class="space-y-6">
      <!-- 1. Cuadrícula de 4 Tarjetas de Métricas Principales (Requerimiento 1) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Total Marcaciones -->
        <StatCard
          title="Total Marcaciones"
          :value="formatNumber(overview.stats.total_marcaciones)"
          subtitle="Registros históricos cargados"
          colorClass="bg-blue-50 text-blue-600"
        >
          <template #icon>
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
          </template>
        </StatCard>

        <!-- Trabajadores Identificados -->
        <StatCard
          title="Trabajadores"
          :value="overview.stats.trabajadores_identificados"
          :subtitle="`${overview.stats.trabajadores_con_nombre} con nombre y departamento registrado`"
          colorClass="bg-indigo-50 text-indigo-600"
        >
          <template #icon>
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
          </template>
        </StatCard>

        <!-- Marcaciones del Día -->
        <StatCard
          title="Marcaciones del Día"
          :value="overview.stats.marcaciones_hoy"
          :subtitle="`Fecha: ${overview.stats.fecha_referencia_hoy}`"
          colorClass="bg-emerald-50 text-emerald-600"
        >
          <template #icon>
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
          </template>
        </StatCard>

        <!-- Fechas Sospechosas -->
        <StatCard
          title="Fechas Sospechosas"
          :value="overview.stats.fechas_sospechosas"
          subtitle="Años futuros (2029, 2033, 2119)"
          colorClass="bg-amber-50 text-amber-600"
        >
          <template #icon>
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
          </template>
        </StatCard>
      </div>

      <!-- Alerta de Fechas Sospechosas Detectadas (Requerimiento 7) -->
      <div v-if="overview.stats.fechas_sospechosas > 0" class="bg-amber-50 border border-amber-200/90 rounded-2xl p-5 shadow-xs">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div class="flex items-start space-x-3.5">
            <div class="w-9 h-9 rounded-xl bg-amber-100 flex items-center justify-center shrink-0 text-amber-700">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
            </div>
            <div>
              <h4 class="text-sm font-bold text-amber-900">
                Se identificaron {{ overview.stats.fechas_sospechosas }} marcaciones con fechas futuras o anómalas
              </h4>
              <p class="text-xs text-amber-800 mt-1 leading-relaxed">
                El sistema conserva íntegramente los campos originales de cada registro sin alterarlos ni eliminarlos.
                Los años detectados comprenden:
                <span v-for="yr in overview.desglose_sospechosas" :key="yr.anio" class="inline-block bg-amber-200/60 font-mono font-semibold px-2 py-0.5 rounded text-[11px] text-amber-950 mx-1">
                  {{ yr.anio }} ({{ yr.cantidad }})
                </span>.
              </p>
            </div>
          </div>
          <router-link
            to="/marcaciones?fecha_sospechosa=true"
            class="inline-flex items-center justify-center px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold transition-colors shrink-0 shadow-xs"
          >
            Filtrar Registros Sospechosos
          </router-link>
        </div>
      </div>

      <!-- Sección de Distribución de Punches y Estado del Dispositivo -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Desglose de Códigos Punch (Requerimiento 6) -->
        <div class="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
          <div class="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 class="text-sm font-bold text-slate-900">Distribución por Código Punch Original</h3>
              <p class="text-xs text-slate-500 mt-0.5">Valores numéricos tal como fueron emitidos por el lector K20</p>
            </div>
            <span class="text-xs font-mono bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md">
              Total: {{ formatNumber(overview.stats.total_marcaciones) }}
            </span>
          </div>

          <!-- Nota metodológica obligatoria -->
          <div class="mt-4 p-3 bg-slate-50 border border-slate-200/60 rounded-xl text-[11px] text-slate-600 flex items-start space-x-2">
            <svg class="w-4 h-4 text-slate-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>
              <strong>Norma de Integridad:</strong> No se interpreta automáticamente ningún código como entrada o salida sin validación de reglas de la institución. Los datos numéricos se muestran sin alterar.
            </span>
          </div>

          <!-- Barras de Distribución -->
          <div class="mt-5 space-y-4">
            <div v-for="item in overview.distribucion_punches" :key="item.punch" class="space-y-1.5">
              <div class="flex justify-between items-center text-xs">
                <div class="flex items-center space-x-2">
                  <span class="w-6 h-6 rounded-md bg-slate-100 font-mono font-bold text-slate-700 flex items-center justify-center text-[11px]">
                    {{ item.punch }}
                  </span>
                  <span class="font-medium text-slate-800">{{ item.nombre }}</span>
                </div>
                <div class="text-right">
                  <span class="font-mono font-semibold text-slate-900">{{ formatNumber(item.cantidad) }}</span>
                  <span class="text-slate-400 text-[11px] ml-1.5">({{ item.porcentaje }}%)</span>
                </div>
              </div>
              <!-- Barra de progreso con gradiente sutil -->
              <div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div
                  class="h-2.5 rounded-full transition-all duration-500"
                  :class="getPunchBarColor(item.punch)"
                  :style="{ width: `${item.porcentaje}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tarjeta de Estado del Biométrico y Sincronizaciones -->
        <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 class="text-sm font-bold text-slate-900">Dispositivo ZKTeco</h3>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium"
                :class="estadoBadgeClase"
              >
                {{ estadoBadgeTexto }}
              </span>
            </div>

            <div class="mt-4 space-y-3 text-xs">
              <div class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Estado:</span>
                <span class="font-semibold" :class="estadoTextoClase">{{ estadoTexto }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Última conexión OK:</span>
                <span class="font-mono text-slate-700">{{ formatDateTime(overview.estado_dispositivo?.ultima_conexion_ok) }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Última sincronización:</span>
                <span class="font-mono text-slate-700">{{ formatDateTime(overview.estado_dispositivo?.ultimo_sync) }}</span>
              </div>
              <div v-if="overview.estado_dispositivo?.ultimo_error" class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Último error:</span>
                <span class="font-mono text-rose-700">{{ overview.estado_dispositivo.ultimo_error }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Última marcación válida:</span>
                <span class="font-mono text-slate-700">{{ formatDateTime(overview.ultima_marcacion_valida) }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Primer Registro:</span>
                <span class="font-mono text-slate-700">{{ formatDate(overview.stats.fecha_minima_registrada) }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-slate-50">
                <span class="text-slate-500">Último Registro:</span>
                <span class="font-mono text-slate-700">{{ formatDate(overview.stats.fecha_maxima_registrada) }}</span>
              </div>
            </div>
          </div>

          <div class="mt-6 pt-4 border-t border-slate-100">
            <div v-if="overview.ultima_sincronizacion" class="text-xs text-slate-500 mb-3 space-y-1">
              <p class="font-medium text-slate-700">Última Importación Ejecutada:</p>
              <p class="text-[11px] font-mono text-slate-500">
                {{ formatDate(overview.ultima_sincronizacion.finalizado_el) }} | Origen: {{ overview.ultima_sincronizacion.origen }}
              </p>
            </div>
            <router-link
              to="/dispositivo"
              class="w-full inline-flex items-center justify-center px-4 py-2 border border-slate-300 text-xs font-semibold rounded-lg text-slate-700 bg-white hover:bg-slate-50 transition-colors"
            >
              Ver Configuración del K20
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import StatCard from '../components/common/StatCard.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import { api } from '../services/api'

const overview = ref(null)
const loading = ref(true)
const error = ref(null)

const estadoTexto = computed(() => {
  const e = overview.value?.estado_dispositivo?.estado_conexion
  if (e === 'comprobada') return 'Conexión comprobada'
  if (e === 'sin_conexion') return 'Sin conexión'
  return 'Configurado'
})

const estadoTextoClase = computed(() => {
  const e = overview.value?.estado_dispositivo?.estado_conexion
  if (e === 'comprobada') return 'text-emerald-700'
  if (e === 'sin_conexion') return 'text-rose-700'
  return 'text-slate-700'
})

const estadoBadgeClase = computed(() => {
  const e = overview.value?.estado_dispositivo?.estado_conexion
  if (e === 'comprobada') return 'bg-emerald-100 text-emerald-800'
  if (e === 'sin_conexion') return 'bg-rose-100 text-rose-800'
  return 'bg-slate-100 text-slate-700'
})

const estadoBadgeTexto = computed(() => {
  const e = overview.value?.estado_dispositivo?.estado_conexion
  if (e === 'comprobada') return 'K20 Conectado'
  if (e === 'sin_conexion') return 'K20 Sin conexión'
  return 'K20 Configurado'
})

async function fetchDashboardData() {
  loading.value = true
  error.value = null
  try {
    const res = await api.getDashboardOverview()
    overview.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Error de conexión con el backend.'
  } finally {
    loading.value = false
  }
}

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return new Intl.NumberFormat('es-PE').format(num)
}

function formatDate(isoStr) {
  if (!isoStr) return 'N/A'
  const d = new Date(isoStr)
  return d.toLocaleString('es-PE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
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

function getPunchBarColor(punch) {
  switch (punch) {
    case 0: return 'bg-blue-600'
    case 1: return 'bg-emerald-500'
    case 4: return 'bg-purple-500'
    case 5: return 'bg-amber-500'
    default: return 'bg-slate-500'
  }
}

onMounted(() => {
  fetchDashboardData()
  window.addEventListener('records-imported', fetchDashboardData)
})

onUnmounted(() => {
  window.removeEventListener('records-imported', fetchDashboardData)
})
</script>

