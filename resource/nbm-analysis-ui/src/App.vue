<script setup lang="ts">
import { RouterView } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <div class="app-container flex">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <div class="main-content flex-1 ml-64">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.main-content {
  overflow-y: auto;
}
</style>
