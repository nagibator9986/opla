/**
 * Pull a user-readable message out of an axios/DRF error.
 *
 * DRF returns ``{"detail": "..."}`` on 4xx/5xx with custom messages
 * (the AI service uses this). Falling back to ``error.message`` would
 * surface ``Request failed with status code 503`` to the user, which
 * is jargon and not actionable.
 */
import { AxiosError } from 'axios'

export function apiErrorMessage(err: unknown, fallback = 'Что-то пошло не так. Попробуйте ещё раз.'): string {
  if (err instanceof AxiosError) {
    const data = err.response?.data as { detail?: string; error?: string } | undefined
    if (data?.detail) return data.detail
    if (data?.error) return data.error
    if (err.code === 'ERR_NETWORK') return 'Нет соединения с сервером. Проверьте интернет.'
  }
  if (err instanceof Error && err.message && !err.message.startsWith('Request failed')) {
    return err.message
  }
  return fallback
}
