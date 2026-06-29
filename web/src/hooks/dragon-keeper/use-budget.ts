import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface BudgetPeriod {
  period_start: string
  total: number
}

export interface BudgetCategory {
  category_id: string
  category_name: string
  group_name: string
  periods: BudgetPeriod[]
  grand_total: number
  weekly_avg: number
  active_weeks: number
  delta_pct: number
  has_activity: boolean
  cancelled_subscriptions: string[]
  budget_target: number | null
}

export interface BudgetData {
  categories: BudgetCategory[]
  per_period_income: number
}

const KEY = ['dragon-keeper', 'budget'] as const

export function useBudget() {
  return useQuery<BudgetData>({
    queryKey: KEY,
    queryFn: () => apiFetch('/dragon-keeper/budget'),
    refetchInterval: 60_000,
  })
}

export function useUpdateBudgetTarget() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ category_id, amount }: { category_id: string; amount: number | null }) =>
      apiFetch('/dragon-keeper/budget/target', {
        method: 'PATCH',
        body: JSON.stringify({ category_id, amount }),
      }),
    onMutate: async ({ category_id, amount }) => {
      await qc.cancelQueries({ queryKey: KEY })
      const prev = qc.getQueryData<BudgetData>(KEY)
      if (prev) {
        qc.setQueryData<BudgetData>(KEY, {
          ...prev,
          categories: prev.categories.map(c =>
            c.category_id === category_id ? { ...c, budget_target: amount } : c
          ),
        })
      }
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useUpdateBudgetIncome() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (amount: number) =>
      apiFetch('/dragon-keeper/budget/income', {
        method: 'PATCH',
        body: JSON.stringify({ amount }),
      }),
    onMutate: async (amount) => {
      await qc.cancelQueries({ queryKey: KEY })
      const prev = qc.getQueryData<BudgetData>(KEY)
      if (prev) qc.setQueryData<BudgetData>(KEY, { ...prev, per_period_income: amount })
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}
