import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface SpendingPeriod {
  period_start: string
  total: number
  txn_count: number
}

export interface CategoryTransaction {
  id: string
  date: string
  amount: number
  payee_name: string | null
  memo: string | null
  account_id: string
  account_name: string | null
}

export interface CategoryDetailData {
  category_id: string
  category_name: string
  group_name: string
  spending_over_time: SpendingPeriod[]
  transactions: CategoryTransaction[]
  total_spending: number
  transaction_count: number
}

export function useCategoryDetail(categoryId: string) {
  return useQuery<CategoryDetailData>({
    queryKey: ['dragon-keeper', 'category-detail', categoryId],
    queryFn: () => apiFetch(`/dragon-keeper/category/${categoryId}`),
    enabled: !!categoryId,
  })
}
