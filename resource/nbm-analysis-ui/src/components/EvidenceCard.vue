<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AnalysisSection, EvidenceRegistry } from '@/types/analysis'

const props = defineProps<{
  title: string
  section: AnalysisSection
  evidenceRegistry: EvidenceRegistry
  icon?: string
}>()

const activeView = ref<'summary' | 'evidence'>('summary')

const evidenceItems = computed(() => {
  return props.section.evidence_ids
    .map((id) => ({
      id,
      ...props.evidenceRegistry[id],
    }))
    .filter((item) => item.quote !== undefined)
})

function getTypeColor(type: string): string {
  const colors: Record<string, string> = {
    direct_quote: 'bg-blue-100 text-blue-800',
    implied_info: 'bg-purple-100 text-purple-800',
    quantitative_data: 'bg-green-100 text-green-800',
    process_detail: 'bg-orange-100 text-orange-800',
  }
  return colors[type] || 'bg-gray-100 text-gray-800'
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    direct_quote: 'Direct Quote',
    implied_info: 'Implied',
    quantitative_data: 'Quantitative',
    process_detail: 'Process',
  }
  return labels[type] || type
}
</script>

<template>
  <div class="evidence-card bg-white rounded-lg shadow-md overflow-hidden">
    <!-- Card Header -->
    <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4">
      <div class="flex items-center gap-2 mb-2">
        <span v-if="icon" class="text-2xl">{{ icon }}</span>
        <h3 class="text-xl font-bold">{{ title }}</h3>
      </div>
      <div class="flex gap-2">
        <button
          @click="activeView = 'summary'"
          :class="[
            'px-4 py-1 rounded text-sm font-medium transition-colors',
            activeView === 'summary'
              ? 'bg-white text-blue-600'
              : 'bg-blue-500 text-white hover:bg-blue-400',
          ]"
        >
          Summary
        </button>
        <button
          @click="activeView = 'evidence'"
          :class="[
            'px-4 py-1 rounded text-sm font-medium transition-colors',
            activeView === 'evidence'
              ? 'bg-white text-blue-600'
              : 'bg-blue-500 text-white hover:bg-blue-400',
          ]"
        >
          Evidence ({{ evidenceItems.length }})
        </button>
      </div>
    </div>

    <!-- Card Body -->
    <div class="p-6">
      <!-- Summary View -->
      <div v-if="activeView === 'summary'" class="summary-view">
        <p class="text-gray-700 leading-relaxed whitespace-pre-wrap">{{ section.summary }}</p>
      </div>

      <!-- Evidence View -->
      <div v-else class="evidence-view space-y-4">
        <div v-if="evidenceItems.length === 0" class="text-center py-8 text-gray-500">
          <p>No evidence found for this section</p>
        </div>
        <div
          v-for="evidence in evidenceItems"
          :key="evidence.id"
          class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between mb-2">
            <span class="text-xs font-mono text-gray-500">{{ evidence.id }}</span>
            <span :class="['text-xs px-2 py-1 rounded-full font-medium', getTypeColor(evidence.type)]">
              {{ getTypeLabel(evidence.type) }}
            </span>
          </div>
          <blockquote class="border-l-4 border-blue-500 pl-4 mb-3">
            <p class="text-gray-800 italic">"{{ evidence.quote }}"</p>
          </blockquote>
          <div class="text-sm text-gray-600 space-y-1">
            <p><strong>Context:</strong> {{ evidence.context }}</p>
            <p><strong>Relevance:</strong> {{ evidence.relevance }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-view,
.evidence-view {
  min-height: 150px;
}
</style>
