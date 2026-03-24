import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

interface SyncAccountHealth {
  account_id: string
  account_name: string
  status: 'ok' | 'warning' | 'error' | 'never'
  last_sync_at: string | null
  last_error: string | null
  transactions_synced: number
}

export interface SyncHealthData {
  accounts: SyncAccountHealth[]
  has_warning_or_error: boolean
  has_data: boolean
}

export function useSyncHealth() {
  return useQuery<SyncHealthData>({
    queryKey: ['dragon-keeper', 'sync-health'],
    queryFn: () => apiFetch('/dragon-keeper/sync-health'),
    refetchInterval: 60_000,
  })
}
