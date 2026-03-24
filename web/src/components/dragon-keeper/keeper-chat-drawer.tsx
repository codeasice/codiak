import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from 'react'
import { useChatHistory, useSendMessage, useClearChat, type ChatMessage } from '../../hooks/dragon-keeper/use-keeper-chat'
import { useToast } from './toast'

const DRAWER_WIDTH = 380
const TRANSITION_MS = 280

const WELCOME_MSG = "Hi! I'm your Dragon Keeper. Ask me about your spending, balances, or pending categorizations."

function formatContent(text: string) {
  const parts: (string | JSX.Element)[] = []
  const regex = /\*\*(.+?)\*\*/g
  let last = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    parts.push(<strong key={match.index}>{match[1]}</strong>)
    last = regex.lastIndex
  }
  if (last < text.length) parts.push(text.slice(last))

  return parts.flatMap((part, i) => {
    if (typeof part !== 'string') return [part]
    return part.split('\n').flatMap((line, j, arr) =>
      j < arr.length - 1 ? [line, <br key={`br-${i}-${j}`} />] : [line],
    )
  })
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: '4px', padding: '4px 0' }}>
      {[0, 1, 2].map(i => (
        <span
          key={i}
          style={{
            width: 6, height: 6, borderRadius: '50%',
            background: 'var(--text-muted)',
            animation: `keeper-dot-bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
          }}
        />
      ))}
      <style>{`
        @keyframes keeper-dot-bounce {
          0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
          30% { opacity: 1; transform: translateY(-4px); }
        }
      `}</style>
    </div>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  const isSystem = msg.role === 'system'

  if (isSystem) {
    return (
      <div style={{
        textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)',
        padding: '4px 12px', fontStyle: 'italic',
      }}>
        {formatContent(msg.content)}
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex', gap: '8px',
      flexDirection: isUser ? 'row-reverse' : 'row',
      alignItems: 'flex-start',
      padding: '2px 0',
    }}>
      {!isUser && (
        <div style={{
          width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
          background: 'color-mix(in srgb, var(--accent) 15%, var(--bg-card))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '14px', lineHeight: 1, marginTop: 2,
        }}>
          🐉
        </div>
      )}
      <div style={{ maxWidth: '80%', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{
          padding: '8px 12px',
          borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
          background: isUser
            ? 'color-mix(in srgb, var(--accent) 18%, var(--bg-card))'
            : 'var(--bg-card)',
          borderLeft: isUser ? 'none' : '3px solid #6366f1',
          color: 'var(--text-primary)',
          fontSize: '13px', lineHeight: 1.5,
          wordBreak: 'break-word',
        }}>
          {formatContent(msg.content)}
        </div>
        {msg.tool_calls && (
          <div style={{
            fontSize: '11px', color: 'var(--text-muted)',
            paddingLeft: isUser ? 0 : 4,
            display: 'flex', alignItems: 'center', gap: '4px',
          }}>
            <span style={{ fontSize: '12px' }}>🔍</span>
            Looked up financial data
          </div>
        )}
      </div>
    </div>
  )
}

export default function KeeperChatDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { toast } = useToast()
  const { data, isLoading, isError, refetch } = useChatHistory()
  const sendMutation = useSendMessage()
  const clearMutation = useClearChat()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [rendered, setRendered] = useState(open)

  useEffect(() => {
    if (open) setRendered(true)
  }, [open])

  const handleTransitionEnd = useCallback(() => {
    if (!open) setRendered(false)
  }, [open])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [data?.messages, sendMutation.isPending])

  useEffect(() => {
    if (open && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), TRANSITION_MS)
    }
  }, [open])

  const autoResize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }, [])

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || sendMutation.isPending) return

    sendMutation.mutate(trimmed, {
      onSuccess: () => setInput(''),
      onError: (err) => toast(err.message || 'Failed to send message', 'error'),
    })
  }, [input, sendMutation, toast])

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleClear = useCallback(() => {
    clearMutation.mutate(undefined, {
      onSuccess: () => toast('Chat cleared', 'info'),
      onError: (err) => toast(err.message || 'Failed to clear chat', 'error'),
    })
  }, [clearMutation, toast])

  const messages = data?.messages ?? []
  const showWelcome = !isLoading && !isError && messages.length === 0

  if (!rendered && !open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 99,
          background: 'rgba(0,0,0,0.4)',
          opacity: open ? 1 : 0,
          transition: `opacity ${TRANSITION_MS}ms ease`,
          pointerEvents: open ? 'auto' : 'none',
        }}
      />

      {/* Drawer */}
      <div
        onTransitionEnd={handleTransitionEnd}
        style={{
          position: 'fixed', top: 0, right: 0, bottom: 0,
          width: DRAWER_WIDTH, zIndex: 100,
          background: 'var(--bg-secondary)',
          borderLeft: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column',
          transform: open ? 'translateX(0)' : `translateX(${DRAWER_WIDTH}px)`,
          transition: `transform ${TRANSITION_MS}ms cubic-bezier(0.4,0,0.2,1)`,
        }}
      >
        {/* Header */}
        <div style={{
          padding: '16px', display: 'flex', alignItems: 'center', gap: '10px',
          borderBottom: '1px solid var(--border)', flexShrink: 0,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
            background: 'color-mix(in srgb, var(--accent) 15%, var(--bg-card))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '20px', lineHeight: 1,
          }}>
            🐉
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
              Dragon Keeper
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Financial Assistant
            </div>
          </div>
          <button
            onClick={handleClear}
            disabled={clearMutation.isPending || messages.length === 0}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '11px', padding: '4px 8px',
              borderRadius: 'var(--radius)', whiteSpace: 'nowrap',
              opacity: messages.length === 0 ? 0.4 : 1,
            }}
            onMouseEnter={e => { if (messages.length > 0) e.currentTarget.style.color = 'var(--text-primary)' }}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            Clear chat
          </button>
          <button
            onClick={onClose}
            aria-label="Close chat"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '18px', lineHeight: 1,
              padding: '4px', borderRadius: 'var(--radius)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-primary)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            ✕
          </button>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '12px 14px',
          display: 'flex', flexDirection: 'column', gap: '10px',
        }}>
          {isError && (
            <div style={{
              textAlign: 'center', padding: '24px 12px',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
            }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Unable to load chat history
              </span>
              <button
                onClick={() => refetch()}
                style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', padding: '6px 14px',
                  borderRadius: 'var(--radius)', cursor: 'pointer', fontSize: '12px',
                }}
              >
                Retry
              </button>
            </div>
          )}

          {showWelcome && (
            <div style={{
              display: 'flex', gap: '8px', alignItems: 'flex-start',
              padding: '2px 0',
            }}>
              <div style={{
                width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                background: 'color-mix(in srgb, var(--accent) 15%, var(--bg-card))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '14px', lineHeight: 1, marginTop: 2,
              }}>
                🐉
              </div>
              <div style={{
                padding: '8px 12px', borderRadius: '12px 12px 12px 2px',
                background: 'var(--bg-card)', borderLeft: '3px solid #6366f1',
                color: 'var(--text-primary)', fontSize: '13px', lineHeight: 1.5,
                maxWidth: '80%',
              }}>
                {WELCOME_MSG}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}

          {sendMutation.isPending && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', padding: '2px 0' }}>
              <div style={{
                width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                background: 'color-mix(in srgb, var(--accent) 15%, var(--bg-card))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '14px', lineHeight: 1, marginTop: 2,
              }}>
                🐉
              </div>
              <div style={{
                padding: '8px 12px', borderRadius: '12px 12px 12px 2px',
                background: 'var(--bg-card)', borderLeft: '3px solid #6366f1',
              }}>
                <TypingIndicator />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '12px 14px', borderTop: '1px solid var(--border)',
          display: 'flex', gap: '8px', alignItems: 'flex-end', flexShrink: 0,
        }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKeyDown}
            placeholder="Ask the Keeper..."
            disabled={sendMutation.isPending}
            rows={1}
            style={{
              flex: 1, resize: 'none', padding: '8px 12px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
              fontSize: '13px', lineHeight: 1.5, fontFamily: 'inherit',
              outline: 'none', minHeight: '36px', maxHeight: '120px',
            }}
            onFocus={e => (e.currentTarget.style.borderColor = 'var(--accent)')}
            onBlur={e => (e.currentTarget.style.borderColor = 'var(--border)')}
          />
          <button
            onClick={handleSend}
            disabled={sendMutation.isPending || !input.trim()}
            aria-label="Send message"
            style={{
              background: input.trim() ? 'var(--accent)' : 'var(--bg-hover)',
              border: 'none', borderRadius: 'var(--radius)',
              color: input.trim() ? '#fff' : 'var(--text-muted)',
              width: 36, height: 36, flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: input.trim() ? 'pointer' : 'default',
              fontSize: '16px', lineHeight: 1,
              transition: 'background 150ms ease, color 150ms ease',
            }}
          >
            ↑
          </button>
        </div>
      </div>
    </>
  )
}
