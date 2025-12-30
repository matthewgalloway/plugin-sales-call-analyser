import type { AxiosInstance } from 'axios'
import type { AnalysisResult, DealReview } from '@/types/analysis'

export class AnalysisAPI {
  private client: AxiosInstance

  constructor(client: AxiosInstance) {
    this.client = client
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
}
