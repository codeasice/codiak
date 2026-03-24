import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface CategorySpend {
  category: string
  amount: number
  transaction_count: number
}

export interface PayPeriod {
  period_start: string
  period_end: string
  paycheck_amount: number
  total_spent: number
  total_saved: number
  save_rate: number
  categories: CategorySpend[]
  is_current: boolean
}

export interface CategoryAverage {
  category: string
  avg_amount: number
  avg_percent: number
  period_count: number
}

export interface IncomeSource {
  id: number
  payee_name: string
  cadence: string
  expected_amount: number
  occurrence_count: number
}

export interface PaycheckTracerData {
  income_source: IncomeSource | null
  periods: PayPeriod[]
  category_averages: CategoryAverage[]
}

export interface IncomeSourcesData {
  sources: IncomeSource[]
}

export function usePaycheckTracer(incomeItemId?: number, periods: number = 6) {
  const params = new URLSearchParams()
  if (incomeItemId) params.set('income_item_id', String(incomeItemId))
  params.set('periods', String(periods))

  return useQuery<PaycheckTracerData>({
    queryKey: ['dragon-keeper', 'paycheck-tracer', incomeItemId, periods],
    queryFn: () => apiFetch(`/dragon-keeper/paycheck-tracer?${params}`),
  })
}

export function useIncomeSources() {
  return useQuery<IncomeSourcesData>({
    queryKey: ['dragon-keeper', 'paycheck-tracer', 'sources'],
    queryFn: () => apiFetch('/dragon-keeper/paycheck-tracer/sources'),
    staleTime: 5 * 60 * 1000,
  })
}
