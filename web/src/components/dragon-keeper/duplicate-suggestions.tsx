import { useDuplicateSuggestions, type DuplicateSuggestion } from '../../hooks/dragon-keeper/use-duplicate-suggestions'
import type { RecurringItem } from '../../hooks/dragon-keeper/use-recurring'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

interface DuplicateSuggestionsProps {
  items: RecurringItem[]
  onCombine: (anchor: RecurringItem, sourceId: number) => void
}

export default function DuplicateSuggestions({ items, onCombine }: DuplicateSuggestionsProps) {
  const { data, isLoading } = useDuplicateSuggestions(items.some(i => i.type === 'expense' && i.status === 'active'))

  const suggestions = data?.suggestions ?? []
  if (isLoading || suggestions.length === 0) return null

  const itemById = new Map(items.map(i => [i.id, i]))

  return (
    <div style={{
      background: 'color-mix(in srgb, var(--accent) 8%, transparent)',
      border: '1px solid color-mix(in srgb, var(--accent) 25%, transparent)',
      borderRadius: 'var(--radius-lg)', padding: '16px 20px',
    }}>
      <div style={{ marginBottom: '10px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Possible duplicates
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
          Similar names and matching amounts — review before combining.
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {suggestions.map((s: DuplicateSuggestion) => {
          const anchor = itemById.get(s.item_a_id)
          if (!anchor) return null
          return (
            <div key={`${s.item_a_id}-${s.item_b_id}`} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px',
              flexWrap: 'wrap', padding: '10px 12px',
              background: 'var(--bg-card)', borderRadius: 'var(--radius)',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                <span style={{ fontWeight: 600 }}>{s.payee_a}</span>
                <span style={{ color: 'var(--text-muted)' }}> ↔ </span>
                <span style={{ fontWeight: 600 }}>{s.payee_b}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px', marginLeft: '8px' }}>
                  {formatCurrency(s.amount_a)} · {s.cadence} · {Math.round(s.name_similarity * 100)}% name match
                </span>
              </div>
              <button
                onClick={() => onCombine(anchor, s.item_b_id)}
                style={{
                  padding: '5px 12px', fontSize: '11px', fontWeight: 600,
                  borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                  background: 'var(--accent)', color: '#fff', whiteSpace: 'nowrap',
                }}
              >
                Review & combine
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
