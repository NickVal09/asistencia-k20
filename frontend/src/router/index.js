import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import MarcacionesView from '../views/MarcacionesView.vue'
import TrabajadoresView from '../views/TrabajadoresView.vue'
import ExportacionesView from '../views/ExportacionesView.vue'
import DispositivoView from '../views/DispositivoView.vue'
import LoginView from '../views/LoginView.vue'
import { getToken } from '../services/api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { title: 'Iniciar Sesión', public: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: { title: 'Dashboard General' }
  },
  {
    path: '/marcaciones',
    name: 'Marcaciones',
    component: MarcacionesView,
    meta: { title: 'Historial de Marcaciones' }
  },
  {
    path: '/trabajadores',
    name: 'Trabajadores',
    component: TrabajadoresView,
    meta: { title: 'Padrón de Trabajadores' }
  },
  {
    path: '/exportaciones',
    name: 'Exportaciones',
    component: ExportacionesView,
    meta: { title: 'Centro de Exportación' }
  },
  {
    path: '/dispositivo',
    name: 'Dispositivo',
    component: DispositivoView,
    meta: { title: 'Dispositivo ZKTeco K20' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Control'} | Asistencia K20`
  if (to.meta.public) {
    if (to.name === 'Login' && getToken()) return next({ name: 'Dashboard' })
    return next()
  }
  if (!getToken()) return next({ name: 'Login', query: { redirect: to.fullPath } })
  next()
})

export default router

