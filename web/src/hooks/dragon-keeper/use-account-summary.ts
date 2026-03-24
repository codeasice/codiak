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
  pending_bills: {
    total: number
    count: number
    timeframe: string
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
