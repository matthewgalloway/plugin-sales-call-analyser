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
    progressMessage.value = 'Uploading transcript...'

    try {
      let evidenceData: any = null
      let analysisData: any = null

      await analysisAPI.analyzeTranscriptStreamed(file, (update) => {
        if (update.stage === 'error') {
          error.value = update.error || 'Analysis failed'
          return
        }

        if (update.stage === 'evidence') {
          if (update.status === 'started') {
            progressMessage.value = "Extracting evidence from transcript... Let's face it, this is still faster than you watching the whole discovery call, so be patient 😉"
          } else if (update.status === 'complete' && update.data) {
            evidenceData = update.data
            progressMessage.value = 'Evidence extracted! Analyzing frameworks...'
          }
        } else if (update.stage === 'analysis') {
          if (update.status === 'started') {
            progressMessage.value = 'Analyzing Three Whys and MEDDIC frameworks... Almost there!'
          } else if (update.status === 'complete' && update.data) {
            analysisData = update.data
            progressMessage.value = 'Analysis complete!'
          }
        }

        // When complete, combine the results
        if (update.complete && evidenceData && analysisData) {
          currentAnalysis.value = {
            ...evidenceData,
            ...analysisData,
            is_sample: false,
          }
          currentTab.value = 'three-whys'
        }
      })

      return currentAnalysis.value
    } catch (err: any) {
      error.value = err.message || 'Analysis failed. Please try again.'
      throw err
    } finally {
      isLoading.value = false
      progressMessage.value = ''
    }
  }

  async function analyzeSample() {
    isLoading.value = true
    error.value = null
    progressMessage.value = 'Loading sample transcript...'

    try {
      let evidenceData: any = null
      let analysisData: any = null

      await analysisAPI.analyzeSampleStreamed((update) => {
        if (update.stage === 'error') {
          error.value = update.error || 'Sample analysis failed'
          return
        }

        if (update.stage === 'evidence') {
          if (update.status === 'started') {
            progressMessage.value = "Extracting evidence from sample... Let's face it, this is still faster than you watching the whole discovery call, so be patient 😉"
          } else if (update.status === 'complete' && update.data) {
            evidenceData = update.data
            progressMessage.value = 'Evidence extracted! Analyzing frameworks...'
          }
        } else if (update.stage === 'analysis') {
          if (update.status === 'started') {
            progressMessage.value = 'Analyzing Three Whys and MEDDIC frameworks... Almost there!'
          } else if (update.status === 'complete' && update.data) {
            analysisData = update.data
            progressMessage.value = 'Analysis complete!'
          }
        }

        // When complete, combine the results
        if (update.complete && evidenceData && analysisData) {
          currentAnalysis.value = {
            ...evidenceData,
            ...analysisData,
            is_sample: true,
          }
          currentTab.value = 'three-whys'
        }
      })

      return currentAnalysis.value
    } catch (err: any) {
      error.value = err.message || 'Sample analysis failed. Please try again.'
      throw err
    } finally {
      isLoading.value = false
      progressMessage.value = ''
    }
  }

  async function analyzeText(text: string) {
    isLoading.value = true
    error.value = null
    progressMessage.value = 'Analyzing your text...'

    try {
      let evidenceData: any = null
      let analysisData: any = null

      await analysisAPI.analyzeTextStreamed(text, (update) => {
        if (update.stage === 'error') {
          error.value = update.error || 'Text analysis failed'
          return
        }

        if (update.stage === 'evidence') {
          if (update.status === 'started') {
            progressMessage.value = "Extracting evidence from your text... Let's face it, this is still faster than you watching the whole discovery call, so be patient 😉"
          } else if (update.status === 'complete' && update.data) {
            evidenceData = update.data
            progressMessage.value = 'Evidence extracted! Analyzing frameworks...'
          }
        } else if (update.stage === 'analysis') {
          if (update.status === 'started') {
            progressMessage.value = 'Analyzing Three Whys and MEDDIC frameworks... Almost there!'
          } else if (update.status === 'complete' && update.data) {
            analysisData = update.data
            progressMessage.value = 'Analysis complete!'
          }
        }

        // When complete, combine the results
        if (update.complete && evidenceData && analysisData) {
          currentAnalysis.value = {
            ...evidenceData,
            ...analysisData,
            is_sample: false,
          }
          currentTab.value = 'three-whys'
        }
      })

      return currentAnalysis.value
    } catch (err: any) {
      error.value = err.message || 'Text analysis failed. Please try again.'
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
          sales_whys: currentAnalysis.value.sales_whys,
          business_context: currentAnalysis.value.business_context,
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
    analyzeText,
    analyzeSample,
    generateDealReview,
    setTab,
    resetAnalysis,
    clearError,
  }
})
