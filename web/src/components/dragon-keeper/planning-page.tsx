import { useMemo, useState } from 'react'
import { ChevronUp, ChevronDown, ExternalLink, Check } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine } from 'recharts'
import {
  usePlanning,
  usePlanningUpdateCost,
  usePlanningUpdatePurchaseDate,
  usePlanningMovePurchase,
  usePlanningUpdateSavings,
  usePlanningUpdatePeriod,
  usePlanningUpdateCompletedDate,
  usePlanningMarkAsDone,
  usePlanningUpdateActualSavings,
  usePlanningMoveSavings,
  usePlanningUpdateCurrentValue,
  usePlanningUpdateSoldDate,
  usePlanningMoveSelling,
  type PlanningItem,
  type PlanningType,
  type PlanningData,
} from '../../hooks/dragon-keeper/use-planning'
import { useSavingsOpportunities } from '../../hooks/dragon-keeper/use-savings-opportunities'
import type { SavingsPeriod } from '../../hooks/dragon-keeper/use-savings-opportunities'

const TYPE_LABELS: Record<PlanningType, string> = {
  purchase: 'Purchase',
  savings: 'Savings',
  selling: 'Selling',
}

const TYPE_COLORS: Record<PlanningType, string> = {
  purchase: '#ef4444',
  savings: '#10b981',
  selling: '#06b6d4',
}

const STATUS_COLORS: Record<string, string> = {
  considering: 'var(--text-muted)',
  approved: 'var(--accent)',
  purchased: 'var(--success)',
  done: 'var(--success)',
  sold: 'var(--success)',
  dropped: 'var(--text-muted)',
}

function fmt(n: number | null) {
  if (n == null) return '—'
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function isActive(status: string) {
  return status === 'considering' || status === 'approved'
}

function completedYear(date: string | null | undefined): number | null {
  if (!date) return null
  const y = parseInt(date.slice(0, 4), 10)
  return isNaN(y) ? null : y
}

function InlineNumberEdit({ value, onSave }: { value: number | null; onSave: (v: number) => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  if (!editing) {
    return (
      <button onClick={() => { setDraft(value?.toString() ?? ''); setEditing(true) }}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', padding: 0, fontFamily: 'inherit', fontSize: 'inherit' }}>
        {fmt(value)}
      </button>
    )
  }
  return (
    <input autoFocus type="number" step="0.01" value={draft} onChange={e => setDraft(e.target.value)}
      onBlur={() => { const n = parseFloat(draft); if (!isNaN(n)) onSave(n); setEditing(false) }}
      onKeyDown={e => {
        if (e.key === 'Enter') { const n = parseFloat(draft); if (!isNaN(n)) onSave(n); setEditing(false) }
        if (e.key === 'Escape') setEditing(false)
      }}
      style={{ width: '90px', padding: '2px 6px', fontSize: 'inherit', fontFamily: 'inherit' }}
    />
  )
}

function InlinePeriodSelect({ value, onSave }: { value: SavingsPeriod; onSave: (v: SavingsPeriod) => void }) {
  return (
    <select value={value} onChange={e => onSave(e.target.value as SavingsPeriod)}
      style={{ padding: '2px 4px', fontSize: 'inherit', fontFamily: 'inherit', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '4px' }}>
      <option value="one-time">One-time</option>
      <option value="monthly">Monthly</option>
      <option value="yearly">Yearly</option>
    </select>
  )
}

function InlineDateEdit({ value, onSave }: { value: string | null; onSave: (v: string | null) => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  if (!editing) {
    return (
      <button onClick={() => { setDraft(value ?? ''); setEditing(true) }}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: value ? 'var(--text-primary)' : 'var(--text-muted)', padding: 0, fontFamily: 'inherit', fontSize: 'inherit' }}>
        {value || 'Set date'}
      </button>
    )
  }
  return (
    <input autoFocus type="date" value={draft} onChange={e => setDraft(e.target.value)}
      onBlur={() => { onSave(draft || null); setEditing(false) }}
      onKeyDown={e => {
        if (e.key === 'Enter') { onSave(draft || null); setEditing(false) }
        if (e.key === 'Escape') setEditing(false)
      }}
      style={{ padding: '2px 6px', fontSize: 'inherit', fontFamily: 'inherit' }}
    />
  )
}

function SummaryBar({ summary, maxCcRate }: { summary: PlanningData['summary']; maxCcRate: number | null }) {
  return (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
      {[
        { label: 'True cost (purchases)', value: summary.true_cost_out, color: 'var(--error)' },
        { label: 'True savings', value: summary.true_savings_in, color: 'var(--success)' },
        { label: 'Sale proceeds', value: summary.true_sale_proceeds, color: 'var(--success)' },
        { label: 'Net true impact', value: summary.net_true_impact, color: summary.net_true_impact >= 0 ? 'var(--success)' : 'var(--error)' },
      ].map(card => (
        <div key={card.label} style={{
          flex: '1 1 140px', padding: '12px 14px', background: 'var(--bg-secondary)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius)',
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 4 }}>{card.label}</div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: card.color, fontVariantNumeric: 'tabular-nums' }}>
            {card.value >= 0 && card.label === 'Net true impact' ? '+' : ''}{fmt(card.value)}
            {(card.label === 'True cost (purchases)' || card.label === 'True savings') ? '/yr' : ''}
          </div>
        </div>
      ))}
      {maxCcRate != null && (
        <div style={{ flex: '1 1 100%', fontSize: '11px', color: 'var(--text-muted)' }}>
          True impact calculated at {maxCcRate}% APR (highest CC rate)
        </div>
      )}
    </div>
  )
}

