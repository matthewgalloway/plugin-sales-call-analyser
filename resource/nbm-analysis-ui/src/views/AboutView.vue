<template>
  <div class="about">
    <div style="display: flex; flex-direction: column;">
    <h1>This is an about page</h1>
    <button @click="helloWorld">Click me to call the server API</button>
    <p v-if="helloWorldResult !== ''">{{ helloWorldResult }}</p></div>
  </div>
</template>

<script lang="ts" setup>
import { serverAPI } from '@/main.ts'
import { ref } from 'vue'

const helloWorldResult = ref<string>('')

const helloWorld = async () => {
  helloWorldResult.value = await serverAPI.getHelloWorld()
}
</script>

<style>

@media (min-width: 1024px) {
  .about {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>
