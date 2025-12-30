<script setup lang="ts">
import { computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import EvidenceCard from '@/components/EvidenceCard.vue'

const analysisStore = useAnalysisStore()

const threeWhys = computed(() => analysisStore.currentAnalysis?.three_whys)
const evidenceRegistry = computed(() => analysisStore.currentAnalysis?.evidence_registry || {})
</script>

<template>
  <div class="business-view p-8">
    <div class="max-w-6xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Business Challenge Deep Dive</h1>
        <p class="text-gray-600">
          Detailed breakdown of corporate objectives, initiatives, and operational challenges
        </p>
      </div>

      <div v-if="threeWhys" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Corporate Objectives -->
        <EvidenceCard
          title="Corporate Objectives"
          :section="threeWhys.corporate_objectives"
          :evidence-registry="evidenceRegistry"
          icon="🏢"
        />

        <!-- Domain Initiatives -->
        <EvidenceCard
          title="Domain Initiatives"
          :section="threeWhys.domain_initiatives"
          :evidence-registry="evidenceRegistry"
          icon="📋"
        />

        <!-- Domain Challenges -->
        <EvidenceCard
          title="Domain Challenges"
          :section="threeWhys.domain_challenges"
          :evidence-registry="evidenceRegistry"
          icon="⚡"
        />
      </div>

      <div v-else class="text-center py-12 text-gray-500">
        <p>No analysis available. Please upload a transcript first.</p>
      </div>
    </div>
  </div>
</template>
