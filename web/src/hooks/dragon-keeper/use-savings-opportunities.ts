import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export type SavingsPeriod = 'one-time' | 'monthly' | 'yearly'

export interface SavingsOpportunity {
  filename: string
  filepath: string
  action: string
  savings: number | null
  period: SavingsPeriod
  order: number | null
  priority: string
  category: string
  status: string
  added: string
  completed_date: string | null
  actual_savings: number | null
  url: string | null
  notes: string | null
  annual_savings: number | null
  true_savings_1yr: number | null
}

export interface SavingsOpportunitiesData {
  opportunities: SavingsOpportunity[]
  total_annual_savings: number
  total_true_savings_1yr: number
  total_realized_savings: number
  realized_by_year: Record<string, number>
  max_cc_rate: number | null
}

function enc(filename: string) {
  return encodeURIComponent(filename)
}

export function useSavingsOpportunities() {
  return useQuery<SavingsOpportunitiesData>({
    queryKey: ['savings-opportunities'],
    queryFn: () => apiFetch<SavingsOpportunitiesData>('/dragon-keeper/savings-opportunities'),
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  })
}

export function useUpdateSavings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, savings }: { filename: string; savings: number }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/savings', {
        method: 'PATCH',
        body: JSON.stringify({ savings }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['savings-opportunities'] }),
  })
}

export function useUpdatePeriod() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, period }: { filename: string; period: SavingsPeriod }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/period', {
        method: 'PATCH',
        body: JSON.stringify({ period }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['savings-opportunities'] }),
  })
}

export function useUpdateCompletedDate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, date }: { filename: string; date: string | null }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/completed-date', {
        method: 'PATCH',
        body: JSON.stringify({ date }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['savings-opportunities'] }),
  })
}

export function useMarkAsDone() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (filename: string) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/mark-done', {
        method: 'POST',
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['savings-opportunities'] })
      qc.invalidateQueries({ queryKey: ['planning'] })
    },
  })
}

export function useUpdateActualSavings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, actual_savings }: { filename: string; actual_savings: number }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/actual-savings', {
        method: 'PATCH',
        body: JSON.stringify({ actual_savings }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['savings-opportunities'] }),
  })
}

export function useMoveSavingsOpportunity() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, direction }: { filename: string; direction: 'up' | 'down' }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/move', {
        method: 'POST',
        body: JSON.stringify({ direction }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['savings-opportunities'] }),
  })
}
