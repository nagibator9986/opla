import api from './axios'

export interface InviteParticipant {
  name: string
  company: string
  status: 'invited' | 'in_progress' | 'completed' | 'expired'
}

export interface InviteQuestion {
  question_id: number
  order: number
  stage: string
  text: string
  field_type: 'text' | 'longtext' | 'number' | 'choice' | 'multichoice' | 'url'
  placeholder: string
  choices: string[]
  progress: { done: number; total: number }
}

export interface InviteContext {
  participant: InviteParticipant
  intro?: string
  next_question?: InviteQuestion | null
  first_question?: InviteQuestion | null
  completed?: boolean
  thanks?: string
  progress: { done: number; total: number }
}

export async function getInviteContext(token: string): Promise<InviteContext> {
  const { data } = await api.get<InviteContext>(`/invite/${token}/`)
  return data
}

export interface InviteAnswerInput {
  question_id: number
  value?: string | null
  values?: string[]
}

export async function submitInviteAnswer(
  token: string,
  payload: InviteAnswerInput,
): Promise<InviteContext> {
  const { data } = await api.post<InviteContext>(`/invite/${token}/answer/`, payload)
  return data
}
