import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface Rule {
  id: number
  payee_pattern: string
  match_type: string
  category_id: string
  min_amount: number | null
  max_amount: number | null
  confidence: number
  source: string
  times_applied: number
  created_at: string
  updated_at: string
  category_name: string | null
  group_name: string | null
}

interface RulesResponse {
  rules: Rule[]
}

interface RulePayload {
  payee_pattern: string
  match_type: string
  category_id: string
  min_amount?: number | null
  max_amount?: number | null
}

interface RestorePayload {
  payee_pattern: string
  match_type: string
  category_id: string
  min_amount?: number | null
  max_amount?: number | null
  confidence: number
  source: string
  times_applied: number
}

const RULES_KEY = ['dragon-keeper', 'rules'] as const

export function useRules() {
  return useQuery<RulesResponse>({
    queryKey: RULES_KEY,
    queryFn: () => apiFetch('/dragon-keeper/rules'),
    refetchOnWindowFocus: true,
  })
}

export function useCreateRule() {
  const qc = useQueryClient()
  return useMutation<Rule, Error, RulePayload>({
    mutationFn: (data) =>
      apiFetch('/dragon-keeper/rules', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: RULES_KEY })
    },
  })
}

export function useUpdateRule() {
  const qc = useQueryClient()
  return useMutation<Rule, Error, RulePayload & { rule_id: number }>({
    mutationFn: ({ rule_id, ...data }) =>
      apiFetch(`/dragon-keeper/rules/${rule_id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: RULES_KEY })
    },
  })
}

export function useDeleteRule() {
  const qc = useQueryClient()
  return useMutation<Rule, Error, number>({
    mutationFn: (rule_id) =>
      apiFetch(`/dragon-keeper/rules/${rule_id}`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: RULES_KEY })
    },
  })
}

export function useRestoreRule() {
  const qc = useQueryClient()
  return useMutation<Rule, Error, RestorePayload>({
    mutationFn: (data) =>
      apiFetch('/dragon-keeper/rules/restore', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: RULES_KEY })
    },
  })
}
