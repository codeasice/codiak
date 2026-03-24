import { useState, useEffect } from 'react'
import { useSyncHealth } from '../../hooks/dragon-keeper/use-sync-health'

const STATUS_COLORS: Record<string, string> = {
  ok: 'var(--success)',
  warning: 'var(--warning)',
  error: 'var(--danger)',
  never: 'var(--text-dim)',
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return 'Never'
  try {
    const d = new Date(ts)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return 'Just now'
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHr = Math.floor(diffMin / 60)
    if (diffHr < 24) return `${diffHr}h ago`
    const diffDay = Math.floor(diffHr / 24)
    return `${diffDay}d ago`
  } catch {
    return ts
  }
}

function StatusDot({ status }: { status: string }) {
  return (
    <span style={{
      display: 'inline-block',
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: STATUS_COLORS[status] || STATUS_COLORS.never,
      flexShrink: 0,
    }} />
  )
}

export default function SyncHealthCollapsible() {
  const { data, isLoading } = useSyncHealth()
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    if (data?.has_warning_or_error) {
      setIsOpen(true)
    }
  }, [data?.has_warning_or_error])

  if (isLoading) {
    return (
      <div style={{
        padding: '12px 16px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
      }}>
        <div style={{ width: '120px', height: '12px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
      </div>
    )
  }

  if (!data || !data.has_data) return null

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
    }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '12px 16px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text-muted)',
          fontSize: '12px',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          fontFamily: 'var(--font)',
        }}
      >
        <span style={{
          transform: isOpen ? 'rotate(90deg)' : 'rotate(0)',
          transition: 'transform 0.2s',
          fontSize: '10px',
        }}>
          &#9654;
        </span>
        <span>Sync Health</span>
        <span style={{ display: 'flex', gap: '4px', marginLeft: '8px' }}>
          {data.accounts.map(a => (
            <StatusDot key={a.account_id} status={a.status} />
          ))}
        </span>
      </button>

      {isOpen && (
        <div style={{ padding: '0 16px 12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.accounts.map(a => (
            <div
              key={a.account_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                padding: '4px 0',
              }}
            >
              <StatusDot status={a.status} />
              <span style={{ flex: 1, color: 'var(--text-primary)' }}>{a.account_name}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                {formatTimestamp(a.last_sync_at)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
