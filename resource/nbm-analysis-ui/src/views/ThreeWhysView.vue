<script setup lang="ts">
import { computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import EvidenceCard from '@/components/EvidenceCard.vue'

const analysisStore = useAnalysisStore()

const salesWhys = computed(() => analysisStore.currentAnalysis?.sales_whys)
const evidenceRegistry = computed(() => analysisStore.currentAnalysis?.evidence_registry || {})
</script>

<template>
  <div class="three-whys-view p-8">
    <div class="max-w-6xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Three Whys Framework</h1>
        <p class="text-gray-600">
          Hierarchical analysis from strategic corporate objectives to operational challenges
        </p>
      </div>

      <div v-if="salesWhys" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Why Anything? -->
        <EvidenceCard
          title="Why Anything?"
          :section="salesWhys.why_anything"
          :evidence-registry="evidenceRegistry"
          icon="🎯"
        />

        <!-- Why Now? -->
        <EvidenceCard
          title="Why Now?"
          :section="salesWhys.why_now"
          :evidence-registry="evidenceRegistry"
          icon="🚀"
        />

        <!-- Why Us? -->
        <EvidenceCard
          title="Why Us?"
          :section="salesWhys.why_us"
          :evidence-registry="evidenceRegistry"
          icon="💡"
        />
      </div>

      <div v-else class="text-center py-12 text-gray-500">
        <p>No analysis available. Please upload a transcript first.</p>
      </div>
    </div>
  </div>
</template>
