import { useMutation, useQueryClient } from '@tanstack/react-query'

interface SyncResponse {
  status: string
  sync_type: string
  budget_id: string
  accounts_synced: number
  categories_synced: number
  category_groups_synced: number
  payees_synced: number
  transactions_synced: number
  server_knowledge: number
  synced_at: string
}

interface SyncError {
  error: string
  code: string
  detail: string
}

export function useSync() {
  const queryClient = useQueryClient()

  return useMutation<SyncResponse, Error>({
    mutationFn: async () => {
      const res = await fetch('http://localhost:8000/api/dragon-keeper/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (!res.ok) {
        const err: SyncError = await res.json().catch(() => ({
          error: 'sync_failed', code: 'UNKNOWN', detail: res.statusText,
        }))
        throw new Error(err.detail)
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dragon-keeper'] })
    },
  })
}
