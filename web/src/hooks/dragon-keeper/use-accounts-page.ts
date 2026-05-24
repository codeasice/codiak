import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface MonthlyActivity {
  month: string
  debits: number
  credits: number
}

export interface Account {
  id: string
  name: string
  type: string
  balance: number
  cleared_balance: number
  uncleared_balance: number
  on_budget: boolean
  note: string | null
  interest_rate: number | null
  credit_limit: number | null
  monthly_activity: MonthlyActivity[]
}

export interface AccountsPageData {
  accounts: Account[]
}

export function useAccountsPage() {
  return useQuery<AccountsPageData>({
    queryKey: ['dragon-keeper', 'accounts-page'],
    queryFn: () => apiFetch('/dragon-keeper/accounts-page'),
    staleTime: 2 * 60 * 1000,
  })
}

export function useSetCreditLimit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ accountId, limit }: { accountId: string; limit: number | null }) =>
      apiFetch(`/dragon-keeper/accounts-page/${accountId}/credit-limit`, {
        method: 'PUT',
        body: JSON.stringify({ limit }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dragon-keeper', 'accounts-page'] }),
  })
}

export function useSetInterestRate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ accountId, rate }: { accountId: string; rate: number | null }) =>
      apiFetch(`/dragon-keeper/accounts-page/${accountId}/interest-rate`, {
        method: 'PUT',
        body: JSON.stringify({ rate }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dragon-keeper', 'accounts-page'] }),
  })
}
