import axios from 'axios'

const TOKEN_KEY = 'k20_access_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Adjunta el Bearer token (si existe) a cada peticion.
apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Reintento automatico (una sola vez) para consultas GET cuando el backend
// aun esta arrancando o hubo un corte momentaneo de conexion.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config
    const esGet = config && (config.method || 'get').toLowerCase() === 'get'
    const cancelada = error.code === 'ERR_CANCELED'
    const falloDeRed = !cancelada && !error.response && error.code !== 'ECONNABORTED'

    // Sesion caducada: limpiar y redirigir al login (salvo la propia peticion de login).
    if (error.response?.status === 401 && !(config?.url || '').includes('/auth/login')) {
      clearToken()
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    if (esGet && falloDeRed && !config.__reintentado) {
      config.__reintentado = true
      await new Promise((resolve) => setTimeout(resolve, 1200))
      return apiClient(config)
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Autenticacion
  login(usuario, password) {
    return apiClient.post('/auth/login', { usuario, password })
  },
  me() {
    return apiClient.get('/auth/me')
  },

  // Dashboard
  getDashboardOverview() {
    return apiClient.get('/dashboard/overview')
  },

  // Marcaciones
  getMarcaciones(params, config = {}) {
    return apiClient.get('/marcaciones', { params, ...config })
  },
  getMarcacionById(id) {
    return apiClient.get(`/marcaciones/${id}`)
  },

  // Trabajadores
  getTrabajadores(params, config = {}) {
    return apiClient.get('/trabajadores', { params, ...config })
  },
  getTrabajadorById(userId) {
    return apiClient.get(`/trabajadores/${userId}`)
  },

  // Importacion
  triggerImport(filePath) {
    const params = filePath ? { archivo_csv: filePath } : {}
    return apiClient.post('/importar/csv', null, { params })
  },
  triggerImportColaboradores(filePath) {
    const params = filePath ? { archivo_xls: filePath } : {}
    return apiClient.post('/importar/colaboradores', null, { params })
  },
  getImportHistory() {
    return apiClient.get('/importar/historial')
  },

  // Dispositivo
  getDispositivos() {
    return apiClient.get('/dispositivos')
  },
  getK20Status() {
    return apiClient.get('/dispositivos/k20/status')
  },

  // Sincronizacion K20
  iniciarSincronizacionK20() {
    return apiClient.post('/sincronizacion/k20')
  },
  getEstadoSincronizacion() {
    return apiClient.get('/sincronizacion/estado')
  },
  probarConexionK20() {
    return apiClient.post('/sincronizacion/probar-conexion')
  },
  getHistorialSincronizacion() {
    return apiClient.get('/sincronizacion/historial')
  },

  // Exportaciones: descarga autenticada por blob
  async descargarExportacion(formato, params = {}, timeout = 120000) {
    const res = await apiClient.get(`/export/${formato}`, {
      params,
      responseType: 'blob',
      timeout,
    })
    const cd = res.headers['content-disposition'] || ''
    const match = cd.match(/filename="?([^";]+)"?/)
    const filename = match ? match[1] : `marcaciones_k20.${formato === 'excel' ? 'xlsx' : 'csv'}`
    const url = window.URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    return filename
  },
}

export default apiClient
