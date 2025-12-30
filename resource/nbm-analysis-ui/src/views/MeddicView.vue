<script setup lang="ts">
import { computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import EvidenceCard from '@/components/EvidenceCard.vue'

const analysisStore = useAnalysisStore()

const meddic = computed(() => analysisStore.currentAnalysis?.meddic)
const evidenceRegistry = computed(() => analysisStore.currentAnalysis?.evidence_registry || {})
</script>

<template>
  <div class="meddic-view p-8">
    <div class="max-w-7xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">MEDDIC Analysis</h1>
        <p class="text-gray-600">
          Comprehensive qualification framework for sales opportunities
        </p>
      </div>

      <div v-if="meddic" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Metrics -->
        <EvidenceCard
          title="Metrics"
          :section="meddic.metrics"
          :evidence-registry="evidenceRegistry"
          icon="📈"
        />

        <!-- Economic Buyer -->
        <EvidenceCard
          title="Economic Buyer"
          :section="meddic.economic_buyer"
          :evidence-registry="evidenceRegistry"
          icon="💰"
        />

        <!-- Decision Process -->
        <EvidenceCard
          title="Decision Process"
          :section="meddic.decision_process"
          :evidence-registry="evidenceRegistry"
          icon="🔄"
        />

        <!-- Decision Criteria -->
        <EvidenceCard
          title="Decision Criteria"
          :section="meddic.decision_criteria"
          :evidence-registry="evidenceRegistry"
          icon="✓"
        />

        <!-- Implicated Pain -->
        <EvidenceCard
          title="Implicated Pain"
          :section="meddic.implicated_pain"
          :evidence-registry="evidenceRegistry"
          icon="⚠️"
        />

        <!-- Champion -->
        <EvidenceCard
          title="Champion"
          :section="meddic.champion"
          :evidence-registry="evidenceRegistry"
          icon="🏆"
        />
      </div>

      <div v-else class="text-center py-12 text-gray-500">
        <p>No analysis available. Please upload a transcript first.</p>
      </div>
    </div>
  </div>
</template>
