import api from './axios'
import type { Tariff } from '../types/api'

export async function getTariffs(): Promise<Tariff[]> {
  const { data } = await api.get<Tariff[]>('/payments/tariffs/')
  return data
}
