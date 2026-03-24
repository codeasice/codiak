import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface UpcomingItem {
  id: number
  payee_name: string
  type: 'income' | 'expense'
  cadence: 'biweekly' | 'monthly' | 'annual'
  expected_amount: number
  next_expected_date: string
  confirmed: boolean
}

export interface SafeToSpendData {
  starting_balance: number
  pending_outflows: number
  projection_days: number
  buffer_amount: number
  upcoming_income: number
  upcoming_expenses: number
  min_projected_balance: number
  min_balance_date: string
  safe_to_spend: number
  status: 'healthy' | 'caution' | 'critical'
  upcoming_items: UpcomingItem[]
  has_data: boolean
  /* Legacy compat fields (mapped in hero) */
  amount?: number
}

export function useSafeToSpend() {
  return useQuery<SafeToSpendData>({
    queryKey: ['dragon-keeper', 'safe-to-spend'],
    queryFn: () => apiFetch('/dragon-keeper/safe-to-spend'),
    refetchInterval: 30_000,
  })
}
