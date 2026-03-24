import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../api'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  tool_calls?: string | null
  created_at: string
}

interface ChatHistoryResponse {
  messages: ChatMessage[]
}

interface SendMessageResponse {
  role: string
  content: string
  tool_calls_made: boolean
}

export function useChatHistory() {
  return useQuery<ChatHistoryResponse>({
    queryKey: ['dragon-keeper', 'chat-history'],
    queryFn: () => apiFetch('/dragon-keeper/chat/history'),
  })
}

export function useSendMessage() {
  const qc = useQueryClient()
  return useMutation<SendMessageResponse, Error, string>({
    mutationFn: (message) =>
      apiFetch('/dragon-keeper/chat', {
        method: 'POST',
        body: JSON.stringify({ message }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'chat-history'] })
    },
  })
}

export function useClearChat() {
  const qc = useQueryClient()
  return useMutation<void, Error, void>({
    mutationFn: () =>
      apiFetch('/dragon-keeper/chat/history', { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dragon-keeper', 'chat-history'] })
    },
  })
}
