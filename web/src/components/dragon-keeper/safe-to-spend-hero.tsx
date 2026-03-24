import { useState } from 'react'
import { useSafeToSpend } from '../../hooks/dragon-keeper/use-safe-to-spend'

const STATUS_CONFIG = {
  healthy: { color: 'var(--success)', label: 'Healthy' },
  caution: { color: 'var(--warning)', label: 'Caution' },
  critical: { color: 'var(--danger)', label: 'Critical' },
} as const

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatShortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function Skeleton() {
  return (
    <div style={{
      padding: '32px 24px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      textAlign: 'center',
    }}>
      <div style={{
        width: '120px', height: '14px', background: 'var(--bg-hover)',
        borderRadius: '4px', margin: '0 auto 16px',
      }} />
      <div style={{
        width: '200px', height: '40px', background: 'var(--bg-hover)',
        borderRadius: '6px', margin: '0 auto 12px',
      }} />
      <div style={{
        width: '80px', height: '12px', background: 'var(--bg-hover)',
        borderRadius: '4px', margin: '0 auto',
      }} />
    </div>
  )
}

function BreakdownRow({ label, amount, color }: { label: string; amount: number; color?: string }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '4px 0', fontSize: '12px',
    }}>
      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span style={{
        fontVariantNumeric: 'tabular-nums', fontWeight: 600,
        color: color ?? 'var(--text-primary)',
      }}>
        {formatCurrency(amount)}
      </span>
    </div>
  )
}

export default function SafeToSpendHero() {
  const { data, isLoading, isError } = useSafeToSpend()
  const [expanded, setExpanded] = useState(false)

  if (isLoading) return <Skeleton />

  if (isError || !data) {
    return (
      <div style={{
        padding: '24px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '13px',
      }}>
        Unable to load safe-to-spend data.
      </div>
    )
  }

  if (!data.has_data) {
    return (
      <div style={{
        padding: '32px 24px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '14px',
      }}>
        Import YNAB data to see your safe-to-spend number.
      </div>
    )
  }

  const stsAmount = data.safe_to_spend ?? data.amount ?? 0
  const config = STATUS_CONFIG[data.status]
  const hasProjection = data.upcoming_income !== undefined

  return (
    <div style={{
      padding: '24px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
          letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '8px',
        }}>
          Safe to Spend
        </div>
        <div style={{
          fontSize: '36px', fontWeight: 700, color: config.color,
          lineHeight: 1.2, marginBottom: '8px',
        }}>
          {formatCurrency(stsAmount)}
        </div>
        <div style={{
          display: 'inline-block',
          padding: '2px 10px',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: 600,
          color: config.color,
          background: `color-mix(in srgb, ${config.color} 12%, transparent)`,
        }}>
          {config.label}
        </div>

        {hasProjection && (
          <div style={{ marginTop: '8px' }}>
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-muted)', fontSize: '11px', fontWeight: 500,
                padding: '4px 8px',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--accent)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
            >
              {expanded ? 'Hide' : 'Show'} breakdown {expanded ? '\u25B2' : '\u25BC'}
            </button>
          </div>
        )}
      </div>

      {expanded && hasProjection && (
        <div style={{
          marginTop: '16px', paddingTop: '16px',
          borderTop: '1px solid var(--border)',
          maxWidth: '320px', marginLeft: 'auto', marginRight: 'auto',
        }}>
          <BreakdownRow label="Current balance" amount={data.starting_balance} />
          {data.pending_outflows > 0 && (
            <BreakdownRow label="Pending outflows" amount={-data.pending_outflows} color="var(--danger)" />
          )}
          {data.upcoming_income > 0 && (
            <BreakdownRow label={`Income (next ${data.projection_days}d)`} amount={data.upcoming_income} color="var(--success)" />
          )}
          {data.upcoming_expenses > 0 && (
            <BreakdownRow label={`Bills (next ${data.projection_days}d)`} amount={-data.upcoming_expenses} color="var(--danger)" />
          )}
          <div style={{
            borderTop: '1px solid var(--border)', marginTop: '8px', paddingTop: '8px',
          }}>
            <BreakdownRow label="Projected minimum" amount={data.min_projected_balance} />
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '2px 0', fontSize: '11px',
            }}>
              <span style={{ color: 'var(--text-muted)' }}>
                Lowest on {formatShortDate(data.min_balance_date)}
              </span>
            </div>
            <BreakdownRow label={`Buffer (-${formatCurrency(data.buffer_amount)})`} amount={-data.buffer_amount} />
          </div>
          <div style={{
            borderTop: '1px solid var(--border)', marginTop: '8px', paddingTop: '8px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            fontSize: '13px', fontWeight: 700,
          }}>
            <span style={{ color: 'var(--text-primary)' }}>Safe to spend</span>
            <span style={{ color: config.color, fontVariantNumeric: 'tabular-nums' }}>
              {formatCurrency(stsAmount)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
