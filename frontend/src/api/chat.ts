import api from './axios'

export interface QuickReply {
  label: string
  payload: string
  /**
   * 'message' (default) — отправить payload как сообщение в чат.
   * 'navigate' — payload это путь, открыть его через router (закрыв чат).
   */
  action?: 'message' | 'navigate'
}

export interface ChatConfig {
  name: string
  greeting: string
  quick_replies: QuickReply[]
}

export type ChatMode = 'chat' | 'questionnaire'

export interface QuestionPayload {
  question_id: number
  order: number
  stage: string
  text: string
  field_type: 'text' | 'longtext' | 'number' | 'choice' | 'multichoice' | 'url'
  placeholder: string
  choices: string[]
  progress: { done: number; total: number }
}

export interface ChatStartResponse {
  session_id: string
  greeting: string
  quick_replies: QuickReply[]
  mode: ChatMode
  is_authenticated?: boolean
}

export interface AssistantReply {
  id?: number
  role: 'assistant'
  content: string
  created_at?: string
}

export interface ChatMessageResponse {
  reply: AssistantReply
  mode?: ChatMode
  completed?: boolean
  validation_error?: string
  next_question?: QuestionPayload | null
  user_message_id?: number
}

export interface CollectedData {
  name?: string
  phone_wa?: string
  email?: string
  // Stage I — company passport
  company?: string
  company_website?: string
  industry_field?: string
  city?: string
  employees_count?: string
  company_age?: string
  parent_company?: string
  // Stage II — role
  role?: string
  // legacy
  industry_code?: string
  goals?: string
}

export interface ChatSessionState {
  id: string
  status: string
  collected_data: CollectedData
}

export interface AuthTokens {
  access: string
  refresh: string
  client_profile_id: number
  name: string
}

export interface StartQuestionnaireResponse {
  session_id: string
  intro: string
  mode: ChatMode
  submission_id: string
  next_question: QuestionPayload | null
}

export async function getChatConfig(): Promise<ChatConfig> {
  const { data } = await api.get<ChatConfig>('/chat/config/')
  return data
}

export async function startChat(): Promise<ChatStartResponse> {
  const { data } = await api.post<ChatStartResponse>('/chat/start/', {})
  return data
}

export async function sendMessage(
  sessionId: string,
  content: string | string[],
): Promise<ChatMessageResponse> {
  const { data } = await api.post<ChatMessageResponse>('/chat/message/', {
    session_id: sessionId,
    content: Array.isArray(content) ? content.join(', ') : content,
  })
  return data
}

export async function collectProfile(
  sessionId: string,
  payload: CollectedData,
): Promise<ChatSessionState> {
  const { data } = await api.post<ChatSessionState>('/chat/collect/', {
    session_id: sessionId,
    ...payload,
  })
  return data
}

export async function exchangeForTokens(sessionId: string): Promise<AuthTokens> {
  const { data } = await api.post<AuthTokens>('/chat/auth-token/', {
    session_id: sessionId,
  })
  return data
}

export async function startQuestionnaire(
  sessionId: string,
  submissionId: string,
): Promise<StartQuestionnaireResponse> {
  const { data } = await api.post<StartQuestionnaireResponse>('/chat/start-questionnaire/', {
    session_id: sessionId,
    submission_id: submissionId,
  })
  return data
}

export interface RequestEmailCodeResponse {
  sent?: boolean
  email?: string
  ttl_minutes?: number
  already_verified?: boolean
  detail?: string
}

export async function requestEmailCode(sessionId: string): Promise<RequestEmailCodeResponse> {
  const { data } = await api.post<RequestEmailCodeResponse>('/chat/request-email-code/', {
    session_id: sessionId,
  })
  return data
}

export interface VerifyEmailCodeResponse {
  verified: boolean
  access?: string
  refresh?: string
  client_profile_id?: number
  name?: string
  detail?: string
}

export async function verifyEmailCode(
  sessionId: string,
  code: string,
): Promise<VerifyEmailCodeResponse> {
  const { data } = await api.post<VerifyEmailCodeResponse>('/chat/verify-email-code/', {
    session_id: sessionId,
    code,
  })
  return data
}
