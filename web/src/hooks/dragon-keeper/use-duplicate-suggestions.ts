import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface DuplicateSuggestion {
  item_a_id: number
  item_b_id: number
  payee_a: string
  payee_b: string
  cadence: string
  amount_a: number
  amount_b: number
  amount_diff_pct: number
  name_similarity: number
}

const KEY = ['dragon-keeper', 'recurring', 'duplicate-suggestions'] as const

export function useDuplicateSuggestions(enabled = true) {
  return useQuery<{ suggestions: DuplicateSuggestion[] }>({
    queryKey: KEY,
    queryFn: () => apiFetch('/dragon-keeper/recurring/duplicate-suggestions'),
    enabled,
  })
}
