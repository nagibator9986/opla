import api from './axios'

export interface SiteSettings {
  payments_enabled: boolean
  free_mode_banner: string
}

export async function getSiteSettings(): Promise<SiteSettings> {
  const { data } = await api.get<SiteSettings>('/site/')
  return data
}
