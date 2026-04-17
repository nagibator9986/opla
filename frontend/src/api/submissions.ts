import api from './axios'
import type { Submission } from '../types/api'

export async function getMySubmission(): Promise<Submission> {
  const { data } = await api.get<Submission>('/submissions/my/')
  return data
}
