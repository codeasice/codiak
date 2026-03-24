import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface PeriodValue {
  period_start: string
  total: number
}

export interface SpendingTrendItem {
  category_id: string
  category_name: string
  group_name: string
  periods: PeriodValue[]
  grand_total: number
  delta_pct: number
}

export function useSpendingTrends() {
  return useQuery<SpendingTrendItem[]>({
    queryKey: ['dragon-keeper', 'spending-trends'],
    queryFn: () => apiFetch('/dragon-keeper/spending-trends'),
    refetchInterval: 60_000,
  })
}
