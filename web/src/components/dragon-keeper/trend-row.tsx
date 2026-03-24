import { useState } from 'react'
import { useSpendingTrends, type SpendingTrendItem, type PeriodValue } from '../../hooks/dragon-keeper/use-spending-trends'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatPeriodDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/* ---- Skeleton ---- */

function RowSkeleton() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '12px',
      padding: '12px 16px',
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{ width: '120px', height: '12px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
      <div style={{ flex: 1, display: 'flex', gap: '3px', alignItems: 'flex-end', height: '24px' }}>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} style={{
            width: '10px',
            height: `${8 + Math.random() * 16}px`,
            background: 'var(--bg-hover)',
            borderRadius: '2px',
          }} />
        ))}
      </div>
      <div style={{ width: '48px', height: '12px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
      <div style={{ width: '64px', height: '12px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
    </div>
  )
}

/* ---- Sparkline ---- */

interface SparklineProps {
  periods: PeriodValue[]
}

function Sparkline({ periods }: SparklineProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)
  const max = Math.max(...periods.map(p => p.total), 1)
  const barWidth = 10
  const gap = 3
  const maxHeight = 24

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'flex-end', gap: `${gap}px`, height: `${maxHeight}px` }}>
      {periods.map((p, i) => {
        const h = Math.max(2, (p.total / max) * maxHeight)
        const isLast = i === periods.length - 1
        return (
          <div
            key={p.period_start}
            onMouseEnter={() => setHoveredIdx(i)}
            onMouseLeave={() => setHoveredIdx(null)}
            style={{
              width: `${barWidth}px`,
              height: `${h}px`,
              background: isLast ? 'var(--accent)' : 'var(--text-muted)',
              opacity: isLast ? 1 : 0.45,
              borderRadius: '2px',
              cursor: 'default',
              transition: 'opacity 0.15s',
              ...(hoveredIdx === i ? { opacity: 1 } : {}),
            }}
          />
        )
      })}

      {hoveredIdx !== null && periods[hoveredIdx] && (
        <div style={{
          position: 'absolute',
          bottom: `${maxHeight + 6}px`,
          left: `${hoveredIdx * (barWidth + gap)}px`,
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '4px 8px',
          fontSize: '11px',
          color: 'var(--text-primary)',
          whiteSpace: 'nowrap',
          zIndex: 10,
          pointerEvents: 'none',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        }}>
          {formatPeriodDate(periods[hoveredIdx].period_start)}: {formatCurrency(periods[hoveredIdx].total)}
        </div>
      )}
    </div>
  )
}

/* ---- Delta badge ---- */

function DeltaBadge({ delta }: { delta: number }) {
  const isDown = delta <= 0
  const color = isDown ? 'var(--success)' : 'var(--danger)'
  const arrow = isDown ? '▼' : '▲'
  const display = `${arrow} ${Math.abs(delta).toFixed(1)}%`

  return (
    <span style={{
      fontSize: '11px', fontWeight: 600, color,
      fontVariantNumeric: 'tabular-nums',
      minWidth: '60px', textAlign: 'right',
    }}>
      {display}
    </span>
  )
}

/* ---- Trend Row ---- */

function TrendRow({ item, onClick }: { item: SpendingTrendItem; onClick?: () => void }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '10px 16px',
        borderBottom: '1px solid var(--border)',
        cursor: 'pointer',
        background: hovered ? 'var(--bg-hover)' : 'transparent',
        transition: 'background 0.15s',
      }}
    >
      <div style={{
        width: '140px', minWidth: '140px',
        fontSize: '13px', fontWeight: 500,
        color: 'var(--text-primary)',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}>
        {item.category_name}
      </div>

      <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <Sparkline periods={item.periods} />
      </div>

      <DeltaBadge delta={item.delta_pct} />

      <div style={{
        fontSize: '13px', fontWeight: 600,
        color: 'var(--text-primary)',
        fontVariantNumeric: 'tabular-nums',
        minWidth: '72px', textAlign: 'right',
      }}>
        {formatCurrency(item.grand_total)}
      </div>
    </div>
  )
}

/* ---- Main component ---- */

interface SpendingTrendsProps {
  onCategoryClick?: (categoryId: string) => void
}

export default function SpendingTrends({ onCategoryClick }: SpendingTrendsProps) {
  const { data, isLoading, isError } = useSpendingTrends()

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--border)',
      }}>
        <h3 style={{
          margin: 0, fontSize: '13px', fontWeight: 600,
          textTransform: 'uppercase', letterSpacing: '1px',
          color: 'var(--text-muted)',
        }}>
          Spending Trends
        </h3>
      </div>

      {isLoading && (
        <div>
          {Array.from({ length: 5 }).map((_, i) => <RowSkeleton key={i} />)}
        </div>
      )}

      {!isLoading && (isError || !data) && (
        <div style={{
          padding: '24px', textAlign: 'center',
          color: 'var(--text-muted)', fontSize: '13px',
        }}>
          Unable to load spending trends.
        </div>
      )}

      {!isLoading && data && data.length === 0 && (
        <div style={{
          padding: '32px 24px', textAlign: 'center',
          color: 'var(--text-muted)', fontSize: '13px',
        }}>
          Import data to see trends
        </div>
      )}

      {!isLoading && data && data.length > 0 && (
        <div>
          {data.map(item => (
            <TrendRow
              key={item.category_id}
              item={item}
              onClick={() => onCategoryClick?.(item.category_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
