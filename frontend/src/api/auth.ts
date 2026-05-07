import api from './axios'

export interface LoginLinkResponse {
  sent: boolean
  delivered_via: 'whatsapp' | 'fallback' | 'noop'
  /** Появляется только в DEBUG-окружении когда WhatsApp канал не настроен. */
  debug_url?: string
}

export interface MagicVerifyResponse {
  access: string
  refresh: string
  client_profile_id: number
  name: string
}

export async function requestLoginLink(phone_wa: string): Promise<LoginLinkResponse> {
  const { data } = await api.post<LoginLinkResponse>('/auth/login-link/', { phone_wa })
  return data
}

export async function verifyMagicLink(token: string): Promise<MagicVerifyResponse> {
  const { data } = await api.get<MagicVerifyResponse>(`/auth/magic/${token}/`)
  return data
}
