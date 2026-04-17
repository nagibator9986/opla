import { useQuery } from '@tanstack/react-query'
import { getMySubmission } from '../api/submissions'
import { useAuthStore } from '../store/authStore'

export function useSubmission() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['my-submission'],
    queryFn: getMySubmission,
    enabled: isAuthenticated,
    staleTime: 30_000,
  })
}
