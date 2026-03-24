import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'

type ToastType = 'success' | 'info' | 'warning' | 'error'

interface Toast {
  id: number
  message: string
  type: ToastType
  exiting?: boolean
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} })

export const useToast = () => useContext(ToastContext)

const COLORS: Record<ToastType, string> = {
  success: 'var(--success)',
  info: 'var(--accent)',
  warning: 'var(--warning)',
  error: 'var(--danger)',
}

const ICONS: Record<ToastType, string> = {
  success: '\u2713',
  info: '\u2139',
  warning: '\u26A0',
  error: '\u2717',
}

const DURATION = 3500
const EXIT_MS = 300

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(0)

  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = nextId.current++
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t))
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), EXIT_MS)
    }, DURATION)
  }, [])

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      <div style={{
        position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999,
        display: 'flex', flexDirection: 'column-reverse', gap: '8px',
        pointerEvents: 'none',
      }}>
        {toasts.map(t => (
          <ToastItem key={t.id} toast={t} onDismiss={() =>
            setToasts(prev => prev.filter(x => x.id !== t.id))
          } />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const [visible, setVisible] = useState(false)
  const color = COLORS[toast.type]

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))
  }, [])

  const opacity = toast.exiting ? 0 : visible ? 1 : 0
  const translateY = toast.exiting ? 20 : visible ? 0 : 20

  return (
    <div
      style={{
        display: 'flex', alignItems: 'center', gap: '10px',
        padding: '10px 16px',
        background: 'var(--bg-card)',
        border: `1px solid color-mix(in srgb, ${color} 40%, var(--border))`,
        borderRadius: 'var(--radius)',
        boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
        fontSize: '12px', color: 'var(--text-primary)',
        pointerEvents: 'auto',
        opacity,
        transform: `translateY(${translateY}px)`,
        transition: `opacity ${EXIT_MS}ms ease, transform ${EXIT_MS}ms ease`,
        maxWidth: '360px',
      }}
    >
      <span style={{ fontSize: '14px', color, flexShrink: 0 }}>{ICONS[toast.type]}</span>
      <span style={{ flex: 1 }}>{toast.message}</span>
      <button
        onClick={onDismiss}
        style={{
          background: 'none', border: 'none', color: 'var(--text-muted)',
          cursor: 'pointer', fontSize: '14px', padding: '0 2px', flexShrink: 0,
        }}
      >
        &times;
      </button>
    </div>
  )
}
