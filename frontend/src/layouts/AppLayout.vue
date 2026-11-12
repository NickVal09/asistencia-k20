<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden">
    <!-- Barra Lateral de Navegación -->
    <Sidebar />

    <!-- Contenedor Principal -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Barra Superior -->
      <Navbar
    @open-import-modal="isImportModalOpen = true"
    @open-sync-modal="isSyncModalOpen = true"
    @logout="logout"
  />

      <!-- Área de Contenido con Scroll -->
      <main class="flex-1 overflow-y-auto p-6 md:p-8">
        <router-view />
      </main>
    </div>

    <!-- Modal de Importación / Sincronización CSV -->
    <Modal :isOpen="isImportModalOpen" @close="isImportModalOpen = false">
      <template #title>
        Sincronizar Archivo CSV de Marcaciones
      </template>

      <div class="space-y-4">
        <p class="text-sm text-slate-600">
          Esta operación leerá el archivo de marcaciones extraído del reloj K20 y actualizará la base de datos MySQL localmente.
        </p>

        <div class="bg-blue-50 border border-blue-200 rounded-xl p-3.5 space-y-2 text-xs text-blue-900">
          <div class="flex items-center space-x-2 font-semibold text-blue-950">
            <svg class="w-4 h-4 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Propiedades del proceso:</span>
          </div>
          <ul class="list-disc list-inside space-y-1 text-blue-800">
            <li><strong>Idempotente:</strong> Omite duplicados automáticamente mediante hash SHA-256.</li>
            <li><strong>Preservación:</strong> Conserva UIDs, ceros iniciales y códigos originales.</li>
            <li><strong>Detección de anomalías:</strong> Identifica fechas sospechosas (años futuros).</li>
          </ul>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Ruta del archivo CSV (Opcional):</label>
          <input
            v-model="customCsvPath"
            type="text"
            placeholder="Por defecto: datos/registros_k20.csv"
            class="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
          />
          <p class="text-[11px] text-slate-400 mt-1">Dejar vacío para usar el archivo extraído por defecto.</p>
        </div>

        <div v-if="importLoading" class="pt-2">
          <div class="flex items-center space-x-3 text-sm text-blue-600 bg-blue-50/50 p-3 rounded-lg border border-blue-100">
            <svg class="animate-spin w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Importando marcaciones... Esto puede tomar varios segundos.</span>
          </div>
        </div>

        <!-- Importación del padrón de colaboradores (.xls) -->
        <div class="pt-3 border-t border-slate-200 space-y-3">
          <div>
            <h4 class="text-xs font-bold text-slate-800">Padrón de Colaboradores (.xls)</h4>
            <p class="text-[11px] text-slate-500 mt-0.5">
              Importa nombres y departamentos desde el archivo exportado de ZLM60_TFT y los relaciona con las marcaciones mediante <code class="font-mono">AC No. = user_id</code>.
            </p>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Ruta del archivo .xls (Opcional):</label>
            <input
              v-model="customXlsPath"
              type="text"
              placeholder="Por defecto: datos/Colaboradores Export.xls"
              class="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
            />
          </div>

          <div class="flex items-center justify-between gap-3">
            <p class="text-[11px] text-slate-400">
              Operación idempotente: no altera las marcaciones ni crea duplicados.
            </p>
            <button
              @click="executeColaboradoresImport"
              :disabled="colabLoading"
              class="px-3 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-xs transition-colors cursor-pointer disabled:opacity-50 shrink-0"
            >
              <span v-if="!colabLoading">Importar Colaboradores</span>
              <span v-else>Procesando...</span>
            </button>
          </div>
        </div>
      </div>

      <template #footer>
        <button
          @click="isImportModalOpen = false"
          :disabled="importLoading"
          class="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
        >
          Cancelar
        </button>
        <button
          @click="executeImport"
          :disabled="importLoading"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition-colors flex items-center space-x-2 cursor-pointer disabled:opacity-50"
        >
          <span v-if="!importLoading">Ejecutar Importación</span>
          <span v-else>Procesando...</span>
        </button>
      </template>
    </Modal>

    <!-- Modal de Sincronizacion con K20 (Fase 2) -->
    <Modal :isOpen="isSyncModalOpen" @close="cerrarSyncModal">
      <template #title>
        Sincronizar con K20 (Lectura Directa)
      </template>

      <div class="space-y-4">
        <p class="text-sm text-slate-600">
          Descarga todas las marcaciones del reloj ZKTeco K20 y las inserta en MySQL conservando los registros existentes. Operación de solo lectura sobre el dispositivo.
        </p>

        <div class="bg-amber-50 border border-amber-200 rounded-xl p-3.5 text-xs text-amber-900 space-y-1">
          <p class="font-semibold">Aviso importante:</p>
          <ul class="list-disc list-inside space-y-0.5">
            <li>La descarga completa tarda aproximadamente 50 segundos.</li>
            <li>La tarea continúa aunque cierres el navegador.</li>
            <li>No se borra ni modifica nada en el reloj ni en MySQL.</li>
          </ul>
        </div>

        <div v-if="syncEstado" class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs space-y-1.5">
          <div class="flex justify-between">
            <span class="text-slate-500">Estado de conexión:</span>
            <span class="font-semibold" :class="syncEstado.estado_conexion === 'comprobada' ? 'text-emerald-700' : (syncEstado.estado_conexion === 'sin_conexion' ? 'text-rose-700' : 'text-slate-700')">
              {{ syncEstado.estado_conexion }}
            </span>
          </div>
          <div v-if="syncEstado.dispositivo?.ultima_conexion_ok" class="flex justify-between">
            <span class="text-slate-500">Última conexión OK:</span>
            <span class="font-mono">{{ formatDateTime(syncEstado.dispositivo.ultima_conexion_ok) }}</span>
          </div>
          <div v-if="syncEstado.dispositivo?.ultimo_error" class="text-rose-600">
            Último error: {{ syncEstado.dispositivo.ultimo_error }}
          </div>
        </div>

        <div v-if="syncEnCurso || syncResultado" class="pt-2">
          <div v-if="syncEnCurso" class="flex items-center space-x-3 text-sm text-blue-600 bg-blue-50/50 p-3 rounded-lg border border-blue-100">
            <svg class="animate-spin w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Sincronizando con el K20... {{ syncFase }}</span>
          </div>

          <div v-if="syncResultado" class="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 text-xs space-y-1.5">
            <p class="font-semibold text-emerald-800">Sincronización finalizada: {{ syncResultado.estado }}</p>
            <div class="grid grid-cols-2 gap-1 text-emerald-900">
              <span>Leídos: <strong>{{ syncResultado.total_leidos }}</strong></span>
              <span>Nuevos: <strong>{{ syncResultado.nuevos_registros }}</strong></span>
              <span>Duplicados: <strong>{{ syncResultado.duplicados_omitidos }}</strong></span>
              <span>Errores: <strong>{{ syncResultado.errores }}</strong></span>
              <span v-if="syncResultado.duracion_segundos">Duración: <strong>{{ syncResultado.duracion_segundos }}s</strong></span>
            </div>
            <p v-if="syncResultado.mensaje_detalle" class="text-[11px] text-emerald-800 pt-1">
              {{ syncResultado.mensaje_detalle }}
            </p>
          </div>
        </div>
      </div>

      <template #footer>
        <button
          @click="cerrarSyncModal"
          :disabled="syncEnCurso"
          class="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
        >
          Cerrar
        </button>
        <button
          @click="probarConexion"
          :disabled="syncEnCurso || probando"
          class="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
        >
          {{ probando ? 'Probando...' : 'Probar conexión' }}
        </button>
        <button
          @click="iniciarSync"
          :disabled="syncEnCurso"
          class="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-xs transition-colors flex items-center space-x-2 cursor-pointer disabled:opacity-50"
        >
          <span v-if="!syncEnCurso">Sincronizar con K20</span>
          <span v-else>Sincronizando...</span>
        </button>
      </template>
    </Modal>

    <!-- Sistema Global de Toast -->
    <Toast
      :show="toast.show"
      :type="toast.type"
      :title="toast.title"
      :message="toast.message"
      @close="toast.show = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '../components/layout/Sidebar.vue'
