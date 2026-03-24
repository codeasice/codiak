import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface DkSettings {
  projection_days: number
  buffer_amount: number
  ynab_budget_id: string
}

const KEY = ['dragon-keeper', 'settings'] as const

export function useDkSettings() {
  return useQuery<DkSettings>({
    queryKey: KEY,
    queryFn: () => apiFetch('/dragon-keeper/settings'),
    staleTime: 5 * 60 * 1000,
  })
}

export function useUpdateDkSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { projection_days?: number; buffer_amount?: number }) =>
      apiFetch('/dragon-keeper/settings', {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}
