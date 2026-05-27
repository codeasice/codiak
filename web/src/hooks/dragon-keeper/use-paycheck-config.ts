import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface DeductionItem {
  id?: number
  category: string
  name: string
  amount: number
  sort_order: number
}

export interface PaycheckConfig {
  id: number
  gross_amount: number
  take_home_amount: number
  effective_date: string
  notes: string | null
  deductions: {
    taxes: DeductionItem[]
    benefits: DeductionItem[]
    retirement: DeductionItem[]
    other: DeductionItem[]
  }
}

export interface PaycheckConfigInput {
  gross_amount: number
  take_home_amount: number
  effective_date: string
  notes?: string | null
  deduction_items: Omit<DeductionItem, 'id'>[]
}

export function usePaycheckConfig() {
  return useQuery<PaycheckConfig>({
    queryKey: ['dragon-keeper', 'paycheck-config'],
    queryFn: () => apiFetch('/dragon-keeper/paycheck-tracer/config'),
    staleTime: 5 * 60 * 1000,
  })
}

export function useUpdatePaycheckConfig() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PaycheckConfigInput) =>
      apiFetch('/dragon-keeper/paycheck-tracer/config', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'paycheck-config'] })
    },
  })
}