import Navbar from '../components/layout/Navbar.vue'
import Modal from '../components/common/Modal.vue'
import Toast from '../components/common/Toast.vue'
import { api, clearToken, isAuthenticated } from '../services/api'

const router = useRouter()

const isImportModalOpen = ref(false)
const importLoading = ref(false)
const colabLoading = ref(false)
const customCsvPath = ref('')
const customXlsPath = ref('')

// Sincronizacion K20
const isSyncModalOpen = ref(false)
const syncEnCurso = ref(false)
const syncFase = ref('')
const syncResultado = ref(null)
const syncEstado = ref(null)
const probando = ref(false)
let pollTimer = null
let sesionTimer = null

const toast = ref({
  show: false,
  type: 'info',
  title: '',
  message: '',
})

function showToast(type, title, message) {
  toast.value = {
    show: true,
    type,
    title,
    message,
  }
  setTimeout(() => {
    toast.value.show = false
  }, 6000)
}

provide('showToast', showToast)

async function executeImport() {
  importLoading.value = true
  try {
    const res = await api.triggerImport(customCsvPath.value || null)
    isImportModalOpen.value = false
    showToast(
      'success',
      'Importación Completada',
      `Leídos: ${res.data.total_leidos} | Nuevos: ${res.data.nuevos_registros} | Duplicados: ${res.data.duplicados_omitidos} | Tiempo: ${res.data.tiempo_segundos}s`
    )
    window.dispatchEvent(new CustomEvent('records-imported'))
  } catch (err) {
    showToast(
      'error',
      'Error en la Importación',
      err.response?.data?.detail || err.message || 'No se pudo completar la importación.'
    )
  } finally {
    importLoading.value = false
  }
}

