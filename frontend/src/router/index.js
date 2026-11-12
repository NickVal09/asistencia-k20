import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '../layouts/AppLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import MarcacionesView from '../views/MarcacionesView.vue'
import TrabajadoresView from '../views/TrabajadoresView.vue'
import ExportacionesView from '../views/ExportacionesView.vue'
import DispositivoView from '../views/DispositivoView.vue'
import LoginView from '../views/LoginView.vue'
import { isAuthenticated, sesionExpirada } from '../services/api'

/**
 * Estructura de rutas:
 *
 *   /login  -> LoginView  (publica, pantalla completa, SIN sidebar ni navbar)
 *   /       -> AppLayout  (protegida: sidebar + navbar)
 *     /                 Dashboard
 *     /marcaciones      Historial de marcaciones
 *     /trabajadores     Padron de trabajadores
 *     /exportaciones    Centro de exportacion
 *     /dispositivo      Dispositivo ZKTeco K20
 *
 * AppLayout solo se monta si la sesion es valida, asi que el sidebar jamas
 * aparece en la pantalla de login ni en una ruta protegida sin autenticar.
 */
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { title: 'Iniciar Sesion', public: true },
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: DashboardView,
        meta: { title: 'Dashboard General' },
      },
      {
        path: 'marcaciones',
        name: 'Marcaciones',
        component: MarcacionesView,
        meta: { title: 'Historial de Marcaciones' },
      },
      {
        path: 'trabajadores',
        name: 'Trabajadores',
        component: TrabajadoresView,
        meta: { title: 'Padron de Trabajadores' },
      },
      {
        path: 'exportaciones',
        name: 'Exportaciones',
        component: ExportacionesView,
        meta: { title: 'Centro de Exportacion' },
      },
      {
        path: 'dispositivo',
        name: 'Dispositivo',
        component: DispositivoView,
        meta: { title: 'Dispositivo ZKTeco K20' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || 'Control'} | Asistencia K20`

  const autenticado = isAuthenticated()

  // Rutas publicas (login)
  if (to.meta.public) {
    if (to.name === 'Login' && autenticado) return { name: 'Dashboard' }
    return true
  }

  // Cualquier otra ruta exige sesion vigente
  if (!autenticado) {
    const query = { redirect: to.fullPath }
    if (sesionExpirada()) query.expirada = '1'
    return { name: 'Login', query }
  }

  return true
})

export default router
