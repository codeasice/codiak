import { useState } from 'react'
import { useDragonState, type DragonStateComponent } from '../../hooks/dragon-keeper/use-dragon-state'

const STATUS_DOT: Record<string, string> = {
  healthy: 'var(--success)',
  attention: 'var(--warning)',
  critical: 'var(--danger)',
}

const STATE_COLOR: Record<string, string> = {
  sleeping: 'var(--success)',
  stirring: 'var(--warning)',
  raging: 'var(--danger)',
}

function TooltipCard({ components }: { components: DragonStateComponent[] }) {
  return (
    <div style={{
      position: 'absolute',
      top: 'calc(100% + 8px)',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '12px 14px',
      minWidth: '220px',
      boxShadow: '0 8px 24px rgba(0,0,0,.35)',
      zIndex: 100,
    }}>
      <div style={{
        fontSize: '10px', fontWeight: 600, textTransform: 'uppercase',
        letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: '8px',
      }}>
        Health Breakdown
      </div>
      {components.map((c) => (
        <div key={c.name} style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '4px 0', fontSize: '12px',
        }}>
          <span style={{
            width: '7px', height: '7px', borderRadius: '50%',
            background: STATUS_DOT[c.status] ?? 'var(--text-muted)',
            flexShrink: 0,
          }} />
          <span style={{ color: 'var(--text-primary)', fontWeight: 500, flex: 1 }}>
            {c.name}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
            {c.detail}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function DragonStateIndicator() {
  const { data, isLoading } = useDragonState()
  const [hovering, setHovering] = useState(false)

  if (isLoading || !data) {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: '6px',
        padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600,
        background: 'var(--bg-hover)', color: 'var(--text-muted)',
      }}>
        <span style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: 'var(--bg-hover)',
        }} />
        &hellip;
      </span>
    )
  }

  const dotColor = STATE_COLOR[data.state] ?? 'var(--text-muted)'

  return (
    <span
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      style={{
        position: 'relative',
        display: 'inline-flex', alignItems: 'center', gap: '6px',
        padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600,
        background: `color-mix(in srgb, ${dotColor} 10%, transparent)`,
        color: dotColor,
        cursor: 'default',
        userSelect: 'none',
      }}
    >
      <span style={{
        width: '8px', height: '8px', borderRadius: '50%',
        background: dotColor,
        boxShadow: data.state !== 'sleeping' ? `0 0 6px ${dotColor}` : 'none',
      }} />
      {data.label}
      {hovering && <TooltipCard components={data.components} />}
    </span>
  )
}
