import { useState } from 'react'
import { useEngagement, type EngagementDay } from '../../hooks/dragon-keeper/use-engagement'

const DAYS = 90
const SQUARE_SIZE = 10
const GAP = 2
const ROWS = 7

function buildDayMap(history: EngagementDay[]): Map<string, EngagementDay> {
  const map = new Map<string, EngagementDay>()
  for (const d of history) map.set(d.date, d)
  return map
}

function last90Dates(): string[] {
  const dates: string[] = []
  const now = new Date()
  for (let i = DAYS - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    dates.push(d.toISOString().slice(0, 10))
  }
  return dates
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function Skeleton() {
  const cols = Math.ceil(DAYS / ROWS)
  return (
    <div style={{
      padding: '20px 24px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
    }}>
      <div style={{
        width: '140px', height: '14px', background: 'var(--bg-hover)',
        borderRadius: '4px', marginBottom: '16px',
      }} />
      <div style={{
        width: `${cols * (SQUARE_SIZE + GAP)}px`,
        height: `${ROWS * (SQUARE_SIZE + GAP)}px`,
        background: 'var(--bg-hover)',
        borderRadius: '4px',
      }} />
    </div>
  )
}

interface TooltipState {
  date: string
  actions: number
  visits: number
  x: number
  y: number
}

export default function ActivitySquares() {
  const { data, isLoading, isError } = useEngagement()
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  if (isLoading) return <Skeleton />

  if (isError || !data) {
    return (
      <div style={{
        padding: '20px 24px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        color: 'var(--text-muted)',
        fontSize: '13px',
      }}>
        Unable to load engagement data.
      </div>
    )
  }

  const dayMap = buildDayMap(data.history)
  const dates = last90Dates()
  const { streak } = data

  const cols = Math.ceil(dates.length / ROWS)

  const squares = dates.map((date, i) => {
    const entry = dayMap.get(date)
    const hasVisit = !!entry && entry.visit_count > 0
    const hasActions = !!entry && entry.actions_count > 0

    let fill: string
    if (hasActions) {
      fill = 'var(--accent)'
    } else if (hasVisit) {
      fill = 'color-mix(in srgb, var(--accent) 30%, transparent)'
    } else {
      fill = 'color-mix(in srgb, var(--text-muted) 10%, transparent)'
    }

    const col = Math.floor(i / ROWS)
    const row = i % ROWS

    return (
      <rect
        key={date}
        x={col * (SQUARE_SIZE + GAP)}
        y={row * (SQUARE_SIZE + GAP)}
        width={SQUARE_SIZE}
        height={SQUARE_SIZE}
        rx={2}
        fill={fill}
        style={{ cursor: 'pointer' }}
        onMouseEnter={(e) => {
          const rect = (e.target as SVGRectElement).getBoundingClientRect()
          setTooltip({
            date,
            actions: entry?.actions_count ?? 0,
            visits: entry?.visit_count ?? 0,
            x: rect.left + rect.width / 2,
            y: rect.top,
          })
        }}
        onMouseLeave={() => setTooltip(null)}
      />
    )
  })

  const svgWidth = cols * (SQUARE_SIZE + GAP) - GAP
  const svgHeight = ROWS * (SQUARE_SIZE + GAP) - GAP

  return (
    <div style={{
      padding: '20px 24px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      position: 'relative',
    }}>
      {/* Streak header */}
      <div style={{
        display: 'flex',
        alignItems: 'baseline',
        justifyContent: 'space-between',
        marginBottom: '16px',
        flexWrap: 'wrap',
        gap: '8px',
      }}>
        <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
          {streak.streak > 0
            ? `\uD83D\uDD25 ${streak.streak} day streak`
            : 'Start your streak!'}
        </div>
        {streak.days_away != null && streak.days_away > 1 && (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Last visited {streak.days_away} days ago
          </div>
        )}
      </div>

      {/* Grid */}
      <div style={{ overflowX: 'auto' }}>
        <svg width={svgWidth} height={svgHeight}>
          {squares}
        </svg>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed',
          left: tooltip.x,
          top: tooltip.y - 8,
          transform: 'translate(-50%, -100%)',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '6px 10px',
          fontSize: '11px',
          color: 'var(--text-primary)',
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        }}>
          <div style={{ fontWeight: 600, marginBottom: '2px' }}>
            {formatDate(tooltip.date)}
          </div>
          <div style={{ color: 'var(--text-muted)' }}>
            {tooltip.visits > 0
              ? `${tooltip.visits} visit${tooltip.visits !== 1 ? 's' : ''}, ${tooltip.actions} action${tooltip.actions !== 1 ? 's' : ''}`
              : 'No activity'}
          </div>
        </div>
      )}
    </div>
  )
}
