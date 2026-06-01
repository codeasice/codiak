import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface CategoryMeta {
  name: string
  total: number
  count: number
}

export interface WeekBucket {
  week_start: string
  [payee: string]: string | number
}

export interface DowBucket {
  week_start: string
  Mon: number
  Tue: number
  Wed: number
  Thu: number
  Fri: number
  Sat: number
  Sun: number
}

export interface PayeeSummaryRow {
  payee_name: string
  transaction_count: number
  avg_amount: number
  total_amount: number
}

export interface CategoryExplorerData {
  category_name: string
  weekly_data: WeekBucket[]
  dow_heatmap: DowBucket[]
  payee_summary: PayeeSummaryRow[]
  all_payees: string[]
}

export function useCategoryList() {
  return useQuery<CategoryMeta[]>({
    queryKey: ['dk', 'category-explorer', 'categories'],
    queryFn: () => apiFetch('/dragon-keeper/category-explorer/categories'),
    staleTime: 5 * 60 * 1000,
  })
}

export function useCategoryExplorer(categoryName: string, weeks: number) {
  return useQuery<CategoryExplorerData>({
    queryKey: ['dk', 'category-explorer', categoryName, weeks],
    queryFn: () => apiFetch(`/dragon-keeper/category-explorer?category_name=${encodeURIComponent(categoryName)}&weeks=${weeks}`),
    enabled: !!categoryName,
    staleTime: 2 * 60 * 1000,
  })
}
