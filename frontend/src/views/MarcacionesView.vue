<template>
  <div class="space-y-5">
    <!-- Header y Acciones de Exportación -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
      <div>
        <h2 class="text-xl font-bold text-slate-900 tracking-tight">Registro General de Marcaciones</h2>
        <p class="text-xs text-slate-500 mt-0.5">
          Consultas paginadas directamente desde la base de datos MySQL con soporte de exportación.
        </p>
      </div>

      <!-- Botones de Exportación Respetando Filtros Activos (Requerimiento 4) -->
      <div class="flex items-center space-x-2.5 shrink-0">
        <button
          @click="exportar('csv')"
          class="inline-flex items-center px-3.5 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-400 transition-colors shadow-2xs cursor-pointer"
          title="Exporta el conjunto actual con codificación UTF-8 BOM"
        >
          <svg class="w-4 h-4 mr-1.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Exportar CSV
        </button>

        <button
          @click="exportar('excel')"
          class="inline-flex items-center px-4 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-xs cursor-pointer"
          title="Exporta libro Excel formateado con estilos y bordes"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Exportar Excel (.xlsx)
        </button>
      </div>
    </div>

    <!-- Barra de Filtros Avanzados (Requerimiento 3) -->
    <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3.5">
        <!-- Fecha Inicial -->
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Fecha Inicial:</label>
          <input
            v-model="filters.fecha_inicio"
            type="date"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
            @change="applyFilters"
          />
        </div>

        <!-- Fecha Final -->
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Fecha Final:</label>
          <input
            v-model="filters.fecha_fin"
            type="date"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
            @change="applyFilters"
          />
        </div>

        <!-- ID Trabajador (user_id texto conservando ceros) -->
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">ID o Nombre:</label>
          <div class="relative">
            <input
              v-model="filters.user_id"
              type="text"
              placeholder="Ej: 104, Pérez..."
              class="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
              @keyup.enter="applyFilters"
            />
            <button
              v-if="filters.user_id"
              @click="filters.user_id = ''; applyFilters()"
              class="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600 text-xs"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Tipo / Código Punch -->
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Tipo / Código Punch:</label>
          <select
            v-model="filters.punch"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden bg-white"
            @change="applyFilters"
          >
            <option :value="null">Todos los Punches</option>
            <option :value="0">Punch 0 (Tipo 0)</option>
            <option :value="1">Punch 1 (Tipo 1)</option>
            <option :value="4">Punch 4 (Tipo 4)</option>
            <option :value="5">Punch 5 (Tipo 5)</option>
          </select>
        </div>

        <!-- Filtro Fechas Sospechosas (Requerimiento 7) -->
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Filtro de Anomalías:</label>
          <select
            v-model="filters.fecha_sospechosa"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden bg-white"
            @change="applyFilters"
          >
            <option :value="null">Todas las Marcaciones</option>
            <option :value="false">Solo Fechas Legítimas</option>
            <option :value="true">⚠️ Solo Fechas Sospechosas (37)</option>
          </select>
        </div>
      </div>

      <!-- Presets Rápidos y Limpiar Filtros -->
      <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs">
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-slate-400 font-medium mr-1 text-[11px]">Accesos rápidos:</span>
          <button
            @click="setPreset('today')"
            class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            Hoy
          </button>
          <button
            @click="setPreset('last7')"
            class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            Últimos 7 días
          </button>
          <button
            @click="setPreset('month')"
            class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            Mes Actual
          </button>
          <button
            @click="setPreset('suspicious')"
            class="px-2.5 py-1 rounded bg-amber-100 hover:bg-amber-200 text-amber-900 font-medium transition-colors"
          >
            Fechas Sospechosas
          </button>
          <button
            @click="resetFilters"
            class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors"
          >
            Limpiar Filtros
          </button>
        </div>

        <!-- Indicador de total encontrado -->
        <div class="text-slate-600 text-xs">
          Coincidencias: <strong class="font-mono text-slate-900">{{ formatNumber(totalRecords) }}</strong> registros
        </div>
      </div>
    </div>

    <!-- Tabla Profesional con Paginación Backend (Requerimiento 2, 6, 8, 9) -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <!-- Loading State -->
      <div v-if="loading" class="p-16">
        <LoadingSpinner text="Consultando marcaciones desde MySQL..." />
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-16 text-center">
        <svg class="w-10 h-10 text-rose-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <h3 class="text-sm font-semibold text-slate-700">No se pudieron cargar las marcaciones</h3>
        <p class="text-xs text-slate-500 mt-1">{{ error }}</p>
        <button
          @click="fetchMarcaciones"
          class="mt-4 px-4 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors"
        >
          Reintentar
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="items.length === 0" class="p-16 text-center">
        <svg class="w-12 h-12 text-slate-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        <h3 class="text-sm font-semibold text-slate-700">No se encontraron marcaciones</h3>
        <p class="text-xs text-slate-500 mt-1">Prueba modificando o eliminando los filtros seleccionados.</p>
        <button
          @click="resetFilters"
          class="mt-3 px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg text-xs font-semibold hover:bg-blue-100 transition-colors"
        >
          Restablecer filtros
        </button>
      </div>

      <!-- Tabla de Datos -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <th class="py-3.5 px-4 font-mono cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('id')" title="Ordenar por ID de registro">
                <div class="flex items-center space-x-1"><span># ID</span><span>{{ sortIndicator('id') }}</span></div>
              </th>
              <th class="py-3.5 px-4 font-mono cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('uid')" title="Ordenar por UID original">
                <div class="flex items-center space-x-1"><span>UID Orig.</span><span>{{ sortIndicator('uid') }}</span></div>
              </th>
              <th class="py-3.5 px-4 font-mono cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('user_id')" title="Ordenar por ID de trabajador">
                <div class="flex items-center space-x-1"><span>ID Trabajador</span><span>{{ sortIndicator('user_id') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('nombre')" title="Ordenar por nombre">
                <div class="flex items-center space-x-1"><span>Nombre del Trabajador</span><span>{{ sortIndicator('nombre') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('departamento')" title="Ordenar por departamento">
                <div class="flex items-center space-x-1"><span>Departamento</span><span>{{ sortIndicator('departamento') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('timestamp')" title="Ordenar por fecha y hora">
                <div class="flex items-center space-x-1"><span>Fecha y Hora</span><span>{{ sortIndicator('timestamp') }}</span></div>
              </th>
              <th class="py-3.5 px-4 text-center cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('status')" title="Ordenar por status">
                <div class="flex items-center justify-center space-x-1"><span>Status</span><span>{{ sortIndicator('status') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('punch')" title="Ordenar por punch original">
                <div class="flex items-center space-x-1"><span>Punch Original</span><span>{{ sortIndicator('punch') }}</span></div>
              </th>
              <th class="py-3.5 px-4 text-center cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('fecha_sospechosa')" title="Ordenar por anomalía">
                <div class="flex items-center justify-center space-x-1"><span>Anomalía</span><span>{{ sortIndicator('fecha_sospechosa') }}</span></div>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="row in items"
              :key="row.id"
              class="hover:bg-slate-50/70 transition-colors"
              :class="{ 'bg-amber-50/40': row.fecha_sospechosa }"
            >
              <!-- ID Registro Interno -->
              <td class="py-3 px-4 font-mono text-slate-400 text-[11px]">{{ row.id }}</td>

              <!-- UID Original de la máquina K20 -->
              <td class="py-3 px-4 font-mono text-slate-600">
                {{ row.uid !== null ? row.uid : '-' }}
              </td>

              <!-- ID Trabajador (conservando formato texto y ceros a la izquierda) -->
              <td class="py-3 px-4">
                <span class="font-mono font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200/50">
                  {{ row.user_id }}
                </span>
              </td>

              <!-- Nombre y departamento obtenidos de la relación con Trabajador -->
              <td class="py-3 px-4">
                <span
                  :class="row.nombre_trabajador === 'Sin nombre registrado'
                    ? 'text-slate-400 italic'
                    : 'text-slate-800 font-medium'"
                >
                  {{ row.nombre_trabajador }}
                </span>
              </td>
              <td class="py-3 px-4 text-slate-600">
                {{ row.departamento_trabajador || '-' }}
              </td>

              <!-- Timestamp -->
              <td class="py-3 px-4 font-mono text-slate-800 font-medium">
                {{ formatDateTime(row.timestamp) }}
              </td>

              <!-- Status Original -->
              <td class="py-3 px-4 text-center">
                <span class="font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
                  {{ row.status }}
                </span>
              </td>

              <!-- Punch Original con Badge -->
              <td class="py-3 px-4">
                <span :class="['inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium font-mono', getPunchBadgeClass(row.punch)]">
                  Punch {{ row.punch }}
                </span>
              </td>

              <!-- Indicador de Fecha Sospechosa (Requerimiento 7) -->
              <td class="py-3 px-4 text-center">
                <span
                  v-if="row.fecha_sospechosa"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300"
                  :title="row.motivo_sospecha || 'Fecha en el futuro detectada'"
                >
                  ⚠️ Futura
                </span>
                <span v-else class="text-slate-300 text-[11px]">
                  ✓ Normal
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Barra de Paginación Backend (Requerimiento 2) -->
      <div class="px-5 py-3.5 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs text-slate-600 bg-slate-50/50">
        <div class="flex items-center space-x-2">
          <span>Mostrando</span>
          <select
            v-model="perPage"
            @change="changePerPage"
            class="px-2 py-1 border border-slate-300 rounded bg-white text-xs font-medium focus:ring-1 focus:ring-blue-500 focus:outline-hidden"
          >
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
          </select>
          <span>por página (Pág. <strong class="font-mono">{{ currentPage }}</strong> de <strong class="font-mono">{{ totalPages }}</strong>)</span>
        </div>

        <div class="flex items-center space-x-1.5 self-center sm:self-auto">
          <button
            @click="goToPage(1)"
            :disabled="currentPage <= 1 || loading"
            class="px-2.5 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Primera página"
          >
            «
          </button>
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage <= 1 || loading"
            class="px-3 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Anterior
          </button>
          <span class="px-2 font-mono text-slate-700">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage >= totalPages || loading"
            class="px-3 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Siguiente
          </button>
          <button
            @click="goToPage(totalPages)"
            :disabled="currentPage >= totalPages || loading"
            class="px-2.5 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Última página"
          >
            »
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import { api } from '../services/api'

const route = useRoute()
const router = useRouter()

const items = ref([])
const totalRecords = ref(0)
const totalPages = ref(1)
const currentPage = ref(1)
const perPage = ref(50)
const loading = ref(true)
const error = ref('')

const filters = reactive({
  fecha_inicio: '',
  fecha_fin: '',
  user_id: '',
  punch: null,
  status: null,
  fecha_sospechosa: null,
  order_by: 'timestamp',
  order_dir: 'desc',
})

async function exportar(formato) {
  try {
    await api.descargarExportacion(formato === 'excel' ? 'excel' : 'csv', buildQueryParams())
  } catch (err) {
    alert(err.response?.data?.detail || err.message || 'No se pudo descargar.')
  }
}

function buildQueryParams() {
  const p = {}
  if (filters.fecha_inicio) p.fecha_inicio = `${filters.fecha_inicio}T00:00:00`
  if (filters.fecha_fin) p.fecha_fin = `${filters.fecha_fin}T23:59:59`
  if (filters.user_id && filters.user_id.trim()) p.user_id = filters.user_id.trim()
  if (filters.punch !== null && filters.punch !== '') p.punch = filters.punch
  if (filters.status !== null && filters.status !== '') p.status = filters.status
  if (filters.fecha_sospechosa !== null && filters.fecha_sospechosa !== '') {
    p.fecha_sospechosa = filters.fecha_sospechosa
  }
  p.order_by = filters.order_by
  p.order_dir = filters.order_dir
  return p
}

// Cancela peticiones anteriores: si el usuario hace clic rapido en varias
// columnas, solo se aplica la respuesta de la ultima, evitando resultados
// fuera de orden.
let peticionActual = null

async function fetchMarcaciones() {
  if (peticionActual) peticionActual.abort()
  const controlador = new AbortController()
  peticionActual = controlador

  loading.value = true
  error.value = ''
  try {
    const params = {
      ...buildQueryParams(),
      page: currentPage.value,
      per_page: perPage.value,
    }
    const res = await api.getMarcaciones(params, { signal: controlador.signal })
    if (peticionActual !== controlador) return
    items.value = res.data.items
    totalRecords.value = res.data.total
    totalPages.value = res.data.total_pages
  } catch (err) {
    // Peticion cancelada por una nueva: no es un error.
    if (controlador.signal.aborted) return
    console.error('Error al consultar marcaciones:', err)
    items.value = []
    totalRecords.value = 0
    totalPages.value = 1
    error.value = err.response?.data?.detail
      || 'No hay conexión con el backend (verifica que esté iniciado en el puerto 8000).'
  } finally {
    if (peticionActual === controlador) loading.value = false
  }
}

function applyFilters() {
  currentPage.value = 1
  fetchMarcaciones()
}

function resetFilters() {
  filters.fecha_inicio = ''
  filters.fecha_fin = ''
  filters.user_id = ''
  filters.punch = null
  filters.status = null
  filters.fecha_sospechosa = null
  filters.order_by = 'timestamp'
  filters.order_dir = 'desc'
  currentPage.value = 1
  fetchMarcaciones()
}

function setPreset(preset) {
  const now = new Date()
  const todayStr = now.toISOString().split('T')[0]

  if (preset === 'today') {
    filters.fecha_inicio = todayStr
    filters.fecha_fin = todayStr
    filters.fecha_sospechosa = null
  } else if (preset === 'last7') {
    const past = new Date()
    past.setDate(past.getDate() - 7)
    filters.fecha_inicio = past.toISOString().split('T')[0]
    filters.fecha_fin = todayStr
    filters.fecha_sospechosa = null
  } else if (preset === 'month') {
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
    filters.fecha_inicio = firstDay.toISOString().split('T')[0]
    filters.fecha_fin = todayStr
    filters.fecha_sospechosa = null
  } else if (preset === 'suspicious') {
    filters.fecha_inicio = ''
    filters.fecha_fin = ''
    filters.fecha_sospechosa = true
  }
  applyFilters()
}

function sortIndicator(col) {
  if (filters.order_by !== col) return ''
  return filters.order_dir === 'asc' ? '▲' : '▼'
}

function toggleSort(col) {
  if (filters.order_by === col) {
    filters.order_dir = filters.order_dir === 'asc' ? 'desc' : 'asc'
  } else {
    filters.order_by = col
    // Fechas y anomalías: primero lo más reciente; el resto: ascendente (1 → N, A → Z)
    filters.order_dir = ['timestamp', 'fecha_sospechosa'].includes(col) ? 'desc' : 'asc'
  }
  currentPage.value = 1
  fetchMarcaciones()
}

function goToPage(p) {
  if (p >= 1 && p <= totalPages.value) {
    currentPage.value = p
    fetchMarcaciones()
  }
}

function changePerPage() {
  currentPage.value = 1
  fetchMarcaciones()
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

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return new Intl.NumberFormat('es-PE').format(num)
}

function getPunchBadgeClass(punch) {
  switch (punch) {
    case 0: return 'bg-blue-100 text-blue-800 border border-blue-200'
    case 1: return 'bg-emerald-100 text-emerald-800 border border-emerald-200'
    case 4: return 'bg-purple-100 text-purple-800 border border-purple-200'
    case 5: return 'bg-amber-100 text-amber-800 border border-amber-200'
    default: return 'bg-slate-100 text-slate-800'
  }
}

onMounted(() => {
  // Capturar posibles filtros pasados por query params (ej: desde Dashboard)
  if (route.query.fecha_sospechosa !== undefined) {
    filters.fecha_sospechosa = route.query.fecha_sospechosa === 'true'
  }
  if (route.query.user_id) {
    filters.user_id = route.query.user_id
  }
  fetchMarcaciones()
})
</script>

