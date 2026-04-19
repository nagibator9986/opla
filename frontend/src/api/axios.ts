import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (val: string) => void; reject: (err: unknown) => void }> = []

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }
      isRefreshing = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        useAuthStore.getState().clearAuth()
        return Promise.reject(error)
      }
      try {
        const baseURL = import.meta.env.VITE_API_URL ?? '/api/v1'
        const { data } = await axios.post(`${baseURL}/auth/token/refresh/`, { refresh: refreshToken })
        localStorage.setItem('access_token', data.access)
        failedQueue.forEach(({ resolve }) => resolve(data.access))
        failedQueue = []
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return api(originalRequest)
      } catch {
        failedQueue.forEach(({ reject: rej }) => rej(error))
        failedQueue = []
        useAuthStore.getState().clearAuth()
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)

export default api
