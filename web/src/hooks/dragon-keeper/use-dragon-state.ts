import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface DragonStateComponent {
  name: string
  status: 'healthy' | 'attention' | 'critical'
  detail: string
}

export interface DragonStateData {
  state: 'sleeping' | 'stirring' | 'raging'
  color: string
  label: string
  components: DragonStateComponent[]
}

export interface GreetingData {
  greeting: string
  streak: number
  days_away: number | null
  pending_count: number
  safe_to_spend: number
}

export function useDragonState() {
  return useQuery<DragonStateData>({
    queryKey: ['dragon-keeper', 'dragon-state'],
    queryFn: () => apiFetch('/dragon-keeper/dragon-state'),
    refetchInterval: 30_000,
  })
}

export function useGreeting() {
  return useQuery<GreetingData>({
    queryKey: ['dragon-keeper', 'greeting'],
    queryFn: () => apiFetch('/dragon-keeper/greeting'),
    refetchInterval: 60_000,
  })
}
