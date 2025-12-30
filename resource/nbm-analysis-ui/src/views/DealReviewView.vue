<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'

const analysisStore = useAnalysisStore()

const dealReview = computed(() => analysisStore.currentAnalysis?.deal_review?.deal_review)
const hasGenerated = computed(() => !!dealReview.value)

async function generateReview() {
  try {
    await analysisStore.generateDealReview()
  } catch (error) {
    console.error('Failed to generate deal review:', error)
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  // Could add a toast notification here
}

function copyAllObjectives() {
  if (dealReview.value?.next_call_objectives) {
    const text = dealReview.value.next_call_objectives.join('\n\n')
    copyToClipboard(text)
  }
}
</script>

<template>
  <div class="deal-review-view p-8">
    <div class="max-w-4xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Deal Review</h1>
        <p class="text-gray-600">
          Honest assessment of deal strength and next steps
        </p>
      </div>

      <!-- Generate Button -->
      <div v-if="!hasGenerated" class="text-center py-12">
        <div class="bg-white rounded-lg shadow-md p-8 max-w-md mx-auto">
          <div class="mb-4 text-5xl">📋</div>
          <h2 class="text-xl font-bold text-gray-800 mb-2">Ready for Deal Review?</h2>
          <p class="text-gray-600 mb-6">
            Get an honest assessment of this opportunity's readiness and identify critical gaps
          </p>
          <button
            @click="generateReview"
            :disabled="analysisStore.isLoading"
            class="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {{ analysisStore.isLoading ? 'Generating...' : 'Generate Deal Review' }}
          </button>
        </div>
      </div>

      <!-- Deal Review Content -->
      <div v-else-if="dealReview" class="space-y-6">
        <!-- Stage Readiness -->
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
          <div
            :class="[
              'p-6',
              dealReview.stage_readiness === 'Ready for Demo'
                ? 'bg-green-100 border-l-4 border-green-600'
                : 'bg-yellow-100 border-l-4 border-yellow-600',
            ]"
          >
            <div class="flex items-center gap-3 mb-2">
              <span class="text-3xl">
                {{ dealReview.stage_readiness === 'Ready for Demo' ? '✅' : '🔍' }}
              </span>
              <h2 class="text-2xl font-bold text-gray-800">{{ dealReview.stage_readiness }}</h2>
            </div>
            <p class="text-gray-700 mt-2">{{ dealReview.confidence_note }}</p>
          </div>
        </div>

        <!-- Critical Gaps -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center gap-2 mb-4">
            <span class="text-2xl">⚠️</span>
            <h3 class="text-xl font-bold text-gray-800">Critical Gaps</h3>
          </div>
          <div class="space-y-3">
            <div
              v-for="(gap, index) in dealReview.critical_gaps"
              :key="index"
              class="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg"
            >
              <span class="font-bold text-red-600 mt-0.5">{{ index + 1 }}.</span>
              <p class="text-gray-800 flex-1">{{ gap }}</p>
            </div>
          </div>
        </div>

        <!-- Next Call Objectives -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <span class="text-2xl">🎯</span>
              <h3 class="text-xl font-bold text-gray-800">Next Call Objectives</h3>
            </div>
            <button
              @click="copyAllObjectives"
              class="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              Copy All
            </button>
          </div>
          <div class="space-y-3">
            <div
              v-for="(objective, index) in dealReview.next_call_objectives"
              :key="index"
              class="group relative p-4 bg-blue-50 border border-blue-200 rounded-lg hover:shadow-md transition-shadow"
            >
              <div class="flex items-start gap-3">
                <span class="font-bold text-blue-600 mt-0.5">{{ index + 1 }}.</span>
                <p class="text-gray-800 flex-1">{{ objective }}</p>
                <button
                  @click="copyToClipboard(objective)"
                  class="opacity-0 group-hover:opacity-100 transition-opacity text-blue-600 hover:text-blue-700"
                  title="Copy to clipboard"
                >
                  <svg
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Regenerate Button -->
        <div class="text-center pt-4">
          <button
            @click="generateReview"
            :disabled="analysisStore.isLoading"
            class="text-blue-600 hover:text-blue-700 font-medium underline disabled:text-gray-400 disabled:no-underline"
          >
            Regenerate Deal Review
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
