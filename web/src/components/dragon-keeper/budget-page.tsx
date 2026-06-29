import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { useBudget, useUpdateBudgetTarget, useUpdateBudgetIncome, type BudgetCategory } from '../../hooks/dragon-keeper/use-budget'
import Sparkline, { type SparklinePoint } from './sparkline'
import { useLocalStorage } from '../../hooks/use-local-storage'

type SortMode = 'alpha' | 'amount' | 'budgeted'
type FilterMode = 'all' | 'active'
type GroupMode = 'grouped' | 'flat'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function fmtAvg(n: number) {
  if (n === 0) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(n)
}

function fmtHours(n: number) {
  if (n <= 0) return '—'
  return n < 0.1 ? '<0.1h' : `${n.toFixed(1)}h`
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span style={{ minWidth: 56, display: 'inline-block' }} />
  const up = delta > 0
  return (
    <span style={{
      fontSize: '11px', fontWeight: 600,
      color: up ? 'var(--error)' : 'var(--success)',
      minWidth: 56, textAlign: 'right', display: 'inline-block',
      fontVariantNumeric: 'tabular-nums',
    }}>
      {up ? '▲' : '▼'} {Math.abs(delta).toFixed(1)}%
    </span>
  )
}

function InlineNumberEdit({
  value, placeholder, onSave,
}: {
  value: number | null
  placeholder?: string
  onSave: (v: number | null) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  const commit = () => {
    const trimmed = draft.trim()
    if (trimmed === '') {
      onSave(null)
    } else {
      const n = parseFloat(trimmed)
      if (!isNaN(n)) onSave(n)
    }
    setEditing(false)
  }

  if (!editing) {
    return (
      <button
        onClick={(e) => { e.stopPropagation(); setDraft(value?.toString() ?? ''); setEditing(true) }}
        style={{
          background: 'none', border: '1px dashed transparent', cursor: 'pointer',
          color: value != null ? 'var(--text-primary)' : 'var(--text-muted)',
          padding: '2px 6px', fontFamily: 'inherit', fontSize: 'inherit',
          borderRadius: '4px', textAlign: 'right', width: '100%',
          fontVariantNumeric: 'tabular-nums',
        }}
        title="Click to set budget"
      >
        {value != null ? fmt(value) : (placeholder ?? '—')}
      </button>
    )
  }

  return (
    <input
      autoFocus
      type="number"
      step="1"
      min="0"
      value={draft}
      onChange={e => setDraft(e.target.value)}
      onClick={e => e.stopPropagation()}
      onBlur={commit}
      onKeyDown={e => {
        if (e.key === 'Enter') commit()
        if (e.key === 'Escape') setEditing(false)
      }}
      style={{ width: '80px', padding: '2px 6px', fontSize: 'inherit', fontFamily: 'inherit', textAlign: 'right' }}
    />
  )
}

function CategoryRow({ cat, showGroup, indent, hourlyRate, onCategoryClick, onTargetSave }: {
  cat: BudgetCategory
  showGroup: boolean
  indent: boolean
  hourlyRate: number
  onCategoryClick?: (id: string) => void
  onTargetSave: (categoryId: string, amount: number | null) => void
}) {
  const [hovered, setHovered] = useState(false)
  const points: SparklinePoint[] = cat.periods.map(p => ({ date: p.period_start, value: p.total }))

  return (
    <div
      onClick={() => onCategoryClick?.(cat.category_id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: `8px 16px 8px ${indent ? 32 : 16}px`,
        borderBottom: '1px solid var(--border)',
        opacity: cat.has_activity ? 1 : 0.45,
        cursor: onCategoryClick ? 'pointer' : 'default',
        background: hovered && onCategoryClick ? 'var(--bg-hover)' : 'transparent',
        transition: 'background 0.15s',
      }}
    >
      <div style={{ width: 180, minWidth: 180 }}>
        <div style={{
          fontSize: '13px', fontWeight: 500,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          color: 'var(--text-primary)',
        }}>
          {cat.category_name}
        </div>
        {cat.cancelled_subscriptions.length > 0 && (
          <div
            style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}
            title={cat.cancelled_subscriptions.join(', ')}
          >
            cancelled: {cat.cancelled_subscriptions.join(', ')}
          </div>
        )}
      </div>

      {showGroup && (
        <div style={{
          width: 140, minWidth: 140,
          fontSize: '12px', color: 'var(--text-muted)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {cat.group_name}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', minWidth: 80 }}>
        {cat.has_activity
          ? <Sparkline points={points} />
          : <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>no activity</span>
        }
      </div>

      <div style={{ width: 80, textAlign: 'right', fontSize: '13px', color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
        {fmtAvg(cat.weekly_avg)}
      </div>

      <div style={{ width: 56, textAlign: 'right', fontSize: '12px', color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
        {hourlyRate > 0 ? fmtHours(cat.weekly_avg / hourlyRate) : '—'}
      </div>

      <div style={{ width: 88, textAlign: 'right', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
        {cat.grand_total > 0 ? fmt(cat.grand_total) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
      </div>

      <DeltaBadge delta={cat.delta_pct} />

      <div style={{ width: 96, textAlign: 'right' }} onClick={e => e.stopPropagation()}>
        <InlineNumberEdit
          value={cat.budget_target}
          placeholder="Set budget"
          onSave={amount => onTargetSave(cat.category_id, amount)}
        />
      </div>
    </div>
  )
}

function GroupSection({ groupName, categories, defaultOpen, hourlyRate, onCategoryClick, onTargetSave }: {
  groupName: string
  categories: BudgetCategory[]
  defaultOpen: boolean
  hourlyRate: number
  onCategoryClick?: (id: string) => void
  onTargetSave: (categoryId: string, amount: number | null) => void
}) {
  const [open, setOpen] = useState(defaultOpen)
  const groupTotal = categories.reduce((s, c) => s + c.grand_total, 0)
  const groupBudget = categories.reduce((s, c) => s + (c.budget_target ?? 0), 0)
  const activeCount = categories.filter(c => c.has_activity).length

  return (
    <div style={{ marginBottom: 4 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          width: '100%', padding: '10px 16px',
          background: 'var(--bg-secondary)', border: 'none',
          borderBottom: '1px solid var(--border)',
          cursor: 'pointer', textAlign: 'left',
        }}
      >
        {open ? <ChevronDown size={13} color="var(--text-muted)" /> : <ChevronRight size={13} color="var(--text-muted)" />}
        <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', flex: 1 }}>
          {groupName}
        </span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {activeCount}/{categories.length} active
        </span>
        {groupTotal > 0 && (
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginLeft: 12, fontVariantNumeric: 'tabular-nums' }}>
            {fmt(groupTotal)}
          </span>
        )}
        {groupBudget > 0 && (
          <span style={{ fontSize: '12px', color: 'var(--accent)', marginLeft: 8, fontVariantNumeric: 'tabular-nums' }}>
            / {fmt(groupBudget)}
          </span>
        )}
      </button>

      {open && categories.map(cat => (
        <CategoryRow
          key={cat.category_id}
          cat={cat}
          showGroup={false}
          indent={true}
          hourlyRate={hourlyRate}
          onCategoryClick={onCategoryClick}
          onTargetSave={onTargetSave}
        />
      ))}
    </div>
  )
}

function RemainingHeader({ perPeriodIncome, totalBudgeted, onIncomeSave }: {
  perPeriodIncome: number
  totalBudgeted: number
  onIncomeSave: (v: number) => void
}) {
  const remaining = perPeriodIncome - totalBudgeted
  const hourlyRate = perPeriodIncome / 40
  const pct = perPeriodIncome > 0 ? Math.min(100, (totalBudgeted / perPeriodIncome) * 100) : 0

  return (
    <div style={{
      padding: '16px', marginBottom: 16,
      background: 'var(--bg-secondary)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
    }}>
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 4 }}>Per-period income</div>
          <div style={{ fontSize: '20px', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
            <InlineNumberEdit value={perPeriodIncome || null} placeholder="Set income" onSave={v => onIncomeSave(v ?? 0)} />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>click to edit</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 4 }}>Budgeted</div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
            {fmt(totalBudgeted)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 4 }}>Remaining</div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: remaining >= 0 ? 'var(--success)' : 'var(--error)', fontVariantNumeric: 'tabular-nums' }}>
            {fmt(remaining)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 4 }}>Hourly rate</div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
            {hourlyRate > 0 ? fmtAvg(hourlyRate) : '—'}
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 160, alignSelf: 'center' }}>
          <div style={{ height: 8, background: 'var(--border)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 4,
              width: `${pct}%`,
              background: pct > 100 ? 'var(--error)' : pct > 80 ? 'var(--warning, #f59e0b)' : 'var(--accent)',
              transition: 'width 0.3s',
            }} />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 4 }}>
            {pct.toFixed(0)}% allocated
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BudgetPage({ onCategoryClick }: { onCategoryClick?: (id: string) => void }) {
  const { data, isLoading, isError, error } = useBudget()
  const updateTarget = useUpdateBudgetTarget()
  const updateIncome = useUpdateBudgetIncome()

  const [filterMode, setFilterMode] = useLocalStorage<FilterMode>('dk-budget-filter', 'all')
  const [sortMode, setSortMode] = useLocalStorage<SortMode>('dk-budget-sort', 'amount')
  const [groupMode, setGroupMode] = useLocalStorage<GroupMode>('dk-budget-group', 'grouped')

  const categories = data?.categories ?? []

  const filtered = useMemo(() =>
    filterMode === 'active' ? categories.filter(c => c.has_activity) : categories,
    [categories, filterMode],
  )

  const budgetSortKey = (c: BudgetCategory) => c.budget_target ?? c.weekly_avg

  const sortByBudgeted = (a: BudgetCategory, b: BudgetCategory) => {
    const aHas = a.budget_target !== null
    const bHas = b.budget_target !== null
    if (aHas !== bHas) return aHas ? -1 : 1
    return budgetSortKey(b) - budgetSortKey(a)
  }

  const sorted = useMemo(() => {
    if (sortMode === 'alpha') return [...filtered].sort((a, b) => a.category_name.localeCompare(b.category_name))
    if (sortMode === 'budgeted') return [...filtered].sort(sortByBudgeted)
    return [...filtered].sort((a, b) => b.grand_total - a.grand_total)
  }, [filtered, sortMode])

  const grouped = useMemo(() => {
    const byGroup = new Map<string, BudgetCategory[]>()
    for (const cat of filtered) {
      if (!byGroup.has(cat.group_name)) byGroup.set(cat.group_name, [])
      byGroup.get(cat.group_name)!.push(cat)
    }
    const sortCats = (cats: BudgetCategory[]) => {
      if (sortMode === 'alpha') return [...cats].sort((a, b) => a.category_name.localeCompare(b.category_name))
      if (sortMode === 'budgeted') return [...cats].sort(sortByBudgeted)
      return [...cats].sort((a, b) => b.grand_total - a.grand_total)
    }
    const groups = Array.from(byGroup.entries()).map(([name, cats]) => ({
      name,
      categories: sortCats(cats),
      total: cats.reduce((s, c) => s + c.grand_total, 0),
      budgetTotal: cats.reduce((s, c) => s + budgetSortKey(c), 0),
    }))
    if (sortMode === 'alpha') return groups.sort((a, b) => a.name.localeCompare(b.name))
    if (sortMode === 'budgeted') return groups.sort((a, b) => b.budgetTotal - a.budgetTotal)
    return groups.sort((a, b) => b.total - a.total)
  }, [filtered, sortMode])

  const totalSpend = useMemo(() => categories.reduce((s, c) => s + c.grand_total, 0), [categories])
  const totalBudgeted = useMemo(() => categories.reduce((s, c) => s + (c.budget_target ?? 0), 0), [categories])
  const activeCount = useMemo(() => categories.filter(c => c.has_activity).length, [categories])
  const hourlyRate = (data?.per_period_income ?? 0) / 40

  const handleTargetSave = (categoryId: string, amount: number | null) => {
    updateTarget.mutate({ category_id: categoryId, amount })
  }

  if (isLoading) return <div className="info-box">Loading budget data…</div>
  if (isError) return <div className="error-box">Failed to load budget data{error?.message ? `: ${error.message}` : ''}.</div>
  if (!data || categories.length === 0) return <div className="info-box">No category data found. Sync from YNAB first.</div>

  return (
    <div>
      <RemainingHeader
        perPeriodIncome={data.per_period_income}
        totalBudgeted={totalBudgeted}
        onIncomeSave={amount => updateIncome.mutate(amount)}
      />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px' }}>Budget</h2>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 3 }}>
            {activeCount} of {categories.length} categories active · {fmt(totalSpend)} over 52 weeks · <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{fmtAvg(totalSpend / 52)}/wk avg</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {(['all', 'active'] as FilterMode[]).map(f => (
            <button key={f} onClick={() => setFilterMode(f)}
              className={`btn btn-ghost${filterMode === f ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}>
              {f === 'all' ? 'All' : 'Active only'}
            </button>
          ))}
          <div style={{ width: 1, background: 'var(--border)', margin: '0 4px' }} />
          {(['grouped', 'flat'] as GroupMode[]).map(g => (
            <button key={g} onClick={() => setGroupMode(g)}
              className={`btn btn-ghost${groupMode === g ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}>
              {g === 'grouped' ? 'Grouped' : 'Flat'}
            </button>
          ))}
          <div style={{ width: 1, background: 'var(--border)', margin: '0 4px' }} />
          {([['alpha', 'A–Z'], ['amount', 'By amount'], ['budgeted', 'By budget']] as [SortMode, string][]).map(([s, label]) => (
            <button key={s} onClick={() => setSortMode(s)}
              className={`btn btn-ghost${sortMode === s ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Column headers */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: `6px 16px 6px ${groupMode === 'grouped' ? 32 : 16}px`,
        fontSize: '11px', color: 'var(--text-muted)',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ width: 180, minWidth: 180 }}>Category</div>
        {groupMode === 'flat' && <div style={{ width: 140, minWidth: 140 }}>Group</div>}
        <div style={{ flex: 1, textAlign: 'center', minWidth: 80 }}>52-week trend</div>
        <div style={{ width: 80, textAlign: 'right' }}>Avg/wk</div>
        <div style={{ width: 56, textAlign: 'right' }}>Hrs/wk</div>
        <div style={{ width: 88, textAlign: 'right' }}>52wk total</div>
        <div style={{ width: 56, textAlign: 'right' }}>Δ wk</div>
        <div style={{ width: 96, textAlign: 'right' }}>Budget</div>
      </div>

      {groupMode === 'grouped'
        ? grouped.map(group => (
            <GroupSection
              key={group.name}
              groupName={group.name}
              categories={group.categories}
              defaultOpen={group.total > 0}
              hourlyRate={hourlyRate}
              onCategoryClick={onCategoryClick}
              onTargetSave={handleTargetSave}
            />
          ))
        : sorted.map(cat => (
            <CategoryRow
              key={cat.category_id}
              cat={cat}
              showGroup={true}
              indent={false}
              hourlyRate={hourlyRate}
              onCategoryClick={onCategoryClick}
              onTargetSave={handleTargetSave}
            />
          ))
      }
    </div>
  )
}
