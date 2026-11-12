<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-4">
    <div class="w-full max-w-md bg-white rounded-2xl border border-slate-200/80 shadow-xs p-8">
      <div class="text-center mb-6">
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Asistencia K20</h1>
        <p class="text-xs text-slate-500 mt-1">
          Inicia sesión para consultar marcaciones y ejecutar sincronizaciones.
        </p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Usuario</label>
          <input
            v-model="usuario"
            type="text"
            autocomplete="username"
            class="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
            required
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-700 mb-1">Contraseña</label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
            required
          />
        </div>

        <p v-if="error" class="text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">
          {{ error }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition-colors disabled:opacity-50"
        >
          <span v-if="!loading">Ingresar</span>
          <span v-else>Ingresando...</span>
        </button>
      </form>

      <p class="text-[11px] text-slate-400 mt-6 text-center">
        Acceso protegido. Las credenciales se configuran en el servidor (.env).
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api, setToken } from '../services/api'

const router = useRouter()
const route = useRoute()

const usuario = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.login(usuario.value, password.value)
    setToken(res.data.access_token)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    error.value = err.response?.data?.detail || 'No se pudo iniciar sesión.'
  } finally {
    loading.value = false
  }
}
</script>
