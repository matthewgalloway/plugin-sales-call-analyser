import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AnalysisResult, TabType } from '@/types/analysis'
import { analysisAPI } from '@/main'

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const currentAnalysis = ref<AnalysisResult | null>(null)
  const isLoading = ref(false)
  const currentTab = ref<TabType>('upload')
  const error = ref<string | null>(null)
  const progressMessage = ref<string>('')

  // Actions
  async function analyzeFile(file: File) {
    isLoading.value = true
    error.value = null
    progressMessage.value = 'Uploading and analyzing transcript...'

    try {
      const result = await analysisAPI.analyzeTranscript(file)
      currentAnalysis.value = result
      currentTab.value = 'three-whys'
      return result
    } catch (err: any) {
      error.value = err.response?.data?.error || 'Analysis failed. Please try again.'
      throw err
    } finally {
      isLoading.value = false
      progressMessage.value = ''
    }
  }

  async function analyzeSample() {
    isLoading.value = true
    error.value = null
    progressMessage.value = 'Analyzing sample transcript...'

    try {
      const result = await analysisAPI.analyzeSample()
      currentAnalysis.value = result
      currentTab.value = 'three-whys'
      return result
    } catch (err: any) {
      error.value = err.response?.data?.error || 'Sample analysis failed. Please try again.'
      throw err
    } finally {
      isLoading.value = false
      progressMessage.value = ''
    }
  }

  async function generateDealReview() {
    if (!currentAnalysis.value) {
      error.value = 'No analysis available'
      return
    }

    isLoading.value = true
    error.value = null
    progressMessage.value = 'Generating deal review...'

    try {
      const dealReview = await analysisAPI.generateDealReview(
        currentAnalysis.value.evidence_registry,
        {
          three_whys: currentAnalysis.value.three_whys,
          meddic: currentAnalysis.value.meddic,
        }
      )

      // Update current analysis with deal review
      currentAnalysis.value = {
        ...currentAnalysis.value,
        deal_review: dealReview,
      }

      currentTab.value = 'deal-review'
      return dealReview
    } catch (err: any) {
      error.value = err.response?.data?.error || 'Deal review generation failed. Please try again.'
      throw err
    } finally {
      isLoading.value = false
      progressMessage.value = ''
    }
  }

  function setTab(tab: TabType) {
    currentTab.value = tab
  }

  function resetAnalysis() {
    currentAnalysis.value = null
    currentTab.value = 'upload'
    error.value = null
    progressMessage.value = ''
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    currentAnalysis,
    isLoading,
    currentTab,
    error,
    progressMessage,

    // Actions
    analyzeFile,
    analyzeSample,
    generateDealReview,
    setTab,
    resetAnalysis,
    clearError,
  }
})
