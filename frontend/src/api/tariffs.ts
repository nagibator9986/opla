import api from './axios'
import type { Tariff } from '../types/api'

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// DRF pagination is enabled project-wide, so the raw list endpoint returns
// `{ count, next, previous, results }`. If pagination is ever disabled, the
// response becomes a bare array — handle both so the UI doesn't break.
export async function getTariffs(): Promise<Tariff[]> {
  const { data } = await api.get<Tariff[] | Paginated<Tariff>>('/payments/tariffs/')
  return Array.isArray(data) ? data : data.results
}
