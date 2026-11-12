<template>
  <aside class="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 h-screen sticky top-0 border-r border-slate-800">
    <!-- Brand / Logo Header -->
    <div class="px-6 py-5 border-b border-slate-800 flex items-center space-x-3">
      <div class="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      </div>
      <div>
        <h1 class="text-white font-bold text-base leading-tight tracking-tight">Asistencia K20</h1>
        <p class="text-xs text-blue-400 font-medium">Control Biométrico</p>
      </div>
    </div>

    <!-- Navigation Links -->
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <router-link
        to="/"
        class="flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all group"
        :class="[$route.path === '/' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60']"
      >
        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
        </svg>
        <span>Dashboard</span>
      </router-link>

      <router-link
        to="/marcaciones"
        class="flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all group"
        :class="[$route.path === '/marcaciones' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60']"
      >
        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
        </svg>
        <span>Marcaciones</span>
      </router-link>

      <router-link
        to="/trabajadores"
        class="flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all group"
        :class="[$route.path === '/trabajadores' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60']"
      >
        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
        </svg>
        <span>Trabajadores</span>
      </router-link>

      <router-link
        to="/exportaciones"
        class="flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all group"
        :class="[$route.path === '/exportaciones' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60']"
      >
        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <span>Exportar Reportes</span>
      </router-link>

      <router-link
        to="/dispositivo"
        class="flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all group"
        :class="[$route.path === '/dispositivo' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60']"
      >
        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
        </svg>
        <span>Dispositivo K20</span>
      </router-link>
    </nav>

    <!-- Footer Dispositivo K20 Info -->
    <div class="p-4 border-t border-slate-800 text-xs">
      <div class="bg-slate-800/80 rounded-lg p-3 space-y-1.5 border border-slate-700/50">
        <div class="flex items-center justify-between text-slate-400">
          <span class="font-medium text-slate-300">Biométrico</span>
          <span class="text-[11px] font-mono text-emerald-400">Listo</span>
        </div>
        <p class="font-semibold text-white">ZKTeco K20</p>
        <p class="text-[11px] text-slate-400 font-mono">192.168.10.69:4370</p>
        <p class="text-[10px] text-slate-500">Plataforma: ZLM60_TFT</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
</script>

