import api from './axios'

export interface QuickReply {
  label: string
  payload: string
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
  company?: string
  phone_wa?: string
  city?: string
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
