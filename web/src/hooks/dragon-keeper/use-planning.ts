import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'
import type { SavingsPeriod } from './use-savings-opportunities'

export type PlanningType = 'purchase' | 'savings' | 'selling'

export interface PlanningItem {
  type: PlanningType
  filename: string
  filepath: string
  title: string
  status: string
  order: number | null
  added: string
  category: string
  direction: 'in' | 'out'
  impact: number | null
  true_impact: number | null
  impact_detail: string | null
  url: string | null
  cost?: number | null
  purchase_date?: string | null
  savings?: number | null
  period?: SavingsPeriod
  completed_date?: string | null
  actual_savings?: number | null
  current_value?: number | null
  sold_date?: string | null
  brand?: string
  model?: string
}

export interface PlanningSummary {
  true_cost_out: number
  true_savings_in: number
  sale_proceeds: number
  true_sale_proceeds: number
  net_true_impact: number
}

export interface PlanningData {
  items: PlanningItem[]
  summary: PlanningSummary
  max_cc_rate: number | null
  counts: { purchase: number; savings: number; selling: number }
}

function enc(filename: string) {
  return encodeURIComponent(filename)
}

function invalidatePlanning(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['planning'] })
  qc.invalidateQueries({ queryKey: ['purchases'] })
  qc.invalidateQueries({ queryKey: ['savings-opportunities'] })
}

export function usePlanning() {
  return useQuery<PlanningData>({
    queryKey: ['planning'],
    queryFn: () => apiFetch<PlanningData>('/dragon-keeper/planning'),
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  })
}

export function usePlanningUpdateCost() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, cost }: { filename: string; cost: number }) =>
      apiFetch('/dragon-keeper/purchases/' + enc(filename) + '/cost', {
        method: 'PATCH',
        body: JSON.stringify({ cost }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdatePurchaseDate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, date }: { filename: string; date: string | null }) =>
      apiFetch('/dragon-keeper/purchases/' + enc(filename) + '/purchase-date', {
        method: 'PATCH',
        body: JSON.stringify({ date }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningMovePurchase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, direction }: { filename: string; direction: 'up' | 'down' }) =>
      apiFetch('/dragon-keeper/purchases/' + enc(filename) + '/move', {
        method: 'POST',
        body: JSON.stringify({ direction }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdateSavings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, savings }: { filename: string; savings: number }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/savings', {
        method: 'PATCH',
        body: JSON.stringify({ savings }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdatePeriod() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, period }: { filename: string; period: SavingsPeriod }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/period', {
        method: 'PATCH',
        body: JSON.stringify({ period }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdateCompletedDate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, date }: { filename: string; date: string | null }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/completed-date', {
        method: 'PATCH',
        body: JSON.stringify({ date }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningMarkAsDone() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (filename: string) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/mark-done', {
        method: 'POST',
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdateActualSavings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, actual_savings }: { filename: string; actual_savings: number }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/actual-savings', {
        method: 'PATCH',
        body: JSON.stringify({ actual_savings }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningMoveSavings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, direction }: { filename: string; direction: 'up' | 'down' }) =>
      apiFetch('/dragon-keeper/savings-opportunities/' + enc(filename) + '/move', {
        method: 'POST',
        body: JSON.stringify({ direction }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdateCurrentValue() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, current_value }: { filename: string; current_value: number }) =>
      apiFetch('/dragon-keeper/selling/' + enc(filename) + '/current-value', {
        method: 'PATCH',
        body: JSON.stringify({ current_value }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningUpdateSoldDate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, date }: { filename: string; date: string | null }) =>
      apiFetch('/dragon-keeper/selling/' + enc(filename) + '/sold-date', {
        method: 'PATCH',
        body: JSON.stringify({ date }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}

export function usePlanningMoveSelling() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, direction }: { filename: string; direction: 'up' | 'down' }) =>
      apiFetch('/dragon-keeper/selling/' + enc(filename) + '/move', {
        method: 'POST',
        body: JSON.stringify({ direction }),
      }),
    onSuccess: () => invalidatePlanning(qc),
  })
}
