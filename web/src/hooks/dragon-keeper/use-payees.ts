import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface PayeeMeta {
  id: string
  name: string
  display_name: string | null
  note: string | null
}

const KEY = ['dragon-keeper', 'payees'] as const

export function usePayees() {
  return useQuery<PayeeMeta[]>({
    queryKey: KEY,
    queryFn: () => apiFetch('/dragon-keeper/payees'),
    staleTime: 5 * 60 * 1000,
  })
}

/** Returns a map of payee name (lowercase) → PayeeMeta for fast lookup. */
export function usePayeeMap(): Map<string, PayeeMeta> {
  const { data } = usePayees()
  const map = new Map<string, PayeeMeta>()
  for (const p of data ?? []) {
    map.set(p.name.toLowerCase(), p)
  }
  return map
}

export function useUpdatePayee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, display_name, note }: { id: string; display_name: string | null; note: string | null }) =>
      apiFetch(`/dragon-keeper/payees/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ display_name, note }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}
