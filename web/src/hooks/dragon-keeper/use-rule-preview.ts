import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

interface PreviewSample {
  id: string
  date: string
  amount: number
  payee_name: string | null
  memo: string | null
  category_id: string | null
  category_name: string | null
}

interface PreviewResult {
  count: number
  samples: PreviewSample[]
}

interface PreviewParams {
  payee_pattern: string
  match_type: string
  min_amount?: number
  max_amount?: number
}

interface ReclassifyParams {
  payee_pattern: string
  match_type: string
  category_id: string
  min_amount?: number
  max_amount?: number
}

interface ReclassifyResult {
  reclassified_count: number
}

export function useRulePreview() {
  return useMutation<PreviewResult, Error, PreviewParams>({
    mutationFn: (params) =>
      apiFetch('/dragon-keeper/rules/preview', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
  })
}

export function useReclassify() {
  const qc = useQueryClient()
  return useMutation<ReclassifyResult, Error, ReclassifyParams>({
    mutationFn: (params) =>
      apiFetch('/dragon-keeper/rules/reclassify', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper'] })
    },
  })
}
