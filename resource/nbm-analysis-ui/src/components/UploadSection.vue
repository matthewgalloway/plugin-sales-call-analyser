<script setup lang="ts">
import { ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'

const analysisStore = useAnalysisStore()
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

async function handleUpload() {
  if (!selectedFile.value) return

  try {
    await analysisStore.analyzeFile(selectedFile.value)
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  } catch (error) {
    console.error('Upload failed:', error)
  }
}

async function handleTrySample() {
  try {
    await analysisStore.analyzeSample()
  } catch (error) {
    console.error('Sample analysis failed:', error)
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}
</script>

<template>
  <div class="upload-section max-w-2xl mx-auto">
    <div class="text-center mb-8">
      <h2 class="text-3xl font-bold text-gray-800 mb-2">Upload Your Sales Call Transcript</h2>
      <p class="text-gray-600">
        Get AI-powered insights using the 3 Whys and MEDDIC frameworks
      </p>
    </div>

    <div
      class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors"
    >
      <div class="mb-4">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>

      <input
        ref="fileInput"
        type="file"
        accept=".txt,.docx"
        @change="handleFileSelect"
        class="hidden"
      />

      <button
        @click="triggerFileInput"
        class="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors mb-3"
      >
        Choose File
      </button>

      <p v-if="selectedFile" class="text-sm text-gray-600 mb-3">
        Selected: <span class="font-medium">{{ selectedFile.name }}</span>
      </p>

      <p class="text-xs text-gray-500 mb-4">Supports .txt and .docx files (max 5MB)</p>

      <button
        v-if="selectedFile"
        @click="handleUpload"
        :disabled="analysisStore.isLoading"
        class="bg-green-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {{ analysisStore.isLoading ? 'Analyzing...' : 'Analyze Transcript' }}
      </button>
    </div>

    <!-- Try Sample Button -->
    <div class="mt-6 text-center">
      <p class="text-sm text-gray-600 mb-2">Don't have a transcript handy?</p>
      <button
        @click="handleTrySample"
        :disabled="analysisStore.isLoading"
        class="text-blue-600 hover:text-blue-700 font-medium underline disabled:text-gray-400 disabled:no-underline"
      >
        Try with a sample transcript
      </button>
    </div>

    <!-- Loading Progress -->
    <div v-if="analysisStore.isLoading" class="mt-8">
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div class="flex items-center justify-center mb-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
        <p class="text-center text-gray-700 font-medium">
          {{ analysisStore.progressMessage || 'Processing...' }}
        </p>
        <p class="text-center text-sm text-gray-500 mt-2">
          This typically takes 30-60 seconds
        </p>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="analysisStore.error" class="mt-6">
      <div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
        <span class="text-red-600 text-xl">⚠️</span>
        <div class="flex-1">
          <p class="text-red-800 font-medium">Analysis Failed</p>
          <p class="text-red-700 text-sm mt-1">{{ analysisStore.error }}</p>
        </div>
        <button
          @click="analysisStore.clearError()"
          class="text-red-600 hover:text-red-800 text-xl"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>
