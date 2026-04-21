import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/authStore'

const baseURL = import.meta.env.VITE_API_URL ?? '/api/v1'

const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Cross-tab logout: if access_token is cleared in another tab, mirror it here.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === 'access_token' && !e.newValue) {
      useAuthStore.getState().clearAuth()
    }
  })
}

// Single in-flight refresh promise. Concurrent 401s await the same refresh
// instead of racing and burning the refresh token.
let refreshPromise: Promise<string> | null = null

async function performRefresh(): Promise<string> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    throw new Error('missing refresh token')
  }
  const { data } = await axios.post(`${baseURL}/auth/token/refresh/`, {
    refresh: refreshToken,
  })
  localStorage.setItem('access_token', data.access)
  // SimpleJWT with ROTATE_REFRESH_TOKENS returns a new refresh token — persist it.
  if (data.refresh) {
    localStorage.setItem('refresh_token', data.refresh)
  }
  return data.access as string
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const originalRequest = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined

    if (status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        refreshPromise ??= performRefresh().finally(() => {
          // Reset only after the promise settles so waiters still resolve/reject.
          queueMicrotask(() => {
            refreshPromise = null
          })
        })
        const access = await refreshPromise
        originalRequest.headers = {
          ...(originalRequest.headers ?? {}),
          Authorization: `Bearer ${access}`,
        }
        return api(originalRequest)
      } catch (refreshErr) {
        useAuthStore.getState().clearAuth()
        return Promise.reject(refreshErr)
      }
    }

    if (status === 403) {
      // Surface forbidden explicitly — callers can toast if they want.
      if (import.meta.env.DEV) console.warn('API 403 Forbidden:', originalRequest?.url)
    }

    return Promise.reject(error)
  },
)

export default api
