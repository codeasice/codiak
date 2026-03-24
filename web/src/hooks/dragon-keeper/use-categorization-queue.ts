import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

interface QueueItem {
  id: string
  date: string
  amount: number
  payee_name: string | null
  memo: string | null
  suggested_category_id: string | null
  suggestion_confidence: number | null
  suggestion_source: string | null
  suggested_category_name: string | null
}

interface QueueResponse {
  items: QueueItem[]
  total_count: number
}

interface QueueStats {
  pending_count: number
  approved_count: number
  rule_applied_count: number
  skipped_count: number
  categorized_count: number
  total_count: number
  categorization_percentage: number
  estimated_seconds: number
  llm_available: boolean
  awaiting_llm: number
  llm_batch_size: number
}

interface Category {
  id: string
  name: string
  group_name: string
}

export function useQueue() {
  return useQuery<QueueResponse>({
    queryKey: ['dragon-keeper', 'queue'],
    queryFn: () => apiFetch('/dragon-keeper/queue'),
  })
}

export function useQueueStats() {
  return useQuery<QueueStats>({
    queryKey: ['dragon-keeper', 'queue-stats'],
    queryFn: () => apiFetch('/dragon-keeper/queue-stats'),
    refetchInterval: 10_000,
  })
}

export function useCategories() {
  return useQuery<{ categories: Category[] }>({
    queryKey: ['dragon-keeper', 'categories'],
    queryFn: () => apiFetch('/dragon-keeper/categories'),
    staleTime: 5 * 60 * 1000,
  })
}

interface CategorizeOpts {
  reprocess?: boolean
  llm_limit?: number
}

interface CategorizeResult {
  rules_engine: { matched: number; unmatched: number; total_processed: number }
  llm_categorizer: {
    processed: number
    auto_applied: number
    suggested: number
    eligible: number
    remaining: number
    api_calls: number
    tokens: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
    skipped?: boolean
    skip_reason?: string
  }
}

export function useCategorize() {
  const qc = useQueryClient()
  return useMutation<CategorizeResult, Error, CategorizeOpts | undefined>({
    mutationFn: (opts) => {
      const params = new URLSearchParams()
      if (opts?.reprocess) params.set('reprocess', 'true')
      if (opts?.llm_limit != null) params.set('llm_limit', String(opts.llm_limit))
      const qs = params.toString()
      return apiFetch('/dragon-keeper/categorize' + (qs ? `?${qs}` : ''), {
        method: 'POST',
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper'] })
    },
  })
}

export function useApprove() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { transaction_id: string; category_id: string }) =>
      apiFetch('/dragon-keeper/queue/approve', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onMutate: async (data) => {
      await qc.cancelQueries({ queryKey: ['dragon-keeper', 'queue'] })
      const prev = qc.getQueryData<QueueResponse>(['dragon-keeper', 'queue'])
      if (prev) {
        qc.setQueryData<QueueResponse>(['dragon-keeper', 'queue'], {
          ...prev,
          items: prev.items.filter(i => i.id !== data.transaction_id),
          total_count: prev.total_count - 1,
        })
      }
      return { prev }
    },
    onError: (_err, _data, context) => {
      if (context?.prev) qc.setQueryData(['dragon-keeper', 'queue'], context.prev)
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'queue'] })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'queue-stats'] })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'safe-to-spend'] })
    },
  })
}

export function useApproveAll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      apiFetch('/dragon-keeper/queue/approve-all', { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper'] })
    },
  })
}

export function useSkip() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { transaction_id: string }) =>
      apiFetch('/dragon-keeper/queue/skip', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onMutate: async (data) => {
      await qc.cancelQueries({ queryKey: ['dragon-keeper', 'queue'] })
      const prev = qc.getQueryData<QueueResponse>(['dragon-keeper', 'queue'])
      if (prev) {
        qc.setQueryData<QueueResponse>(['dragon-keeper', 'queue'], {
          ...prev,
          items: prev.items.filter(i => i.id !== data.transaction_id),
          total_count: prev.total_count - 1,
        })
      }
      return { prev }
    },
    onError: (_err, _data, context) => {
      if (context?.prev) qc.setQueryData(['dragon-keeper', 'queue'], context.prev)
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'queue'] })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'queue-stats'] })
    },
  })
}

export function useUnskipAll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      apiFetch('/dragon-keeper/queue/unskip-all', { method: 'POST' }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'queue'] })
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'queue-stats'] })
    },
  })
}

export function useRecategorize() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { transaction_id: string; category_id: string }) =>
      apiFetch('/dragon-keeper/recategorize', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper'] })
    },
  })
}
