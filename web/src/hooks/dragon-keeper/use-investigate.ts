import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '../../api'

interface InvestigateRequest {
  payee_name: string
  amount?: number | null
  memo?: string | null
}

interface InvestigateResponse {
  payee: string
  summary: string
  sources: string[]
  error?: string
}

export function useInvestigate() {
  return useMutation<InvestigateResponse, Error, InvestigateRequest>({
    mutationFn: (req) =>
      apiFetch('/dragon-keeper/investigate', {
        method: 'POST',
        body: JSON.stringify(req),
      }),
  })
}
