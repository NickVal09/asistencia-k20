import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// En uso normal la web compilada y la API se sirven juntas desde el puerto 5173.
// Para desarrollar con recarga en caliente se levanta Vite en 5174 y se hace
// proxy de /api hacia el servicio principal (iniciar_frontend.bat).
const puerto = Number(process.env.VITE_PORT || 5173)
const destinoApi = process.env.VITE_API_TARGET || 'http://127.0.0.1:5173'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '127.0.0.1',
    port: puerto,
    proxy: {
      '/api': {
        target: destinoApi,
        changeOrigin: true,
      },
    },
  },
})
