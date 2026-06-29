import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface BalancePoint {
  snapshot_date: string
  checking_total: number
  credit_total: number
  savings_total: number
  net_worth: number
}

export interface BalanceHistoryData {
  points: BalancePoint[]
  count: number
}

export interface CategoryTimelinePoint {
  month: string
  total: number
  txn_count: number
}

export interface CategoryTimelineData {
  category_id: string
  category_name: string
  points: CategoryTimelinePoint[]
}

export interface SankeyNode {
  id: string
  name: string
  column: number
  total: number
}

export interface SankeyLink {
  source: number
  target: number
  value: number
}

export interface SpendingFlowData {
  month: string
  total_spending: number
  transaction_count: number
  nodes: SankeyNode[]
  links: SankeyLink[]
  available_months: string[]
}

export function useBalanceHistory(days: number = 90) {
  return useQuery<BalanceHistoryData>({
    queryKey: ['dragon-keeper', 'charts', 'balance-history', days],
    queryFn: () => apiFetch(`/dragon-keeper/charts/balance-history?days=${days}`),
    staleTime: 5 * 60 * 1000,
  })
}

export function useCategoryTimeline(categoryId: string, periods: number = 12) {
  return useQuery<CategoryTimelineData>({
    queryKey: ['dragon-keeper', 'charts', 'category-timeline', categoryId, periods],
    queryFn: () => apiFetch(`/dragon-keeper/charts/category-timeline/${categoryId}?periods=${periods}`),
    enabled: !!categoryId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useSpendingFlow(month?: string, minAmount: number = 10, maxPayees: number = 30, accountId?: string) {
  const params = new URLSearchParams()
  if (month) params.set('month', month)
  params.set('min_amount', String(minAmount))
  params.set('max_payees', String(maxPayees))
  if (accountId) params.set('account_id', accountId)

  return useQuery<SpendingFlowData>({
    queryKey: ['dragon-keeper', 'charts', 'spending-flow', month, minAmount, maxPayees, accountId],
    queryFn: () => apiFetch(`/dragon-keeper/charts/spending-flow?${params}`),
    staleTime: 5 * 60 * 1000,
  })
}
