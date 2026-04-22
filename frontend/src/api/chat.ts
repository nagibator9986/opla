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

export interface ChatStartResponse {
  session_id: string
  greeting: string
  quick_replies: QuickReply[]
}

export interface AssistantReply {
  id: number
  role: 'assistant'
  content: string
  created_at: string
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
  status: 'active' | 'qualified' | 'paid' | 'abandoned'
  collected_data: CollectedData
}

export interface AuthTokens {
  access: string
  refresh: string
  client_profile_id: number
  name: string
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
  content: string,
): Promise<{ reply: AssistantReply }> {
  const { data } = await api.post<{ reply: AssistantReply }>('/chat/message/', {
    session_id: sessionId,
    content,
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
