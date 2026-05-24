import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface RecurringItem {
  id: number
  payee_name: string
  type: 'income' | 'expense'
  cadence: 'biweekly' | 'monthly' | 'annual'
  expected_amount: number
  expected_day: number
  next_expected_date: string
  confirmed: boolean
  include_in_sts: boolean
  last_seen_date: string | null
  avg_amount: number | null
  occurrence_count: number
  cancelled_date: string | null
  created_at: string
  updated_at: string
}

export interface CancelledCharge {
  date: string
  amount: number
  id: string
}

export interface CancelledChargeAlert {
  recurring_id: number
  payee_name: string
  cancelled_date: string
  charges: CancelledCharge[]
}

export interface RecurringResponse {
  items: RecurringItem[]
  monthly_income: number
  monthly_expenses: number
  annual_expenses: number
  total_count: number
  unconfirmed_count: number
  cancelled_charges: CancelledChargeAlert[]
}

export interface DetectionResult {
  detected: number
  new: number
  updated: number
  items: any[]
}

const KEY = ['dragon-keeper', 'recurring'] as const

export function useRecurring() {
  return useQuery<RecurringResponse>({
    queryKey: KEY,
    queryFn: () => apiFetch('/dragon-keeper/recurring'),
  })
}

export function useDetectRecurring() {
  const qc = useQueryClient()
  return useMutation<DetectionResult>({
    mutationFn: () => apiFetch('/dragon-keeper/recurring/detect', { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useConfirmRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { id: number; confirmed: boolean }) =>
      apiFetch(`/dragon-keeper/recurring/${data.id}/confirm`, {
        method: 'PATCH',
        body: JSON.stringify({ confirmed: data.confirmed }),
      }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useToggleSts() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { id: number; include_in_sts: boolean }) =>
      apiFetch(`/dragon-keeper/recurring/${data.id}/sts`, {
        method: 'PATCH',
        body: JSON.stringify({ include_in_sts: data.include_in_sts }),
      }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useCancelRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { id: number; cancelled_date: string }) =>
      apiFetch(`/dragon-keeper/recurring/${data.id}/cancel`, {
        method: 'PATCH',
        body: JSON.stringify({ cancelled_date: data.cancelled_date }),
      }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useUncancelRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/dragon-keeper/recurring/${id}/uncancel`, { method: 'PATCH' }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useDismissRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/dragon-keeper/recurring/${id}`, { method: 'DELETE' }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}
