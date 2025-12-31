import type { AxiosInstance } from 'axios'
import type { AnalysisResult, DealReview } from '@/types/analysis'

export interface StreamUpdate {
  stage: 'evidence' | 'analysis' | 'error'
  status?: 'started' | 'complete'
  data?: any
  error?: string
  complete: boolean
}

export class AnalysisAPI {
  private client: AxiosInstance
  private baseURL: string

  constructor(client: AxiosInstance) {
    this.client = client
    this.baseURL = client.defaults.baseURL || ''
  }

  public async analyzeTranscript(file: File): Promise<AnalysisResult> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post<AnalysisResult>(
      '/api/analysis/analyze',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  }

  public async analyzeSample(): Promise<AnalysisResult> {
    const response = await this.client.post<AnalysisResult>('/api/analysis/analyze-sample')
    return response.data
  }

  public async analyzeText(text: string): Promise<AnalysisResult> {
    const response = await this.client.post<AnalysisResult>(
      '/api/analysis/analyze-text',
      { text }
    )
    return response.data
  }

  public async generateDealReview(
    evidence_registry: any,
    analysis_data: any
  ): Promise<{ deal_review: DealReview }> {
    const response = await this.client.post<{ deal_review: DealReview }>(
      '/api/analysis/deal-review',
      {
        evidence_registry,
        analysis_data: {
          three_whys: analysis_data.three_whys,
          meddic: analysis_data.meddic,
        },
      }
    )
    return response.data
  }

  public async analyzeTranscriptStreamed(
    file: File,
    onUpdate: (update: StreamUpdate) => void
  ): Promise<void> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseURL}/api/analysis/analyze-stream`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok || !response.body) {
      throw new Error(`Stream request failed: ${response.status} ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim()
            if (data) {
              try {
                const update = JSON.parse(data) as StreamUpdate
                onUpdate(update)

                if (update.complete) {
                  return
                }
              } catch (parseError) {
                console.error('Failed to parse SSE data:', data, parseError)
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream reading error:', error)
      throw error
    } finally {
      reader.releaseLock()
    }
  }

  public async analyzeSampleStreamed(onUpdate: (update: StreamUpdate) => void): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/analysis/analyze-sample-stream`, {
      method: 'POST',
    })

    if (!response.ok || !response.body) {
      throw new Error(`Stream request failed: ${response.status} ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim()
            if (data) {
              try {
                const update = JSON.parse(data) as StreamUpdate
                onUpdate(update)

                if (update.complete) {
                  return
                }
              } catch (parseError) {
                console.error('Failed to parse SSE data:', data, parseError)
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream reading error:', error)
      throw error
    } finally {
      reader.releaseLock()
    }
  }

  public async analyzeTextStreamed(
    text: string,
    onUpdate: (update: StreamUpdate) => void
  ): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/analysis/analyze-text-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    })

    if (!response.ok || !response.body) {
      throw new Error(`Stream request failed: ${response.status} ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim()
            if (data) {
              try {
                const update = JSON.parse(data) as StreamUpdate
                onUpdate(update)

                if (update.complete) {
                  return
                }
              } catch (parseError) {
                console.error('Failed to parse SSE data:', data, parseError)
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream reading error:', error)
      throw error
    } finally {
      reader.releaseLock()
    }
  }
}
