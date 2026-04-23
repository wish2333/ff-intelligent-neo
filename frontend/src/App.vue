<script setup lang="ts">
/**
 * Root layout: AppNavbar + router-view.
 * Provides shared state via provide/inject pattern.
 */
import AppNavbar from "./components/layout/AppNavbar.vue"
</script>

<template>
  <div class="flex h-screen flex-col bg-base-100 text-base-content">
    <AppNavbar />
    <router-view />
  </div>
</template>
