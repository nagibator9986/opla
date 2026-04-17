import axios from 'axios'
import type { DeeplinkResponse } from '../types/api'

const baseURL = import.meta.env.VITE_API_URL ?? '/api/v1'

export async function exchangeDeeplink(uuid: string): Promise<DeeplinkResponse> {
  const { data } = await axios.post<DeeplinkResponse>(`${baseURL}/bot/deeplink/exchange/`, { token: uuid })
  return data
}
