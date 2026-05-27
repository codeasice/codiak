import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

interface AccountDetail {
  id: string
  name: string
  balance: number
}

export interface AccountSummaryData {
  checking: {
    total: number
    accounts: AccountDetail[]
  }
  credit_cards: {
    total: number
    accounts: AccountDetail[]
  }
  remaining_period: {
    total: number
    spent: number
    paycheck_amount: number
    period_start: string | null
    period_end: string | null
  }
  has_data: boolean
}

export function useAccountSummary() {
  return useQuery<AccountSummaryData>({
    queryKey: ['dragon-keeper', 'account-summary'],
    queryFn: () => apiFetch('/dragon-keeper/account-summary'),
    refetchInterval: 30_000,
  })
}
