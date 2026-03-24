import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface TransactionRow {
  id: string
  date: string
  amount: number
  payee_name: string | null
  memo: string | null
  category_id: string | null
  category_name: string | null
  group_name: string | null
  account_name: string | null
}

export interface TransactionSearchResult {
  transactions: TransactionRow[]
  total_count: number
  total_amount: number
  page: number
  page_size: number
  total_pages: number
}

export interface TransactionFilters {
  payee?: string
  category_id?: string
  date_from?: string
  date_to?: string
  amount_min?: number
  amount_max?: number
  sort_by?: string
  sort_dir?: string
  page?: number
  page_size?: number
}

export interface CategoryBreakdownItem {
  category_id: string | null
  category_name: string
  count: number
  amount: number
}

export interface PayeeSummary {
  payee: string
  transaction_count: number
  total_amount: number
  first_date: string | null
  last_date: string | null
  category_breakdown: CategoryBreakdownItem[]
  has_mixed_categories?: boolean
  likely_recurring: boolean
}

function buildQueryString(filters: TransactionFilters): string {
  const params = new URLSearchParams()
  if (filters.payee) params.set('payee', filters.payee)
  if (filters.category_id) params.set('category_id', filters.category_id)
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  if (filters.amount_min != null) params.set('amount_min', String(filters.amount_min))
  if (filters.amount_max != null) params.set('amount_max', String(filters.amount_max))
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_dir) params.set('sort_dir', filters.sort_dir)
  if (filters.page) params.set('page', String(filters.page))
  if (filters.page_size) params.set('page_size', String(filters.page_size))
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function useTransactionSearch(filters: TransactionFilters) {
  return useQuery<TransactionSearchResult>({
    queryKey: ['dragon-keeper', 'transactions', filters],
    queryFn: () => apiFetch(`/dragon-keeper/transactions${buildQueryString(filters)}`),
    placeholderData: (prev) => prev,
  })
}

export function usePayeeSummary(payee: string | undefined) {
  return useQuery<PayeeSummary>({
    queryKey: ['dragon-keeper', 'payee-summary', payee],
    queryFn: () => apiFetch(`/dragon-keeper/transactions/payee-summary?payee=${encodeURIComponent(payee!)}`),
    enabled: !!payee && payee.length >= 2,
  })
}

export function useBulkRecategorize() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { transaction_ids: string[]; category_id: string }) =>
      apiFetch('/dragon-keeper/transactions/bulk-recategorize', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper'] })
    },
  })
}
