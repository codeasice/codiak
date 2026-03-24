import { useState } from 'react'
import { useGreeting } from '../../hooks/dragon-keeper/use-dragon-state'

function Skeleton() {
  return (
    <div style={{
      padding: '12px 20px',
      background: `linear-gradient(135deg,
        color-mix(in srgb, var(--accent) 8%, var(--bg-card)),
        color-mix(in srgb, var(--accent) 3%, var(--bg-card)))`,
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      display: 'flex', alignItems: 'center', gap: '12px',
    }}>
      <div style={{
        width: '260px', height: '14px',
        background: 'var(--bg-hover)', borderRadius: '4px',
      }} />
    </div>
  )
}

export default function KeeperGreetingStrip() {
  const { data, isLoading, isError } = useGreeting()
  const [collapsed, setCollapsed] = useState(false)

  if (isLoading) return <Skeleton />
  if (isError || !data || collapsed) return null

  const hasStreak = data.streak > 1
  const isRecovery = (data as any).recovery === true
  const tintColor = isRecovery ? 'var(--warning)' : 'var(--accent)'

  return (
    <div style={{
      padding: '10px 16px',
      background: `linear-gradient(135deg,
        color-mix(in srgb, ${tintColor} 8%, var(--bg-card)),
        color-mix(in srgb, ${tintColor} 3%, var(--bg-card)))`,
      border: `1px solid color-mix(in srgb, ${tintColor} 20%, var(--border))`,
      borderRadius: 'var(--radius)',
      display: 'flex', alignItems: 'center', gap: '10px',
    }}>
      {isRecovery ? (
        <span style={{ fontSize: '16px', lineHeight: 1 }} aria-label="welcome back">
          👋
        </span>
      ) : hasStreak ? (
        <span style={{ fontSize: '16px', lineHeight: 1 }} aria-label="streak">
          🔥
        </span>
      ) : null}
      <span style={{
        flex: 1, fontSize: '13px', fontWeight: 500,
        color: 'var(--text-primary)',
      }}>
        {data.greeting}
      </span>
      <button
        onClick={() => setCollapsed(true)}
        aria-label="Dismiss greeting"
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-muted)', padding: '2px 4px', fontSize: '16px',
          lineHeight: 1, borderRadius: 'var(--radius)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
        onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-primary)')}
        onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
      >
        ✕
      </button>
    </div>
  )
}