function RealizedSavingsSummary({
  totalRealized,
  realizedByYear,
  doneCount,
  yearFilter,
  onYearFilterChange,
}: {
  totalRealized: number
  realizedByYear: Record<string, number>
  doneCount: number
  yearFilter: string
  onYearFilterChange: (year: string) => void
}) {
  if (doneCount === 0) return null

  const years = Object.keys(realizedByYear).sort((a, b) => parseInt(b) - parseInt(a))
  const filteredTotal = yearFilter === 'all' ? totalRealized : (realizedByYear[yearFilter] ?? 0)

  return (
    <div style={{
      marginBottom: 16, padding: '12px 14px', background: 'var(--bg-secondary)',
      border: '1px solid var(--border)', borderRadius: 'var(--radius)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
    }}>
      <div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 4 }}>Realized savings</div>
        <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--success)', fontVariantNumeric: 'tabular-nums' }}>
          {fmt(filteredTotal)}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>
          from {doneCount} completed {doneCount === 1 ? 'action' : 'actions'}
          {yearFilter !== 'all' && ` in ${yearFilter}`}
        </div>
      </div>
      {years.length > 0 && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {['all', ...years].map(y => (
            <button key={y} onClick={() => onYearFilterChange(y)}
              className={`btn btn-ghost${yearFilter === y ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}>
              {y === 'all' ? 'All' : y}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function truncateLabel(s: string, max = 32) {
  return s.length > max ? s.slice(0, max - 1) + '…' : s
}

function ImpactChart({ items }: { items: PlanningItem[] }) {
  const data = useMemo(
    () => items
      .filter(i => isActive(i.status) && (i.true_impact ?? 0) !== 0)
      .map(i => {
        const impact = i.true_impact!
        const signed = i.direction === 'out' ? -impact : impact
        return {
          label: truncateLabel(i.title),
          fullLabel: `${TYPE_LABELS[i.type]}: ${i.title}`,
          value: signed,
          type: i.type,
        }
      })
      .sort((a, b) => a.value - b.value),
    [items],
  )

  if (data.length === 0) return null

  const chartHeight = Math.max(220, data.length * 36 + 48)

  return (
    <div style={{ marginBottom: 20, padding: '16px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ fontSize: '13px', fontWeight: 600 }}>True Impact by Item (active)</div>
        <div style={{ display: 'flex', gap: 12, fontSize: '11px', color: 'var(--text-muted)' }}>
          <span><span style={{ color: '#ef4444' }}>◀</span> Purchases (cost)</span>
          <span>Savings &amp; sales (benefit) <span style={{ color: '#10b981' }}>▶</span></span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart layout="vertical" data={data} margin={{ top: 4, right: 24, left: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            tickFormatter={(v: number) => fmt(Math.abs(v))}
          />
          <YAxis
            type="category"
            dataKey="label"
            width={160}
            tick={{ fontSize: 11, fill: 'var(--text-primary)' }}
          />
          <ReferenceLine x={0} stroke="var(--text-muted)" strokeWidth={1.5} />
          <Tooltip
            formatter={(value: number) => [fmt(Math.abs(value)), value < 0 ? 'Cost' : 'Benefit']}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel ?? ''}
            contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', fontSize: '12px' }}
          />
          <Bar dataKey="value" radius={4} maxBarSize={22}>
            {data.map((d, i) => (
              <Cell key={i} fill={TYPE_COLORS[d.type]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function PlanningRow({
  item, isFirst, isLast, onMove, markingDoneFilename,
}: {
  item: PlanningItem
  isFirst: boolean
  isLast: boolean
  onMove: (direction: 'up' | 'down') => void
  markingDoneFilename: string | null
}) {
  const updateCost = usePlanningUpdateCost()
  const updatePurchaseDate = usePlanningUpdatePurchaseDate()
  const updateSavings = usePlanningUpdateSavings()
  const updatePeriod = usePlanningUpdatePeriod()
  const updateCompletedDate = usePlanningUpdateCompletedDate()
  const markAsDone = usePlanningMarkAsDone()
  const updateActualSavings = usePlanningUpdateActualSavings()
  const updateCurrentValue = usePlanningUpdateCurrentValue()
  const updateSoldDate = usePlanningUpdateSoldDate()

  const impactColor = item.direction === 'out' ? 'var(--error)' : 'var(--success)'
  const interestDelta = item.true_impact != null && item.impact != null && item.type !== 'purchase'
    ? item.true_impact - item.impact
    : item.type === 'purchase' && item.true_impact != null && item.cost != null
      ? item.true_impact - item.cost
      : null

  return (
    <tr>
      <td style={{ width: 56, textAlign: 'center', padding: '6px 0' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <button onClick={() => onMove('up')} disabled={isFirst} title="Move up"
            style={{ background: 'none', border: 'none', cursor: isFirst ? 'default' : 'pointer', padding: '1px 4px', color: isFirst ? 'var(--border)' : 'var(--text-muted)' }}>
            <ChevronUp size={14} />
          </button>
          <button onClick={() => onMove('down')} disabled={isLast} title="Move down"
            style={{ background: 'none', border: 'none', cursor: isLast ? 'default' : 'pointer', padding: '1px 4px', color: isLast ? 'var(--border)' : 'var(--text-muted)' }}>
            <ChevronDown size={14} />
          </button>
        </div>
      </td>
      <td style={{ padding: '8px 12px' }}>
        <span style={{ fontSize: '11px', fontWeight: 600, color: TYPE_COLORS[item.type], textTransform: 'uppercase' }}>
          {TYPE_LABELS[item.type]}
        </span>
      </td>
      <td style={{ padding: '8px 12px' }}>
        <div style={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6 }}>
          {item.title}
          {item.url && (
            <a href={item.url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-muted)' }}>
              <ExternalLink size={11} />
            </a>
          )}
        </div>
        {item.category && <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>{item.category}</div>}
        {item.type === 'selling' && (item.brand || item.model) && (
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>{[item.brand, item.model].filter(Boolean).join(' ')}</div>
        )}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {item.type === 'purchase' && <InlineNumberEdit value={item.cost ?? null} onSave={cost => updateCost.mutate({ filename: item.filename, cost })} />}
        {item.type === 'savings' && <InlineNumberEdit value={item.savings ?? null} onSave={savings => updateSavings.mutate({ filename: item.filename, savings })} />}
        {item.type === 'selling' && <InlineNumberEdit value={item.current_value ?? null} onSave={v => updateCurrentValue.mutate({ filename: item.filename, current_value: v })} />}
      </td>
      <td style={{ padding: '8px 12px' }}>
        {item.type === 'savings' && item.period
          ? <InlinePeriodSelect value={item.period} onSave={period => updatePeriod.mutate({ filename: item.filename, period })} />
          : <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.impact_detail ?? '—'}</span>}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {item.true_impact != null ? (
          <span title={interestDelta != null && interestDelta > 0 ? `+${fmt(interestDelta)} interest` : undefined} style={{ color: impactColor, fontWeight: 500 }}>
            {item.direction === 'out' ? '−' : '+'}{fmt(item.true_impact)}
          </span>
        ) : '—'}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: '12px', color: STATUS_COLORS[item.status] ?? 'var(--text-muted)', fontWeight: 500 }}>
            {item.status}
          </span>
          {item.type === 'savings' && isActive(item.status) && (
            <button
              onClick={() => markAsDone.mutate(item.filename)}
              disabled={markingDoneFilename === item.filename || item.savings == null}
              className="btn btn-ghost"
              title={item.savings == null ? 'Set a savings amount first' : 'Mark as done'}
              style={{ fontSize: '11px', padding: '2px 8px', display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--success)' }}
            >
              <Check size={12} />
              {markingDoneFilename === item.filename ? 'Saving…' : 'Mark done'}
            </button>
          )}
        </div>
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {item.type === 'savings' && item.status === 'done' ? (
          <InlineNumberEdit
            value={item.actual_savings ?? null}
            onSave={actual_savings => updateActualSavings.mutate({ filename: item.filename, actual_savings })}
          />
        ) : (
          <span style={{ color: 'var(--text-muted)' }}>—</span>
        )}
      </td>
      <td style={{ padding: '8px 12px' }}>
        {item.type === 'purchase' && <InlineDateEdit value={item.purchase_date ?? null} onSave={date => updatePurchaseDate.mutate({ filename: item.filename, date })} />}
        {item.type === 'savings' && <InlineDateEdit value={item.completed_date ?? null} onSave={date => updateCompletedDate.mutate({ filename: item.filename, date })} />}
        {item.type === 'selling' && <InlineDateEdit value={item.sold_date ?? null} onSave={date => updateSoldDate.mutate({ filename: item.filename, date })} />}
      </td>
      <td style={{ padding: '8px 12px', color: 'var(--text-muted)', fontSize: '12px' }}>{item.added || '—'}</td>
    </tr>
  )
}

export default function PlanningPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = usePlanning()
  const { data: savingsData } = useSavingsOpportunities()
  const movePurchase = usePlanningMovePurchase()
  const moveSavings = usePlanningMoveSavings()
  const moveSelling = usePlanningMoveSelling()
  const markAsDone = usePlanningMarkAsDone()
  const [typeFilter, setTypeFilter] = useState<string>('active')
  const [yearFilter, setYearFilter] = useState<string>('all')

  if (isLoading) return <div className="info-box">Loading planning data…</div>
  if (isError) return (
    <div className="error-box">
      Failed to load planning data{error?.message ? `: ${error.message}` : ''}.
      {' '}Restart the FastAPI backend if you just added this feature.
    </div>
  )

  const { items, summary, max_cc_rate, counts } = data!

  const filtered = items.filter(i => {
    if (typeFilter === 'active') return isActive(i.status)
    if (typeFilter === 'all') return true
    return i.type === typeFilter
  })

  function handleMove(item: PlanningItem, direction: 'up' | 'down') {
    if (item.type === 'purchase') movePurchase.mutate({ filename: item.filename, direction })
    else if (item.type === 'savings') moveSavings.mutate({ filename: item.filename, direction })
    else moveSelling.mutate({ filename: item.filename, direction })
  }

  function typePosition(item: PlanningItem) {
    const typeItems = filtered.filter(i => i.type === item.type)
    const idx = typeItems.findIndex(i => i.filename === item.filename)
    return { isFirst: idx === 0, isLast: idx === typeItems.length - 1 }
  }

  const doneSavings = items.filter(i => i.type === 'savings' && i.status === 'done')
  const doneCountForYear = yearFilter === 'all'
    ? doneSavings.length
    : doneSavings.filter(i => completedYear(i.completed_date)?.toString() === yearFilter).length

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px' }}>Financial Planning</h2>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 3 }}>
            {counts.purchase} purchases · {counts.savings} savings · {counts.selling} selling
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={() => refetch()} disabled={isFetching} className="btn btn-ghost" style={{ fontSize: '12px', padding: '4px 10px' }}>
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
          {['active', 'all', 'purchase', 'savings', 'selling'].map(f => (
            <button key={f} onClick={() => setTypeFilter(f)}
              className={`btn btn-ghost${typeFilter === f ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}>
              {f === 'active' ? 'Active' : f === 'all' ? 'All' : TYPE_LABELS[f as PlanningType]}
            </button>
          ))}
        </div>
      </div>

      {savingsData && (typeFilter === 'active' || typeFilter === 'all' || typeFilter === 'savings') && (
        <RealizedSavingsSummary
          totalRealized={savingsData.total_realized_savings}
          realizedByYear={savingsData.realized_by_year}
          doneCount={doneCountForYear}
          yearFilter={yearFilter}
          onYearFilterChange={setYearFilter}
        />
      )}

      <SummaryBar summary={summary} maxCcRate={max_cc_rate} />
      <ImpactChart items={items} />

      {filtered.length === 0 ? (
        <div className="info-box">
          No planning items found. Add notes in Obsidian using the purchase, savings opportunity, or selling templates.
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '12px', textAlign: 'left' }}>
                <th style={{ width: 56 }} />
                <th style={{ padding: '6px 12px' }}>Type</th>
                <th style={{ padding: '6px 12px' }}>Title</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Amount</th>
                <th style={{ padding: '6px 12px' }}>Period</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>True Impact</th>
                <th style={{ padding: '6px 12px', textAlign: 'center' }}>Status</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Actual Savings</th>
                <th style={{ padding: '6px 12px' }}>Date</th>
                <th style={{ padding: '6px 12px' }}>Added</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(item => {
                const { isFirst, isLast } = typePosition(item)
                return (
                  <PlanningRow
                    key={`${item.type}-${item.filename}`}
                    item={item}
                    isFirst={isFirst}
                    isLast={isLast}
                    onMove={dir => handleMove(item, dir)}
                    markingDoneFilename={markAsDone.isPending ? (markAsDone.variables ?? null) : null}
                  />
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
