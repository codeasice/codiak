import { useState, useMemo, useRef, useEffect } from 'react'
import { useCategoryDetail, type CategoryTransaction } from '../../hooks/dragon-keeper/use-category-detail'
import { useCategories, useRecategorize } from '../../hooks/dragon-keeper/use-categorization-queue'
import { useToast } from './toast'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatPeriodDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/* ---- Skeleton ---- */

function DetailSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ width: '120px', height: '14px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
      </div>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px',
      }}>
        <div style={{ width: '200px', height: '20px', background: 'var(--bg-hover)', borderRadius: '4px', marginBottom: '8px' }} />
        <div style={{ width: '100px', height: '14px', background: 'var(--bg-hover)', borderRadius: '4px', marginBottom: '24px' }} />
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '120px' }}>
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} style={{
              flex: 1,
              height: `${20 + Math.random() * 100}px`,
              background: 'var(--bg-hover)',
              borderRadius: '4px 4px 0 0',
            }} />
          ))}
        </div>
      </div>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px',
      }}>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} style={{
            height: '44px', background: 'var(--bg-hover)',
            borderRadius: '4px', marginBottom: '8px',
          }} />
        ))}
      </div>
    </div>
  )
}

/* ---- Spending bar chart ---- */

interface SpendingChartProps {
  periods: { period_start: string; total: number; txn_count: number }[]
}

