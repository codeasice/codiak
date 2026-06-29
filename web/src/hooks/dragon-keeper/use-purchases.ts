import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface Purchase {
  filename: string
  filepath: string
  item: string
  cost: number | null
  order: number | null
  priority: string
  category: string
  status: string
  added: string
  purchase_date: string | null
  url: string | null
  notes: string | null
  true_cost_1yr: number | null
}

export interface PurchasesData {
  purchases: Purchase[]
  max_cc_rate: number | null
}

export function usePurchases() {
  return useQuery<PurchasesData>({
    queryKey: ['purchases'],
    queryFn: () => apiFetch<PurchasesData>('/dragon-keeper/purchases'),
  })
}

export function useUpdateCost() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, cost }: { filename: string; cost: number }) =>
      apiFetch('/dragon-keeper/purchases/' + filename + '/cost', {
        method: 'PATCH',
        body: JSON.stringify({ cost }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['purchases'] }),
  })
}

export function useUpdatePurchaseDate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, date }: { filename: string; date: string | null }) =>
      apiFetch('/dragon-keeper/purchases/' + filename + '/purchase-date', {
        method: 'PATCH',
        body: JSON.stringify({ date }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['purchases'] }),
  })
}

export function useMovePurchase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, direction }: { filename: string; direction: 'up' | 'down' }) =>
      apiFetch('/dragon-keeper/purchases/' + filename + '/move', {
        method: 'POST',
        body: JSON.stringify({ direction }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['purchases'] }),
  })
}
