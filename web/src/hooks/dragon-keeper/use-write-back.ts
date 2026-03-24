import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

interface WriteBackStatus {
  pending: number
  in_progress: number
  completed: number
  failed_retryable: number
  failed_permanent: number
}

interface WriteBackResult {
  processed: number
  succeeded: number
  failed: number
  error?: string
}

export function useWriteBackStatus() {
  return useQuery<WriteBackStatus>({
    queryKey: ['dragon-keeper', 'write-back-status'],
    queryFn: () => apiFetch('/dragon-keeper/write-back/status'),
    refetchInterval: 15_000,
  })
}

export function useProcessWriteBack() {
  const qc = useQueryClient()
  return useMutation<WriteBackResult>({
    mutationFn: () => apiFetch('/dragon-keeper/write-back/process', { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'write-back-status'] })
    },
  })
}
