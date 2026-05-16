import api from './axios'

export interface QuickLoginResponse {
  access: string
  refresh: string
  client_profile_id: number
  name: string
}

export async function quickLogin(phone_wa: string): Promise<QuickLoginResponse> {
  const { data } = await api.post<QuickLoginResponse>('/auth/quick-login/', { phone_wa })
  return data
}
