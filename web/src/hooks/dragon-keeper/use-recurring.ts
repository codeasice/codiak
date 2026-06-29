import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface ChargeHistoryPoint {
  date: string
  amount: number
}

export interface RecurringItem {
  id: number
  payee_name: string
  type: 'income' | 'expense'
  cadence: 'biweekly' | 'monthly' | 'semi_monthly' | 'annual'
  expected_amount: number
  expected_day: number
  expected_day_2: number | null
  next_expected_date: string
  confirmed: boolean
  include_in_sts: boolean
  last_seen_date: string | null
  avg_amount: number | null
  occurrence_count: number
  cancelled_date: string | null
  is_subscription: boolean
  status: 'active' | 'cancelled' | 'archived'
  charge_history: ChargeHistoryPoint[]
  linked_payees?: string[]
  all_payee_names?: string[]
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

export function useToggleSubscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { id: number; is_subscription: boolean }) =>
      apiFetch(`/dragon-keeper/recurring/${data.id}/subscription`, {
        method: 'PATCH',
        body: JSON.stringify({ is_subscription: data.is_subscription }),
      }),
    onSettled: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useArchiveRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/dragon-keeper/recurring/${id}/archive`, { method: 'PATCH' }),
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

export interface LinkWarning {
  code: string
  message: string
  severity: 'error' | 'warning' | 'info'
}

export interface LinkPreview {
  canonical: Pick<RecurringItem, 'id' | 'payee_name' | 'type' | 'cadence' | 'expected_amount' | 'confirmed' | 'is_subscription' | 'status' | 'include_in_sts'>
  source: {
    id: number | null
    payee_name: string
    type: RecurringItem['type']
    cadence: RecurringItem['cadence']
    expected_amount: number
    confirmed: boolean
    is_subscription: boolean
    status: RecurringItem['status']
    include_in_sts: boolean
  }
  warnings: LinkWarning[]
  blocking: boolean
  combined_charge_history: ChargeHistoryPoint[]
  combined_occurrence_count: number
  combined_last_seen: string | null
  link_mode?: 'payee_name' | 'recurring_item'
}

export function useLinkPreview(
  itemId: number | null,
  sourceId: number | null,
  canonicalId: number | null,
  enabled: boolean,
) {
  return useQuery<LinkPreview>({
    queryKey: [...KEY, 'link-preview', itemId, 'item', sourceId, canonicalId],
    queryFn: () => {
      const params = new URLSearchParams({
        source_recurring_id: String(sourceId),
        canonical_recurring_id: String(canonicalId),
      })
      return apiFetch(`/dragon-keeper/recurring/${itemId}/link/preview?${params}`)
    },
    enabled: enabled && itemId != null && sourceId != null && canonicalId != null,
  })
}

export function useLinkPreviewByPayeeName(
  itemId: number | null,
  payeeName: string,
  enabled: boolean,
) {
  return useQuery<LinkPreview>({
    queryKey: [...KEY, 'link-preview', itemId, 'payee', payeeName],
    queryFn: () => {
      const params = new URLSearchParams({ payee_name: payeeName })
      return apiFetch(`/dragon-keeper/recurring/${itemId}/link/preview?${params}`)
    },
    enabled: enabled && itemId != null && payeeName.trim().length > 0,
  })
}

export function useLinkRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      itemId: number
      source_recurring_id?: number
      payee_name?: string
      canonical_recurring_id?: number
      force_amount?: boolean
    }) =>
      apiFetch(`/dragon-keeper/recurring/${data.itemId}/link`, {
        method: 'POST',
        body: JSON.stringify({
          source_recurring_id: data.source_recurring_id,
          payee_name: data.payee_name,
          canonical_recurring_id: data.canonical_recurring_id,
          force_amount: data.force_amount ?? false,
        }),
      }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'recurring', 'duplicate-suggestions'] })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useUnlinkRecurringPayee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { itemId: number; payee_name: string }) =>
      apiFetch(
        `/dragon-keeper/recurring/${data.itemId}/link/${encodeURIComponent(data.payee_name)}`,
        { method: 'DELETE' },
      ),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'recurring', 'duplicate-suggestions'] })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}
