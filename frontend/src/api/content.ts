import api from './axios'
import type { ContentBlocks } from '../types/api'

export async function getContentBlocks(): Promise<ContentBlocks> {
  const { data } = await api.get<ContentBlocks>('/content/')
  return data
}
