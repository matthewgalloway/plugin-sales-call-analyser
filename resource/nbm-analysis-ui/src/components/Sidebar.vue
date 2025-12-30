<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { TabType } from '@/types/analysis'

const router = useRouter()
const analysisStore = useAnalysisStore()

const tabs = computed(() => [
  { id: 'upload' as TabType, label: 'Upload', icon: '📄', disabled: false },
  {
    id: 'three-whys' as TabType,
    label: '3 Whys',
    icon: '🎯',
    disabled: !analysisStore.currentAnalysis,
  },
  {
    id: 'business' as TabType,
    label: 'Business Challenge',
    icon: '💼',
    disabled: !analysisStore.currentAnalysis,
  },
  {
    id: 'meddic' as TabType,
    label: 'MEDDIC',
    icon: '📊',
    disabled: !analysisStore.currentAnalysis,
  },
  {
    id: 'deal-review' as TabType,
    label: 'Deal Review',
    icon: '✅',
    disabled: !analysisStore.currentAnalysis,
  },
])

function selectTab(tabId: TabType) {
  const tab = tabs.value.find((t) => t.id === tabId)
  if (!tab?.disabled) {
    router.push(`/${tabId}`)
  }
}
</script>

<template>
  <div class="sidebar bg-navy-900 text-white h-screen w-64 flex flex-col">
    <!-- Logo/Header -->
    <div class="p-6 border-b border-navy-800">
      <h1 class="text-2xl font-bold">NBM Analysis</h1>
      <p class="text-sm text-gray-400 mt-1">Sales Call Insights</p>
    </div>

    <!-- Navigation Tabs -->
    <nav class="flex-1 overflow-y-auto py-4">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="selectTab(tab.id)"
        :disabled="tab.disabled"
        :class="[
          'w-full px-6 py-3 text-left flex items-center gap-3 transition-colors',
          analysisStore.currentTab === tab.id
            ? 'bg-blue-600 text-white'
            : tab.disabled
              ? 'text-gray-500 cursor-not-allowed'
              : 'text-gray-300 hover:bg-navy-800',
        ]"
      >
        <span class="text-xl">{{ tab.icon }}</span>
        <span class="font-medium">{{ tab.label }}</span>
      </button>
    </nav>

    <!-- Footer -->
    <div class="p-4 border-t border-navy-800 text-xs text-gray-400">
      <p>Powered by Dataiku LLM</p>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
}
</style>
