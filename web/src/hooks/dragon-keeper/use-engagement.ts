import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface EngagementDay {
  date: string
  visit_count: number
  actions_count: number
}

export interface StreakInfo {
  streak: number
  last_visit: string | null
  days_away: number | null
}

export interface EngagementData {
  history: EngagementDay[]
  streak: StreakInfo
}

interface VisitResponse {
  today: EngagementDay
  streak: StreakInfo
}

export function useEngagement() {
  return useQuery<EngagementData>({
    queryKey: ['dragon-keeper', 'engagement'],
    queryFn: () => apiFetch('/dragon-keeper/engagement'),
    refetchInterval: 60_000,
  })
}

export function useRecordVisit() {
  const queryClient = useQueryClient()

  return useMutation<VisitResponse, Error>({
    mutationFn: () =>
      apiFetch('/dragon-keeper/engagement/visit', { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dragon-keeper', 'engagement'] })
    },
  })
}

export function useRecordAction() {
  const queryClient = useQueryClient()

  return useMutation<{ recorded: number }, Error, number>({
    mutationFn: (count: number) =>
      apiFetch('/dragon-keeper/engagement/action', {
        method: 'POST',
        body: JSON.stringify({ count }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dragon-keeper', 'engagement'] })
    },
  })
}
