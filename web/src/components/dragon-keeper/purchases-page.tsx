import { useState } from 'react'
import { ChevronUp, ChevronDown, ExternalLink } from 'lucide-react'
import {
  usePurchases,
  useUpdateCost,
  useUpdatePurchaseDate,
  useMovePurchase,
  type Purchase,
} from '../../hooks/dragon-keeper/use-purchases'

const STATUS_COLORS: Record<string, string> = {
  considering: 'var(--text-muted)',
  approved: 'var(--accent)',
  purchased: 'var(--success)',
  dropped: 'var(--text-muted)',
}

const STATUS_LABELS: Record<string, string> = {
  considering: 'Considering',
  approved: 'Approved',
  purchased: 'Purchased',
  dropped: 'Dropped',
}

function fmt(n: number | null) {
  if (n == null) return '—'
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function InlineNumberEdit({
  value,
  onSave,
}: {
  value: number | null
  onSave: (v: number) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  if (!editing) {
    return (
      <button
        onClick={() => { setDraft(value?.toString() ?? ''); setEditing(true) }}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', padding: 0, fontFamily: 'inherit', fontSize: 'inherit' }}
      >
        {fmt(value)}
      </button>
    )
  }
  return (
    <input
      autoFocus
      type="number"
      step="0.01"
      value={draft}
      onChange={e => setDraft(e.target.value)}
      onBlur={() => {
        const n = parseFloat(draft)
        if (!isNaN(n)) onSave(n)
        setEditing(false)
      }}
      onKeyDown={e => {
        if (e.key === 'Enter') { const n = parseFloat(draft); if (!isNaN(n)) onSave(n); setEditing(false) }
        if (e.key === 'Escape') setEditing(false)
      }}
      style={{ width: '90px', padding: '2px 6px', fontSize: 'inherit', fontFamily: 'inherit' }}
    />
  )
}

function InlineDateEdit({
  value,
  onSave,
}: {
  value: string | null
  onSave: (v: string | null) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  if (!editing) {
    return (
      <button
        onClick={() => { setDraft(value ?? ''); setEditing(true) }}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: value ? 'var(--text-primary)' : 'var(--text-muted)', padding: 0, fontFamily: 'inherit', fontSize: 'inherit' }}
      >
        {value || 'Set date'}
      </button>
    )
  }
  return (
    <input
      autoFocus
      type="date"
      value={draft}
      onChange={e => setDraft(e.target.value)}
      onBlur={() => { onSave(draft || null); setEditing(false) }}
      onKeyDown={e => {
        if (e.key === 'Enter') { onSave(draft || null); setEditing(false) }
        if (e.key === 'Escape') setEditing(false)
      }}
      style={{ padding: '2px 6px', fontSize: 'inherit', fontFamily: 'inherit' }}
    />
  )
}

function PurchaseRow({
  purchase,
  isFirst,
  isLast,
  onMove,
  onCostSave,
  onDateSave,
}: {
  purchase: Purchase
  isFirst: boolean
  isLast: boolean
  onMove: (direction: 'up' | 'down') => void
  onCostSave: (cost: number) => void
  onDateSave: (date: string | null) => void
}) {
  const statusColor = STATUS_COLORS[purchase.status] ?? 'var(--text-muted)'
  const interestExtra = purchase.true_cost_1yr != null && purchase.cost != null
    ? purchase.true_cost_1yr - purchase.cost
    : null

  return (
    <tr>
      <td style={{ width: 56, textAlign: 'center', padding: '6px 0' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
          <button
            onClick={() => onMove('up')}
            disabled={isFirst}
            style={{ background: 'none', border: 'none', cursor: isFirst ? 'default' : 'pointer', padding: '1px 4px', color: isFirst ? 'var(--border)' : 'var(--text-muted)' }}
            title="Move up"
          >
            <ChevronUp size={14} />
          </button>
          <button
            onClick={() => onMove('down')}
            disabled={isLast}
            style={{ background: 'none', border: 'none', cursor: isLast ? 'default' : 'pointer', padding: '1px 4px', color: isLast ? 'var(--border)' : 'var(--text-muted)' }}
            title="Move down"
          >
            <ChevronDown size={14} />
          </button>
        </div>
      </td>
      <td style={{ padding: '8px 12px' }}>
        <div style={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6 }}>
          {purchase.item}
          {purchase.url && (
            <a href={purchase.url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-muted)', lineHeight: 1 }}>
              <ExternalLink size={11} />
            </a>
          )}
        </div>
        {purchase.category && (
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>{purchase.category}</div>
        )}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        <InlineNumberEdit value={purchase.cost} onSave={onCostSave} />
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {purchase.true_cost_1yr != null ? (
          <span title={`+${fmt(interestExtra)} interest`} style={{ color: 'var(--error)' }}>
            {fmt(purchase.true_cost_1yr)}
          </span>
        ) : '—'}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'center' }}>
        <span style={{ fontSize: '12px', color: statusColor, fontWeight: 500 }}>
          {STATUS_LABELS[purchase.status] ?? purchase.status}
        </span>
      </td>
      <td style={{ padding: '8px 12px' }}>
        <InlineDateEdit value={purchase.purchase_date} onSave={onDateSave} />
      </td>
      <td style={{ padding: '8px 12px', color: 'var(--text-muted)', fontSize: '12px' }}>
        {purchase.added || '—'}
      </td>
    </tr>
  )
}

export default function PurchasesPage() {
  const { data, isLoading, isError } = usePurchases()
  const updateCost = useUpdateCost()
  const updateDate = useUpdatePurchaseDate()
  const move = useMovePurchase()
  const [statusFilter, setStatusFilter] = useState<string>('active')

  if (isLoading) return <div className="info-box">Loading purchases…</div>
  if (isError) return <div className="error-box">Failed to load purchases. Is the vault path configured?</div>

  const { purchases, max_cc_rate } = data!

  const filtered = purchases.filter(p => {
    if (statusFilter === 'active') return p.status === 'considering' || p.status === 'approved'
    if (statusFilter === 'all') return true
    return p.status === statusFilter
  })

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px' }}>Planned Purchases</h2>
          {max_cc_rate != null && (
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 3 }}>
              True cost calculated at {max_cc_rate}% APR (highest CC rate) over 1 year
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {['active', 'all', 'purchased', 'dropped'].map(f => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`btn btn-ghost${statusFilter === f ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}
            >
              {f === 'active' ? 'Active' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="info-box">
          No purchases found. Add a note to your vault using the <strong>template - purchase</strong> template
          in <code>1 Personal/3 Resources/Shopping</code>.
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '12px', textAlign: 'left' }}>
                <th style={{ width: 56 }} />
                <th style={{ padding: '6px 12px' }}>Item</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Cost</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>True Cost (1yr)</th>
                <th style={{ padding: '6px 12px', textAlign: 'center' }}>Status</th>
                <th style={{ padding: '6px 12px' }}>Purchase Date</th>
                <th style={{ padding: '6px 12px' }}>Added</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p, idx) => (
                <PurchaseRow
                  key={p.filename}
                  purchase={p}
                  isFirst={idx === 0}
                  isLast={idx === filtered.length - 1}
                  onMove={dir => move.mutate({ filename: p.filename, direction: dir })}
                  onCostSave={cost => updateCost.mutate({ filename: p.filename, cost })}
                  onDateSave={date => updateDate.mutate({ filename: p.filename, date })}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
