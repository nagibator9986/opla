import { create } from 'zustand'

interface ClientProfile {
  id: number
  name: string
}

interface AuthState {
  isAuthenticated: boolean
  clientProfile: ClientProfile | null
  // When the user pays a tariff, we save the new submission_id here so the
  // cabinet page can offer «Начать анкету» that opens the chat widget and
  // calls /chat/start-questionnaire/ against (session, submission) pair.
  pendingQuestionnaireSubmissionId: string | null
  setAuth: (profile: ClientProfile, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
  setPendingQuestionnaire: (submissionId: string | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  clientProfile: JSON.parse(localStorage.getItem('client_profile') ?? 'null'),
  pendingQuestionnaireSubmissionId: localStorage.getItem('pending_q_sub') || null,
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
    localStorage.removeItem('pending_q_sub')
    set({
      isAuthenticated: false,
      clientProfile: null,
      pendingQuestionnaireSubmissionId: null,
    })
  },
  setPendingQuestionnaire: (submissionId) => {
    if (submissionId) localStorage.setItem('pending_q_sub', submissionId)
    else localStorage.removeItem('pending_q_sub')
    set({ pendingQuestionnaireSubmissionId: submissionId })
  },
}))
