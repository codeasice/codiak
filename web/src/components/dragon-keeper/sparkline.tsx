import { useState } from 'react'

export interface SparklinePoint {
  date: string
  value: number
}

interface SparklineProps {
  points: SparklinePoint[]
  formatValue?: (value: number) => string
  barColor?: string
  lastBarColor?: string
}

function defaultFormatValue(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

export default function Sparkline({
  points,
  formatValue = defaultFormatValue,
  barColor = 'var(--text-muted)',
  lastBarColor = 'var(--accent)',
}: SparklineProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  if (points.length === 0) {
    return (
      <div
        title="No charge history"
        style={{ width: '88px', height: '24px', color: 'var(--text-muted)', fontSize: '11px' }}
      >
        —
      </div>
    )
  }

  const max = Math.max(...points.map(p => p.value), 1)
  const barWidth = 6
  const gap = 2
  const maxHeight = 24

  return (
    <div
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'flex-end',
        gap: `${gap}px`,
        height: `${maxHeight}px`,
        minWidth: `${points.length * (barWidth + gap)}px`,
      }}
    >
      {points.map((point, i) => {
        const isLast = i === points.length - 1
        const h = Math.max(2, (point.value / max) * maxHeight)

        return (
          <div
            key={`${point.date}-${i}`}
            onMouseEnter={() => setHoveredIdx(i)}
            onMouseLeave={() => setHoveredIdx(null)}
            style={{
              width: `${barWidth}px`,
              height: `${h}px`,
              background: isLast ? lastBarColor : barColor,
              opacity: isLast ? 1 : 0.45,
              borderRadius: '2px',
              transition: 'opacity 0.15s',
              ...(hoveredIdx === i ? { opacity: 1 } : {}),
            }}
          />
        )
      })}

      {hoveredIdx !== null && points[hoveredIdx] && (
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
          {points[hoveredIdx].date}: {formatValue(points[hoveredIdx].value)}
        </div>
      )}
    </div>
  )
}
