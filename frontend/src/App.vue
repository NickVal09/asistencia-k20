<template>
  <router-view />
</template>

<script setup>
// La aplicacion solo monta la vista.
// - /login  -> LoginView (pantalla independiente, sin sidebar ni navbar)
// - Resto   -> AppLayout (sidebar + navbar + modales) con las vistas protegidas
</script>