function SpendingChart({ periods }: SpendingChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  if (periods.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
        No spending data available
      </div>
    )
  }

  const max = Math.max(...periods.map(p => p.total), 1)
  const chartHeight = 160

  return (
    <div style={{ padding: '16px 0 0' }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: '4px',
        height: `${chartHeight}px`, position: 'relative',
      }}>
        {periods.map((p, i) => {
          const h = Math.max(4, (p.total / max) * (chartHeight - 24))
          const isHovered = hoveredIdx === i
          return (
            <div
              key={p.period_start}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{
                flex: 1,
                height: `${h}px`,
                background: isHovered ? 'var(--accent)' : 'color-mix(in srgb, var(--accent) 60%, transparent)',
                borderRadius: '4px 4px 0 0',
                cursor: 'default',
                transition: 'background 0.15s, height 0.2s',
                position: 'relative',
              }}
            >
              {isHovered && (
                <div style={{
                  position: 'absolute',
                  bottom: `${h + 8}px`,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius)',
                  padding: '6px 10px',
                  fontSize: '11px',
                  color: 'var(--text-primary)',
                  whiteSpace: 'nowrap',
                  zIndex: 10,
                  pointerEvents: 'none',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                }}>
                  <div style={{ fontWeight: 600 }}>{formatCurrency(p.total)}</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>
                    {p.txn_count} txn{p.txn_count !== 1 ? 's' : ''}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
      <div style={{
        display: 'flex', gap: '4px', marginTop: '8px',
        borderTop: '1px solid var(--border)', paddingTop: '8px',
      }}>
        {periods.map((p, i) => (
          <div key={p.period_start} style={{
            flex: 1, textAlign: 'center',
            fontSize: '10px', color: hoveredIdx === i ? 'var(--text-primary)' : 'var(--text-muted)',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {formatPeriodDate(p.period_start)}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ---- Transaction table ---- */

type SortKey = 'date' | 'payee' | 'amount' | 'memo'
type SortDir = 'asc' | 'desc'

function CategoryPickerInline({ onSelect, onCancel }: { onSelect: (id: string) => void; onCancel: () => void }) {
  const { data } = useCategories()
  const [search, setSearch] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => { inputRef.current?.focus() }, [])
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) onCancel()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onCancel])

  const filtered = useMemo(() => {
    if (!data?.categories) return []
    const term = search.toLowerCase()
    return data.categories.filter(c =>
      c.name.toLowerCase().includes(term) || c.group_name.toLowerCase().includes(term)
    )
  }, [data, search])

  const grouped = useMemo(() => {
    const groups: Record<string, typeof filtered> = {}
    for (const c of filtered) (groups[c.group_name] ??= []).push(c)
    return groups
  }, [filtered])

  return (
    <div ref={containerRef} style={{
      position: 'absolute', top: '100%', left: 0, zIndex: 20,
      width: '280px', maxHeight: '260px', overflowY: 'auto',
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
    }}>
      <input
        ref={inputRef}
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Search categories..."
        style={{
          width: '100%', padding: '8px 10px', fontSize: '12px',
          background: 'var(--bg-hover)', border: 'none', borderBottom: '1px solid var(--border)',
          color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box',
        }}
      />
      {Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)).map(([group, cats]) => (
        <div key={group}>
          <div style={{
            padding: '6px 10px', fontSize: '10px', fontWeight: 700,
            color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px',
          }}>
            {group}
          </div>
          {cats.map(c => (
            <div
              key={c.id}
              onClick={() => onSelect(c.id)}
              style={{
                padding: '6px 10px 6px 18px', fontSize: '12px',
                color: 'var(--text-primary)', cursor: 'pointer',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              {c.name}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

interface TransactionTableProps {
  transactions: CategoryTransaction[]
  onPayeeNavigate?: (payee: string) => void
}

function TransactionTable({ transactions, onPayeeNavigate }: TransactionTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('date')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [editingId, setEditingId] = useState<string | null>(null)
  const recategorize = useRecategorize()
  const { data: catData } = useCategories()
  const { toast } = useToast()

  const catNames = useMemo(() => {
    const map: Record<string, string> = {}
    for (const c of catData?.categories ?? []) map[c.id] = c.name
    return map
  }, [catData])

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir(key === 'amount' ? 'desc' : 'asc')
    }
  }

  const sorted = useMemo(() => {
    const list = [...transactions]
    const dir = sortDir === 'asc' ? 1 : -1
    list.sort((a, b) => {
      switch (sortKey) {
        case 'date':
          return dir * a.date.localeCompare(b.date)
        case 'payee':
          return dir * (a.payee_name ?? '').localeCompare(b.payee_name ?? '')
        case 'amount':
          return dir * (Math.abs(a.amount) - Math.abs(b.amount))
        case 'memo':
          return dir * (a.memo ?? '').localeCompare(b.memo ?? '')
        default:
          return 0
      }
    })
    return list
  }, [transactions, sortKey, sortDir])

  const columns: { label: string; key: SortKey | null; align: string }[] = [
    { label: 'Date', key: 'date', align: 'left' },
    { label: 'Payee', key: 'payee', align: 'left' },
    { label: 'Amount', key: 'amount', align: 'right' },
    { label: 'Memo', key: 'memo', align: 'left' },
    { label: '', key: null, align: 'right' },
  ]

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {columns.map((col, i) => (
              <th
                key={i}
                onClick={col.key ? () => toggleSort(col.key!) : undefined}
                style={{
                  padding: '10px 12px',
                  textAlign: col.align as CanvasTextAlign,
                  fontSize: '10px', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                  whiteSpace: 'nowrap',
                  color: sortKey === col.key ? 'var(--accent)' : 'var(--text-muted)',
                  cursor: col.key ? 'pointer' : 'default',
                  userSelect: 'none',
                }}
              >
                {col.label}
                {sortKey === col.key && (
                  <span style={{ marginLeft: '4px', fontSize: '9px' }}>
                    {sortDir === 'asc' ? '\u25B2' : '\u25BC'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(t => (
            <tr
              key={t.id}
              style={{ borderBottom: '1px solid var(--border)' }}
              onMouseEnter={e => {
                for (const td of e.currentTarget.children as any)
                  td.style.background = 'var(--bg-hover)'
              }}
              onMouseLeave={e => {
                for (const td of e.currentTarget.children as any)
                  td.style.background = 'transparent'
              }}
            >
              <td style={{
                padding: '10px 12px', whiteSpace: 'nowrap',
                color: 'var(--text-muted)',
              }}>
                {formatDate(t.date)}
              </td>
              <td style={{
                padding: '10px 12px', fontWeight: 500,
                color: 'var(--text-primary)',
              }}>
                {onPayeeNavigate && t.payee_name ? (
                  <span
                    onClick={() => onPayeeNavigate(t.payee_name!)}
                    style={{ cursor: 'pointer', borderBottom: '1px dashed var(--text-muted)' }}
                    onMouseEnter={e => { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)' }}
                    onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--text-muted)' }}
                    title={`View all transactions for ${t.payee_name}`}
                  >
                    {t.payee_name}
                  </span>
                ) : (
                  t.payee_name || 'Unknown'
                )}
              </td>
              <td style={{
                padding: '10px 12px', textAlign: 'right', whiteSpace: 'nowrap',
                fontVariantNumeric: 'tabular-nums',
                color: t.amount < 0 ? 'var(--text-primary)' : 'var(--success)',
              }}>
                {formatCurrency(t.amount)}
              </td>
              <td style={{
                padding: '10px 12px',
                color: 'var(--text-muted)', fontSize: '12px',
                maxWidth: '300px', overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {t.memo || '—'}
              </td>
              <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', textAlign: 'right', position: 'relative' }}>
                <button
                  onClick={() => setEditingId(editingId === t.id ? null : t.id)}
                  style={{
                    padding: '3px 8px', fontSize: '11px', fontWeight: 600,
                    borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                    cursor: 'pointer', background: 'transparent',
                    color: 'var(--accent)',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  Re-categorize
                </button>
                {editingId === t.id && (
                  <CategoryPickerInline
                    onSelect={(categoryId) => {
                      const name = catNames[categoryId] || 'new category'
                      recategorize.mutate(
                        { transaction_id: t.id, category_id: categoryId },
                        { onSuccess: () => toast(`"${t.payee_name}" → ${name}`, 'success') },
                      )
                      setEditingId(null)
                    }}
                    onCancel={() => setEditingId(null)}
                  />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ---- Main component ---- */

interface CategoryDetailProps {
  categoryId: string
  onBack: () => void
  onPayeeNavigate?: (payee: string) => void
}

export default function CategoryDetail({ categoryId, onBack, onPayeeNavigate }: CategoryDetailProps) {
  const { data, isLoading, isError } = useCategoryDetail(categoryId)

  if (isLoading) return <DetailSkeleton />

  if (isError || !data) {
    return (
      <div style={{
        padding: '32px 24px', textAlign: 'center',
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
      }}>
        <div style={{ color: 'var(--danger)', fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
          Failed to load category details
        </div>
        <button
          onClick={onBack}
          style={{
            padding: '6px 16px', fontSize: '12px', fontWeight: 600,
            borderRadius: 'var(--radius)', border: '1px solid var(--border)',
            cursor: 'pointer', background: 'transparent',
            color: 'var(--accent)',
          }}
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Back link */}
      <button
        onClick={onBack}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--accent)', fontSize: '13px', fontWeight: 500,
          padding: 0, alignSelf: 'flex-start',
        }}
      >
        <span style={{ fontSize: '16px', lineHeight: 1 }}>&larr;</span>
        Back to Dashboard
      </button>

      {/* Header card */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 style={{
              margin: 0, fontSize: '18px', fontWeight: 700,
              color: 'var(--text-primary)',
            }}>
              {data.category_name}
            </h2>
            <div style={{
              fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px',
            }}>
              {data.group_name}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{
              fontSize: '22px', fontWeight: 700,
              color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums',
            }}>
              {formatCurrency(data.total_spending)}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {data.transaction_count} transaction{data.transaction_count !== 1 ? 's' : ''} &middot; last 12 weeks
            </div>
          </div>
        </div>

        {/* Spending chart */}
        <SpendingChart periods={data.spending_over_time} />
      </div>

      {/* Transaction table */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      }}>
        <div style={{
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <h3 style={{
            margin: 0, fontSize: '13px', fontWeight: 600,
            textTransform: 'uppercase', letterSpacing: '1px',
            color: 'var(--text-muted)',
          }}>
            Recent Transactions
          </h3>
        </div>

        {data.transactions.length === 0 ? (
          <div style={{
            padding: '32px 24px', textAlign: 'center',
            color: 'var(--text-muted)', fontSize: '13px',
          }}>
            No transactions found for this category
          </div>
        ) : (
          <TransactionTable transactions={data.transactions} onPayeeNavigate={onPayeeNavigate} />
        )}
      </div>
    </div>
  )
}