async function executeColaboradoresImport() {
  colabLoading.value = true
  try {
    const res = await api.triggerImportColaboradores(customXlsPath.value || null)
    showToast(
      'success',
      'Padrón de Colaboradores Importado',
      `Procesados: ${res.data.total_procesados} | Creados: ${res.data.trabajadores_creados} | Actualizados: ${res.data.trabajadores_actualizados} | Sin nombre en archivo: ${res.data.nombres_no_disponibles} | Sin coincidencia: ${res.data.codigos_sin_coincidencia} | Errores: ${res.data.errores}`
    )
    window.dispatchEvent(new CustomEvent('records-imported'))
  } catch (err) {
    showToast(
      'error',
      'Error al Importar Colaboradores',
      err.response?.data?.detail || err.message || 'No se pudo completar la importación del padrón.'
    )
  } finally {
    colabLoading.value = false
  }
}

async function refrescarEstadoSync() {
  try {
    const res = await api.getEstadoSincronizacion()
    syncEstado.value = res.data
    const actual = res.data.ejecucion_actual
    if (actual) {
      syncEnCurso.value = true
      syncFase.value = actual.mensaje_detalle || 'Procesando...'
      if (actual.estado !== 'en_progreso') {
        syncResultado.value = actual
        syncEnCurso.value = false
        stopPolling()
      }
    } else {
      if (syncEnCurso.value && syncEstado.value?.ultima_ejecucion) {
        syncResultado.value = syncEstado.value.ultima_ejecucion
      }
      syncEnCurso.value = false
      stopPolling()
    }
  } catch (e) {
    // silencioso
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refrescarEstadoSync, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function iniciarSync() {
  syncResultado.value = null
  syncFase.value = 'Iniciando...'
  try {
    const res = await api.iniciarSincronizacionK20()
    syncEnCurso.value = true
    syncFase.value = res.data.mensaje
    startPolling()
    if (!res.data.iniciado) {
      showToast('info', 'Sincronización', res.data.mensaje)
    }
  } catch (err) {
    showToast(
      'error',
      'Error al Sincronizar',
      err.response?.data?.detail || err.message || 'No se pudo iniciar la sincronización.'
    )
    syncEnCurso.value = false
  }
}

async function probarConexion() {
  probando.value = true
  try {
    const res = await api.probarConexionK20()
    showToast(
      res.data.conexion_ok ? 'success' : 'error',
      res.data.conexion_ok ? 'Conexión OK' : 'Sin conexión',
      res.data.mensaje
    )
    await refrescarEstadoSync()
  } catch (err) {
    showToast('error', 'Error', err.response?.data?.detail || err.message)
  } finally {
    probando.value = false
  }
}

function cerrarSyncModal() {
  if (syncEnCurso.value) return
  isSyncModalOpen.value = false
  if (syncResultado.value && syncResultado.value.estado === 'completado') {
    window.dispatchEvent(new CustomEvent('records-imported'))
  }
}

function logout() {
  clearToken()
  router.push({ name: 'Login' })
}

// Si el token vencio (o se borro), salir al login desde cualquier pantalla.
function vigilarSesion() {
  if (!isAuthenticated()) {
    clearToken()
    stopPolling()
    if (router.currentRoute.value.name !== 'Login') {
      router.push({ name: 'Login', query: { expirada: '1' } })
    }
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
  refrescarEstadoSync()
  // Vencimiento del token: si expira mientras la pestana esta abierta, se
  // cierra la sesion sin esperar a que una peticion falle con 401.
  sesionTimer = setInterval(vigilarSesion, 30000)
})

onUnmounted(() => {
  stopPolling()
  if (sesionTimer) clearInterval(sesionTimer)
})
</script>

