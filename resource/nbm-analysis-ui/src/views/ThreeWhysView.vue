<script setup lang="ts">
import { computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import EvidenceCard from '@/components/EvidenceCard.vue'

const analysisStore = useAnalysisStore()

const threeWhys = computed(() => analysisStore.currentAnalysis?.three_whys)
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

      <div v-if="threeWhys" class="space-y-6">
        <!-- Why Anything? / Corporate Objectives -->
        <EvidenceCard
          title="Why Anything? - Corporate Objectives"
          :section="threeWhys.corporate_objectives"
          :evidence-registry="evidenceRegistry"
          icon="🎯"
        />

        <!-- Why Now? / Domain Initiatives -->
        <EvidenceCard
          title="Why Now? - Domain Initiatives"
          :section="threeWhys.domain_initiatives"
          :evidence-registry="evidenceRegistry"
          icon="🚀"
        />

        <!-- Why Our Company? / Domain Challenges -->
        <EvidenceCard
          title="Why Our Company? - Domain Challenges"
          :section="threeWhys.domain_challenges"
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
