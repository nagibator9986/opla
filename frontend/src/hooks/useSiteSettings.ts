import { useQuery } from '@tanstack/react-query'
import { getSiteSettings, type SiteSettings } from '../api/site'

const FALLBACK: SiteSettings = {
  payments_enabled: false,
  free_mode_banner: 'Период открытого доступа · аудит бесплатно',
}

export function useSiteSettings() {
  return useQuery({
    queryKey: ['site-settings'],
    queryFn: getSiteSettings,
    staleTime: 60 * 1000,
    placeholderData: FALLBACK,
  })
}
