export interface Evidence {
  quote: string
  type: 'direct_quote' | 'implied_info' | 'quantitative_data' | 'process_detail'
  context: string
  relevance: string
}

export interface EvidenceRegistry {
  [key: string]: Evidence
}

export interface AnalysisSection {
  summary: string
  evidence_ids: string[]
}

export interface SalesWhys {
  why_anything: AnalysisSection
  why_now: AnalysisSection
  why_us: AnalysisSection
}

export interface BusinessContext {
  corporate_objectives: AnalysisSection
  domain_initiatives: AnalysisSection
  domain_challenges: AnalysisSection
}

export interface MEDDIC {
  metrics: AnalysisSection
  economic_buyer: AnalysisSection
  decision_process: AnalysisSection
  decision_criteria: AnalysisSection
  implicated_pain: AnalysisSection
  champion: AnalysisSection
}

export interface DealReview {
  stage_readiness: 'More Discovery Needed' | 'Ready for Demo'
  confidence_note: string
  critical_gaps: string[]
  next_call_objectives: string[]
}

export interface AnalysisResult {
  evidence_registry: EvidenceRegistry
  sales_whys: SalesWhys
  business_context: BusinessContext
  meddic: MEDDIC
  is_sample: boolean
  deal_review?: {
    deal_review: DealReview
  }
}

export type TabType = 'upload' | 'three-whys' | 'business' | 'meddic' | 'deal-review'
