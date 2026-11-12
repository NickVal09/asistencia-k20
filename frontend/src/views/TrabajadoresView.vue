<template>
  <div class="space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
      <div>
        <h2 class="text-xl font-bold text-slate-900 tracking-tight">Padrón de Trabajadores</h2>
        <p class="text-xs text-slate-500 mt-0.5">
          Padrón de colaboradores importado desde <code class="text-blue-700 bg-blue-50 px-1 py-0.5 rounded font-mono">Colaboradores Export.xls</code>, relacionado con las marcaciones por <code class="text-blue-700 bg-blue-50 px-1 py-0.5 rounded font-mono">AC No. = user_id</code>.
        </p>
      </div>

      <!-- Búsqueda rápida -->
      <div class="w-full sm:w-72">
        <div class="relative">
          <input
            v-model="searchTerm"
            @keyup.enter="searchWorkers"
            type="text"
            placeholder="Buscar por nombre o ID de trabajador..."
            class="w-full text-xs font-mono pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
          />
          <svg class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>
      </div>
    </div>

    <!-- Tabla de Trabajadores -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div v-if="loading" class="p-16">
        <LoadingSpinner text="Cargando padrón de trabajadores..." />
      </div>

      <div v-else-if="error" class="p-16 text-center">
        <svg class="w-10 h-10 text-rose-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <h3 class="text-sm font-semibold text-slate-700">No se pudo cargar el padrón</h3>
        <p class="text-xs text-slate-500 mt-1">{{ error }}</p>
        <button
          @click="fetchWorkers"
          class="mt-4 px-4 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors"
        >
          Reintentar
        </button>
      </div>

      <div v-else-if="workers.length === 0" class="p-16 text-center text-slate-500 text-xs">
        No se encontraron trabajadores con el término de búsqueda indicado.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <th class="py-3.5 px-4 font-mono cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('user_id')" title="Ordenar por ID de trabajador">
                <div class="flex items-center space-x-1"><span>ID Trabajador (user_id)</span><span>{{ sortIndicator('user_id') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('nombre')" title="Ordenar por nombre">
                <div class="flex items-center space-x-1"><span>Nombre del Trabajador</span><span>{{ sortIndicator('nombre') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('departamento')" title="Ordenar por departamento">
                <div class="flex items-center space-x-1"><span>Departamento</span><span>{{ sortIndicator('departamento') }}</span></div>
              </th>
              <th class="py-3.5 px-4 text-right cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('total_marcaciones')" title="Ordenar por total de marcaciones">
                <div class="flex items-center justify-end space-x-1"><span>Total Marcaciones</span><span>{{ sortIndicator('total_marcaciones') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('primer_registro')" title="Ordenar por primer registro">
                <div class="flex items-center space-x-1"><span>Primer Registro</span><span>{{ sortIndicator('primer_registro') }}</span></div>
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('ultimo_registro')" title="Ordenar por último registro">
                <div class="flex items-center space-x-1"><span>Último Registro Legítimo</span><span>{{ sortIndicator('ultimo_registro') }}</span></div>
              </th>
              <th class="py-3.5 px-4 text-center cursor-pointer hover:bg-slate-100 transition-colors" @click="toggleSort('activo')" title="Ordenar por estado">
                <div class="flex items-center justify-center space-x-1"><span>Estado</span><span>{{ sortIndicator('activo') }}</span></div>
              </th>
              <th class="py-3.5 px-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="w in workers" :key="w.id" class="hover:bg-slate-50/70 transition-colors">
              <td class="py-3 px-4">
                <span class="font-mono font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200/60">
                  {{ w.user_id }}
                </span>
              </td>
              <td class="py-3 px-4">
                <span
                  v-if="w.nombre"
                  class="text-slate-800 font-medium"
                >{{ w.nombre }}</span>
                <span v-else class="text-slate-400 italic">Sin nombre registrado</span>
              </td>
              <td class="py-3 px-4 text-slate-600">
                {{ w.departamento || '-' }}
              </td>
              <td class="py-3 px-4 text-right font-mono font-semibold text-slate-900">
                {{ formatNumber(w.total_marcaciones) }}
              </td>
              <td class="py-3 px-4 font-mono text-slate-600">
                {{ formatDateTime(w.primer_registro) }}
              </td>
              <td class="py-3 px-4 font-mono text-slate-600">
                {{ formatDateTime(w.ultimo_registro) }}
              </td>
              <td class="py-3 px-4 text-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                  Activo
                </span>
              </td>
              <td class="py-3 px-4 text-right">
                <router-link
                  :to="`/marcaciones?user_id=${w.user_id}`"
                  class="inline-flex items-center px-2.5 py-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                >
                  Ver Historial →
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginación -->
      <div class="px-5 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 bg-slate-50/50">
        <div>Total: <strong class="font-mono text-slate-800">{{ totalWorkers }}</strong> trabajadores registrados</div>
        <div class="flex items-center space-x-1">
          <button
            @click="changePage(currentPage - 1)"
            :disabled="currentPage <= 1 || loading"
            class="px-2.5 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            Anterior
          </button>
          <span class="px-2 font-mono text-slate-700">{{ currentPage }} / {{ totalPages }}</span>
          <button
            @click="changePage(currentPage + 1)"
            :disabled="currentPage >= totalPages || loading"
            class="px-2.5 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import { api } from '../services/api'

const workers = ref([])
const totalWorkers = ref(0)
const totalPages = ref(1)
const currentPage = ref(1)
const searchTerm = ref('')
const loading = ref(true)
const error = ref('')
const sortBy = ref('total_marcaciones')
const sortDir = ref('desc')

// Igual que en Marcaciones: solo se aplica la respuesta de la ultima consulta.
let peticionActual = null

async function fetchWorkers() {
  if (peticionActual) peticionActual.abort()
  const controlador = new AbortController()
  peticionActual = controlador

  loading.value = true
  error.value = ''
  try {
    const res = await api.getTrabajadores({
      search: searchTerm.value || null,
      order_by: sortBy.value,
      order_dir: sortDir.value,
      page: currentPage.value,
      per_page: 50,
    }, { signal: controlador.signal })
    if (peticionActual !== controlador) return
    workers.value = res.data.items
    totalWorkers.value = res.data.total
    totalPages.value = res.data.total_pages
  } catch (err) {
    if (controlador.signal.aborted) return
    console.error('Error al obtener trabajadores:', err)
    workers.value = []
    totalWorkers.value = 0
    totalPages.value = 1
    error.value = err.response?.data?.detail
      || 'No hay conexión con el backend (verifica que esté iniciado en el puerto 8000).'
  } finally {
    if (peticionActual === controlador) loading.value = false
  }
}

function searchWorkers() {
  currentPage.value = 1
  fetchWorkers()
}

function sortIndicator(col) {
  if (sortBy.value !== col) return ''
  return sortDir.value === 'asc' ? '▲' : '▼'
}

function toggleSort(col) {
  if (sortBy.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = col
    // Los campos de texto empiezan de A a Z; los numéricos/fechas de mayor a menor
    sortDir.value = ['nombre', 'departamento', 'user_id'].includes(col) ? 'asc' : 'desc'
  }
  currentPage.value = 1
  fetchWorkers()
}

function changePage(p) {
  if (p >= 1 && p <= totalPages.value) {
    currentPage.value = p
    fetchWorkers()
  }
}

function formatNumber(num) {
  return new Intl.NumberFormat('es-PE').format(num || 0)
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
  })
}

onMounted(() => {
  fetchWorkers()
})
</script>

