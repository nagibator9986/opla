import api from './axios'

export interface CaseSummary {
  slug: string
  title: string
  subtitle: string
  company_name: string
  industry: string
  logo_url: string | null
  metric: string
  metric_label: string
  short_text: string
  accent: 'emerald' | 'sky' | 'amber' | 'rose' | 'violet' | 'slate'
  order: number
}

export interface CaseDetail extends CaseSummary {
  cover_url: string | null
  body: string
  published_at: string | null
}

export async function listCases(): Promise<CaseSummary[]> {
  const { data } = await api.get<CaseSummary[] | { results: CaseSummary[] }>('/cases/')
  return Array.isArray(data) ? data : data.results
}

export async function getCase(slug: string): Promise<CaseDetail> {
  const { data } = await api.get<CaseDetail>(`/cases/${slug}/`)
  return data
}
