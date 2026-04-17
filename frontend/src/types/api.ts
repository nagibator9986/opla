export interface Tariff {
  id: number
  code: string
  title: string
  price_kzt: string
  description: string
}

export interface Submission {
  id: string
  status: string
  template_name: string
  industry_name: string
  total_questions: number
  answered_count: number
  tariff_code: string | null
  pdf_url: string | null
  created_at: string
  completed_at: string | null
}

export interface DeeplinkResponse {
  access: string
  refresh: string
  client_profile_id: number
  name: string
}

export interface UpsellConfig {
  publicId: string
  amount: number
  currency: string
  invoiceId: string
  description: string
  accountId: string
  tariff_code: string
}

export interface ContentBlocks {
  [key: string]: string
}
