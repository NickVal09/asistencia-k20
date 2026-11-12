<template>
  <div class="space-y-6">
    <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
      <h2 class="text-xl font-bold text-slate-900 tracking-tight">Centro de Exportación de Datos</h2>
      <p class="text-xs text-slate-500 mt-1">
        Generación de reportes directos en formatos Excel (<code class="text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded font-mono">.xlsx</code>)
        y texto delimitado por comas (<code class="text-blue-700 bg-blue-50 px-1 py-0.5 rounded font-mono">.csv UTF-8 BOM</code>)
        sin consultar nuevamente el biométrico físico.
      </p>
    </div>

    <!-- Tarjetas de Exportación Rápida -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <!-- Opción 1: Todo el Historial -->
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
        <div>
          <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z"></path>
            </svg>
          </div>
          <h3 class="text-sm font-bold text-slate-900">Historial Completo</h3>
          <p class="text-xs text-slate-500 mt-1">
            Exporta las 48 601 marcaciones históricas conservando todos los identificadores y códigos originales.
          </p>
        </div>
        <div class="mt-5 pt-4 border-t border-slate-100 flex items-center space-x-2">
          <button
            @click="descargar('csv')"
            class="flex-1 text-center py-2 px-3 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            Descargar CSV
          </button>
          <button
            @click="descargar('excel')"
            class="flex-1 text-center py-2 px-3 bg-emerald-600 hover:bg-emerald-700 rounded-lg text-xs font-semibold text-white transition-colors shadow-xs cursor-pointer"
          >
            Descargar Excel
          </button>
        </div>
      </div>

      <!-- Opción 2: Solo Fechas Sospechosas -->
      <div class="bg-white p-5 rounded-2xl border border-amber-200/90 shadow-xs flex flex-col justify-between">
        <div>
          <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
          </div>
          <div class="flex items-center space-x-2">
            <h3 class="text-sm font-bold text-amber-950">Fechas Sospechosas</h3>
            <span class="bg-amber-100 text-amber-900 font-mono text-[10px] px-1.5 py-0.5 rounded-full font-bold">37</span>
          </div>
          <p class="text-xs text-slate-500 mt-1">
            Reporte de auditoría con las 37 marcaciones registradas en años futuros (2029, 2033 y 2119).
          </p>
        </div>
        <div class="mt-5 pt-4 border-t border-slate-100 flex items-center space-x-2">
          <button
            @click="descargar('csv', { fecha_sospechosa: true })"
            class="flex-1 text-center py-2 px-3 border border-amber-300 rounded-lg text-xs font-semibold text-amber-900 hover:bg-amber-50 transition-colors cursor-pointer"
          >
            Descargar CSV
          </button>
          <button
            @click="descargar('excel', { fecha_sospechosa: true })"
            class="flex-1 text-center py-2 px-3 bg-amber-600 hover:bg-amber-700 rounded-lg text-xs font-semibold text-white transition-colors shadow-xs cursor-pointer"
          >
            Descargar Excel
          </button>
        </div>
      </div>

      <!-- Opción 3: Solo Fechas Legítimas -->
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
        <div>
          <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <h3 class="text-sm font-bold text-slate-900">Historial Legítimo</h3>
          <p class="text-xs text-slate-500 mt-1">
            Excluye las 37 fechas sospechosas, entregando un reporte apto para nóminas y cómputo formal.
          </p>
        </div>
        <div class="mt-5 pt-4 border-t border-slate-100 flex items-center space-x-2">
          <button
            @click="descargar('csv', { fecha_sospechosa: false })"
            class="flex-1 text-center py-2 px-3 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            Descargar CSV
          </button>
          <button
            @click="descargar('excel', { fecha_sospechosa: false })"
            class="flex-1 text-center py-2 px-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-xs font-semibold text-white transition-colors shadow-xs cursor-pointer"
          >
            Descargar Excel
          </button>
        </div>
      </div>
    </div>

    <!-- Generador de Exportación Personalizada -->
    <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
      <h3 class="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
        Exportador Personalizado con Criterios Múltiples
      </h3>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Desde Fecha:</label>
          <input
            v-model="customForm.fecha_inicio"
            type="date"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Hasta Fecha:</label>
          <input
            v-model="customForm.fecha_fin"
            type="date"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">ID Trabajador:</label>
          <input
            v-model="customForm.user_id"
            type="text"
            placeholder="Opcional"
            class="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Código Punch:</label>
          <select
            v-model="customForm.punch"
            class="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden bg-white"
          >
            <option :value="null">Todos los Punches</option>
            <option :value="0">Punch 0</option>
            <option :value="1">Punch 1</option>
            <option :value="4">Punch 4</option>
            <option :value="5">Punch 5</option>
          </select>
        </div>
      </div>

      <div class="pt-3 flex items-center justify-end space-x-3">
        <button
          @click="descargarCustom('csv')"
          class="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
        >
          Exportar Selección a CSV
        </button>
        <button
          @click="descargarCustom('excel')"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs font-semibold text-white transition-colors shadow-xs cursor-pointer"
        >
          Exportar Selección a Excel (.xlsx)
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { api } from '../services/api'

const customForm = reactive({
  fecha_inicio: '',
  fecha_fin: '',
  user_id: '',
  punch: null,
})

async function descargar(format, extraParams = {}) {
  try {
    await api.descargarExportacion(format === 'excel' ? 'excel' : 'csv', extraParams)
  } catch (err) {
    alert(err.response?.data?.detail || err.message || 'No se pudo descargar.')
  }
}

async function descargarCustom(format) {
  const p = {}
  if (customForm.fecha_inicio) p.fecha_inicio = `${customForm.fecha_inicio}T00:00:00`
  if (customForm.fecha_fin) p.fecha_fin = `${customForm.fecha_fin}T23:59:59`
  if (customForm.user_id && customForm.user_id.trim()) p.user_id = customForm.user_id.trim()
  if (customForm.punch !== null && customForm.punch !== '') p.punch = customForm.punch
  await descargar(format, p)
}
</script>

