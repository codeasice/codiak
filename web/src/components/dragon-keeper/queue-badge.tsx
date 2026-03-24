import { useQueueStats } from '../../hooks/dragon-keeper/use-categorization-queue'

export default function QueueBadge() {
  const { data } = useQueueStats()
  if (!data || data.pending_count === 0) return null

  const minutes = Math.ceil(data.estimated_seconds / 60)
  const timeLabel = minutes < 1 ? '~20 sec' : `~${minutes} min`

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '6px',
      padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600,
      background: `color-mix(in srgb, var(--accent) 12%, transparent)`,
      color: 'var(--accent)',
    }}>
      {data.pending_count} to review &middot; {timeLabel}
    </span>
  )
}
