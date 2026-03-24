import { useState, useMemo, useRef, useEffect, useCallback } from 'react'
import {
  useTransactionSearch,
  usePayeeSummary,
  useBulkRecategorize,
  type TransactionFilters,
  type TransactionRow,
} from '../../hooks/dragon-keeper/use-transaction-explorer'
import { useCategories, useRecategorize } from '../../hooks/dragon-keeper/use-categorization-queue'
import { useToast } from './toast'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/* ---- CategoryPickerInline ---- */

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

/* ---- Skeleton ---- */

function ExplorerSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ height: '48px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }} />
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px',
      }}>
        {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
          <div key={i} style={{
            height: '44px', background: 'var(--bg-hover)',
            borderRadius: '4px', marginBottom: '8px',
          }} />
        ))}
      </div>
    </div>
  )
}

/* ---- Payee Summary Header ---- */

function PayeeSummaryHeader({ payee }: { payee: string }) {
  const { data, isLoading } = usePayeeSummary(payee)

  if (isLoading || !data || data.transaction_count === 0) return null

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '16px 20px',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
            {data.payee}
          </h3>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            {data.first_date && data.last_date && (
              <>{formatDate(data.first_date)} — {formatDate(data.last_date)}</>
            )}
            {data.likely_recurring && (
              <span style={{
                marginLeft: '10px', padding: '2px 8px', fontSize: '10px', fontWeight: 600,
                background: 'color-mix(in srgb, var(--accent) 15%, transparent)',
                color: 'var(--accent)', borderRadius: '10px',
              }}>
                Likely recurring
              </span>
            )}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{
            fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)',
            fontVariantNumeric: 'tabular-nums',
          }}>
            {formatCurrency(data.total_amount)}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {data.transaction_count} transaction{data.transaction_count !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {data.has_mixed_categories && data.category_breakdown.length > 1 && (
        <div style={{
          marginTop: '12px', paddingTop: '12px',
          borderTop: '1px solid var(--border)',
        }}>
          <div style={{
            fontSize: '10px', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: '8px',
          }}>
            Category Breakdown
            <span style={{
              marginLeft: '8px', padding: '2px 6px', fontSize: '9px', fontWeight: 600,
              background: 'color-mix(in srgb, var(--warning, #f59e0b) 15%, transparent)',
              color: 'var(--warning, #f59e0b)', borderRadius: '8px',
            }}>
              Mixed
            </span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {data.category_breakdown.map((cat, i) => (
              <div key={i} style={{
                padding: '4px 10px', fontSize: '12px',
                background: 'var(--bg-hover)', borderRadius: 'var(--radius)',
                color: 'var(--text-primary)',
              }}>
                <span style={{ fontWeight: 600 }}>{cat.count}</span>
                <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>&times;</span>
                {cat.category_name}
                <span style={{ color: 'var(--text-muted)', marginLeft: '6px', fontSize: '11px' }}>
                  {formatCurrency(cat.amount)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ---- Filter Bar ---- */

interface FilterBarProps {
  filters: TransactionFilters
  onFilterChange: (updates: Partial<TransactionFilters>) => void
  categories: { id: string; name: string; group_name: string }[]
}

function FilterBar({ filters, onFilterChange, categories }: FilterBarProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const payeeInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { payeeInputRef.current?.focus() }, [])

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', fontSize: '13px',
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius)', color: 'var(--text-primary)',
    outline: 'none', boxSizing: 'border-box' as const,
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: '10px',
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '16px 20px',
    }}>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 260px' }}>
          <input
            ref={payeeInputRef}
            type="text"
            value={filters.payee ?? ''}
            onChange={e => onFilterChange({ payee: e.target.value || undefined, page: 1 })}
            placeholder="Search by payee name..."
            style={{ ...inputStyle, width: '100%', paddingLeft: '32px' }}
          />
          <span style={{
            position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-muted)', fontSize: '14px', pointerEvents: 'none',
          }}>
            &#x1F50D;
          </span>
        </div>

        <select
          value={filters.category_id ?? ''}
          onChange={e => onFilterChange({ category_id: e.target.value || undefined, page: 1 })}
          style={{ ...inputStyle, flex: '0 1 200px', cursor: 'pointer' }}
        >
          <option value="">All Categories</option>
          {categories.map(c => (
            <option key={c.id} value={c.id}>{c.group_name} / {c.name}</option>
          ))}
        </select>

        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            padding: '8px 14px', fontSize: '12px', fontWeight: 600,
            borderRadius: 'var(--radius)', border: '1px solid var(--border)',
            cursor: 'pointer', background: showAdvanced ? 'var(--bg-hover)' : 'transparent',
            color: 'var(--text-muted)',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)' }}
        >
          Filters {showAdvanced ? '\u25B2' : '\u25BC'}
        </button>

        {(filters.payee || filters.category_id || filters.date_from || filters.date_to || filters.amount_min != null || filters.amount_max != null) && (
          <button
            onClick={() => onFilterChange({
              payee: undefined, category_id: undefined,
              date_from: undefined, date_to: undefined,
              amount_min: undefined, amount_max: undefined,
              page: 1,
            })}
            style={{
              padding: '8px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: 'none',
              cursor: 'pointer', background: 'color-mix(in srgb, var(--danger) 15%, transparent)',
              color: 'var(--danger)',
            }}
          >
            Clear
          </button>
        )}
      </div>

      {showAdvanced && (
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>From</label>
            <input
              type="date"
              value={filters.date_from ?? ''}
              onChange={e => onFilterChange({ date_from: e.target.value || undefined, page: 1 })}
              style={{ ...inputStyle, width: '150px' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>To</label>
            <input
              type="date"
              value={filters.date_to ?? ''}
              onChange={e => onFilterChange({ date_to: e.target.value || undefined, page: 1 })}
              style={{ ...inputStyle, width: '150px' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>Min $</label>
            <input
              type="number"
              value={filters.amount_min ?? ''}
              onChange={e => onFilterChange({ amount_min: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
              placeholder="0"
              style={{ ...inputStyle, width: '100px' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>Max $</label>
            <input
              type="number"
              value={filters.amount_max ?? ''}
              onChange={e => onFilterChange({ amount_max: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
              placeholder="any"
              style={{ ...inputStyle, width: '100px' }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

/* ---- Pagination ---- */

function Pagination({ page, totalPages, onPageChange }: {
  page: number; totalPages: number; onPageChange: (p: number) => void
}) {
  if (totalPages <= 1) return null

  const btnStyle = (active: boolean): React.CSSProperties => ({
    padding: '6px 12px', fontSize: '12px', fontWeight: active ? 700 : 500,
    borderRadius: 'var(--radius)',
    border: active ? '1px solid var(--accent)' : '1px solid var(--border)',
    cursor: active ? 'default' : 'pointer',
    background: active ? 'color-mix(in srgb, var(--accent) 15%, transparent)' : 'transparent',
    color: active ? 'var(--accent)' : 'var(--text-muted)',
  })

  const pages: number[] = []
  const start = Math.max(1, page - 2)
  const end = Math.min(totalPages, page + 2)
  for (let i = start; i <= end; i++) pages.push(i)

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', padding: '12px 0' }}>
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        style={{ ...btnStyle(false), opacity: page <= 1 ? 0.4 : 1, cursor: page <= 1 ? 'default' : 'pointer' }}
      >
        &larr; Prev
      </button>
      {start > 1 && <span style={{ color: 'var(--text-muted)', fontSize: '12px', padding: '0 4px' }}>...</span>}
      {pages.map(p => (
        <button key={p} onClick={() => onPageChange(p)} style={btnStyle(p === page)}>
          {p}
        </button>
      ))}
      {end < totalPages && <span style={{ color: 'var(--text-muted)', fontSize: '12px', padding: '0 4px' }}>...</span>}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        style={{ ...btnStyle(false), opacity: page >= totalPages ? 0.4 : 1, cursor: page >= totalPages ? 'default' : 'pointer' }}
      >
        Next &rarr;
      </button>
    </div>
  )
}

/* ---- Transaction Table ---- */

type SortKey = 'date' | 'payee' | 'amount' | 'category'

interface TransactionTableProps {
  transactions: TransactionRow[]
  selectedIds: Set<string>
  onToggleSelect: (id: string) => void
  onToggleAll: () => void
  allSelected: boolean
  sortBy: string
  sortDir: string
  onSort: (key: SortKey) => void
  editingId: string | null
  onEditingChange: (id: string | null) => void
  onPayeeClick?: (payee: string) => void
}

function TransactionTable({
  transactions, selectedIds, onToggleSelect, onToggleAll, allSelected,
  sortBy, sortDir, onSort, editingId, onEditingChange, onPayeeClick,
}: TransactionTableProps) {
  const recategorize = useRecategorize()
  const { data: catData } = useCategories()
  const { toast } = useToast()

  const catNames = useMemo(() => {
    const map: Record<string, string> = {}
    for (const c of catData?.categories ?? []) map[c.id] = c.name
    return map
  }, [catData])

  const columns: { label: string; key: SortKey | null; align: string; width?: string }[] = [
    { label: '', key: null, align: 'center', width: '40px' },
    { label: 'Date', key: 'date', align: 'left' },
    { label: 'Payee', key: 'payee', align: 'left' },
    { label: 'Category', key: 'category', align: 'left' },
    { label: 'Amount', key: 'amount', align: 'right' },
    { label: 'Memo', key: null, align: 'left' },
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
                onClick={col.key ? () => onSort(col.key!) : i === 0 ? onToggleAll : undefined}
                style={{
                  padding: '10px 12px',
                  textAlign: col.align as CanvasTextAlign,
                  fontSize: '10px', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                  whiteSpace: 'nowrap', width: col.width,
                  color: sortBy === col.key ? 'var(--accent)' : 'var(--text-muted)',
                  cursor: col.key || i === 0 ? 'pointer' : 'default',
                  userSelect: 'none',
                }}
              >
                {i === 0 ? (
                  <input
                    type="checkbox"
                    checked={allSelected && transactions.length > 0}
                    onChange={onToggleAll}
                    style={{ cursor: 'pointer', accentColor: 'var(--accent)' }}
                  />
                ) : (
                  <>
                    {col.label}
                    {sortBy === col.key && (
                      <span style={{ marginLeft: '4px', fontSize: '9px' }}>
                        {sortDir === 'asc' ? '\u25B2' : '\u25BC'}
                      </span>
                    )}
                  </>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {transactions.map(t => (
            <tr
              key={t.id}
              style={{
                borderBottom: '1px solid var(--border)',
                background: selectedIds.has(t.id) ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent',
              }}
              onMouseEnter={e => {
                if (!selectedIds.has(t.id))
                  for (const td of e.currentTarget.children as any) td.style.background = 'var(--bg-hover)'
              }}
              onMouseLeave={e => {
                const bg = selectedIds.has(t.id) ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent'
                for (const td of e.currentTarget.children as any) td.style.background = bg
              }}
            >
              <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                <input
                  type="checkbox"
                  checked={selectedIds.has(t.id)}
                  onChange={() => onToggleSelect(t.id)}
                  style={{ cursor: 'pointer', accentColor: 'var(--accent)' }}
                />
              </td>
              <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
                {formatDate(t.date)}
              </td>
              <td style={{ padding: '10px 12px', fontWeight: 500, color: 'var(--text-primary)' }}>
                {onPayeeClick && t.payee_name ? (
                  <span
                    onClick={() => onPayeeClick(t.payee_name!)}
                    style={{ cursor: 'pointer', borderBottom: '1px dashed var(--text-muted)' }}
                    onMouseEnter={e => { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)' }}
                    onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--text-muted)' }}
                  >
                    {t.payee_name}
                  </span>
                ) : (
                  t.payee_name || 'Unknown'
                )}
              </td>
              <td style={{
                padding: '10px 12px', fontSize: '12px', position: 'relative',
                color: t.category_name ? 'var(--text-muted)' : 'var(--warning, #f59e0b)',
              }}>
                <span
                  onClick={() => onEditingChange(editingId === t.id ? null : t.id)}
                  style={{ cursor: 'pointer', borderBottom: '1px dashed currentColor' }}
                  title="Click to re-categorize"
                >
                  {t.category_name || 'Uncategorized'}
                </span>
                {editingId === t.id && (
                  <CategoryPickerInline
                    onSelect={(categoryId) => {
                      const name = catNames[categoryId] || 'new category'
                      recategorize.mutate(
                        { transaction_id: t.id, category_id: categoryId },
                        { onSuccess: () => toast(`"${t.payee_name}" → ${name}`, 'success') },
                      )
                      onEditingChange(null)
                    }}
                    onCancel={() => onEditingChange(null)}
                  />
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
                padding: '10px 12px', color: 'var(--text-muted)', fontSize: '12px',
                maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {t.memo || '—'}
              </td>
              <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', textAlign: 'right' }}>
                <button
                  onClick={() => onEditingChange(editingId === t.id ? null : t.id)}
                  style={{
                    padding: '3px 8px', fontSize: '11px', fontWeight: 600,
                    borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                    cursor: 'pointer', background: 'transparent', color: 'var(--accent)',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  Re-cat
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ---- Bulk Action Bar ---- */

function BulkActionBar({ count, onRecategorize, onClear }: {
  count: number; onRecategorize: () => void; onClear: () => void
}) {
  if (count === 0) return null

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '12px',
      padding: '10px 20px',
      background: 'color-mix(in srgb, var(--accent) 10%, var(--bg-card))',
      borderRadius: 'var(--radius)',
      border: '1px solid color-mix(in srgb, var(--accent) 30%, transparent)',
    }}>
      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent)' }}>
        {count} selected
      </span>
      <button
        onClick={onRecategorize}
        style={{
          padding: '6px 14px', fontSize: '12px', fontWeight: 600,
          borderRadius: 'var(--radius)', border: 'none',
          cursor: 'pointer', background: 'var(--accent)', color: '#fff',
        }}
      >
        Re-categorize Selected
      </button>
      <button
        onClick={onClear}
        style={{
          padding: '6px 14px', fontSize: '12px', fontWeight: 600,
          borderRadius: 'var(--radius)', border: '1px solid var(--border)',
          cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
        }}
      >
        Clear
      </button>
    </div>
  )
}

/* ---- Main Component ---- */

interface TransactionExplorerProps {
  onBack: () => void
  initialPayee?: string
}

export default function TransactionExplorer({ onBack, initialPayee }: TransactionExplorerProps) {
  const [filters, setFilters] = useState<TransactionFilters>({
    payee: initialPayee,
    sort_by: 'date',
    sort_dir: 'desc',
    page: 1,
    page_size: 50,
  })
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [bulkPickerOpen, setBulkPickerOpen] = useState(false)
  const bulkPickerRef = useRef<HTMLDivElement>(null)

  const { data, isLoading } = useTransactionSearch(filters)
  const { data: catData } = useCategories()
  const bulkRecategorize = useBulkRecategorize()
  const { toast } = useToast()

  const categories = catData?.categories ?? []
  const transactions = data?.transactions ?? []

  const updateFilters = useCallback((updates: Partial<TransactionFilters>) => {
    setFilters(prev => ({ ...prev, ...updates }))
    setSelectedIds(new Set())
  }, [])

  const handleSort = useCallback((key: SortKey) => {
    setFilters(prev => ({
      ...prev,
      sort_by: key,
      sort_dir: prev.sort_by === key && prev.sort_dir === 'desc' ? 'asc' : 'desc',
      page: 1,
    }))
  }, [])

  const handlePayeeClick = useCallback((payee: string) => {
    setFilters(prev => ({
      ...prev,
      payee,
      page: 1,
    }))
  }, [])

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }, [])

  const toggleAll = useCallback(() => {
    setSelectedIds(prev =>
      prev.size === transactions.length
        ? new Set()
        : new Set(transactions.map(t => t.id))
    )
  }, [transactions])

  const handleBulkRecategorize = useCallback((categoryId: string) => {
    const ids = [...selectedIds]
    const catName = categories.find(c => c.id === categoryId)?.name ?? 'new category'
    bulkRecategorize.mutate(
      { transaction_ids: ids, category_id: categoryId },
      {
        onSuccess: (res: any) => {
          toast(`${res.updated} transactions → ${catName}`, 'success')
          setSelectedIds(new Set())
          setBulkPickerOpen(false)
        },
        onError: () => toast('Bulk re-categorize failed', 'error'),
      },
    )
  }, [selectedIds, categories, bulkRecategorize, toast])

  useEffect(() => {
    if (!bulkPickerOpen) return
    const handler = (e: MouseEvent) => {
      if (bulkPickerRef.current && !bulkPickerRef.current.contains(e.target as Node))
        setBulkPickerOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [bulkPickerOpen])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
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
        Dashboard
      </button>

      {/* Title */}
      <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
        Transaction Explorer
      </h2>

      {/* Filter bar */}
      <FilterBar filters={filters} onFilterChange={updateFilters} categories={categories} />

      {/* Payee summary */}
      {filters.payee && filters.payee.length >= 2 && (
        <PayeeSummaryHeader payee={filters.payee} />
      )}

      {/* Bulk action bar */}
      <div style={{ position: 'relative' }}>
        <BulkActionBar
          count={selectedIds.size}
          onRecategorize={() => setBulkPickerOpen(true)}
          onClear={() => setSelectedIds(new Set())}
        />
        {bulkPickerOpen && (
          <div ref={bulkPickerRef} style={{ position: 'absolute', top: '100%', left: '120px', zIndex: 30 }}>
            <CategoryPickerInline
              onSelect={handleBulkRecategorize}
              onCancel={() => setBulkPickerOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Results summary */}
      {data && !isLoading && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 4px', fontSize: '12px', color: 'var(--text-muted)',
        }}>
          <span>
            {data.total_count.toLocaleString()} transaction{data.total_count !== 1 ? 's' : ''}
            {' '}&middot;{' '}
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {formatCurrency(data.total_amount)}
            </span>
            {' '}total
          </span>
          <span>
            Page {data.page} of {data.total_pages}
          </span>
        </div>
      )}

      {/* Table */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      }}>
        {isLoading && !data ? (
          <ExplorerSkeleton />
        ) : transactions.length === 0 ? (
          <div style={{
            padding: '48px 24px', textAlign: 'center',
            color: 'var(--text-muted)', fontSize: '14px',
          }}>
            No transactions found matching your filters.
          </div>
        ) : (
          <TransactionTable
            transactions={transactions}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onToggleAll={toggleAll}
            allSelected={selectedIds.size === transactions.length && transactions.length > 0}
            sortBy={filters.sort_by ?? 'date'}
            sortDir={filters.sort_dir ?? 'desc'}
            onSort={handleSort}
            editingId={editingId}
            onEditingChange={setEditingId}
            onPayeeClick={handlePayeeClick}
          />
        )}
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          onPageChange={(p) => updateFilters({ page: p })}
        />
      )}
    </div>
  )
}
