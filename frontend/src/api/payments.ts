import api from './axios'
import type { UpsellConfig } from '../types/api'

export async function initiateUpsell(submissionId: string): Promise<UpsellConfig> {
  const { data } = await api.post<UpsellConfig>('/payments/upsell/', { submission_id: submissionId })
  return data
}
