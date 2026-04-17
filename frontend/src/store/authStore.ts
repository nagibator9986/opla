import { create } from 'zustand'

interface ClientProfile {
  id: number
  name: string
}

interface AuthState {
  isAuthenticated: boolean
  clientProfile: ClientProfile | null
  setAuth: (profile: ClientProfile, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  clientProfile: JSON.parse(localStorage.getItem('client_profile') ?? 'null'),
  setAuth: (profile, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('client_profile', JSON.stringify(profile))
    set({ isAuthenticated: true, clientProfile: profile })
  },
  clearAuth: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('client_profile')
    set({ isAuthenticated: false, clientProfile: null })
  },
}))
