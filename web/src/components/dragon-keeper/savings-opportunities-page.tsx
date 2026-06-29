import { useMemo, useState } from 'react'
import { ChevronUp, ChevronDown, ExternalLink, Check } from 'lucide-react'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts'
import {
  useSavingsOpportunities,
  useUpdateSavings,
  useUpdatePeriod,
  useUpdateCompletedDate,
  useUpdateActualSavings,
  useMarkAsDone,
  useMoveSavingsOpportunity,
  type SavingsOpportunity,
  type SavingsPeriod,
} from '../../hooks/dragon-keeper/use-savings-opportunities'

const STATUS_COLORS: Record<string, string> = {
  considering: 'var(--text-muted)',
  approved: 'var(--accent)',
  done: 'var(--success)',
  dropped: 'var(--text-muted)',
}

const STATUS_LABELS: Record<string, string> = {
  considering: 'Considering',
  approved: 'Approved',
  done: 'Done',
  dropped: 'Dropped',
}

const CHART_COLORS = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444', '#6366f1', '#14b8a6', '#f97316']

function fmt(n: number | null) {
  if (n == null) return '—'
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function isActive(status: string) {
  return status === 'considering' || status === 'approved'
}

function completedYear(date: string | null): number | null {
  if (!date) return null
  const y = parseInt(date.slice(0, 4), 10)
  return isNaN(y) ? null : y
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

function InlinePeriodSelect({
  value,
  onSave,
}: {
  value: SavingsPeriod
  onSave: (v: SavingsPeriod) => void
}) {
  return (
    <select
      value={value}
      onChange={e => onSave(e.target.value as SavingsPeriod)}
      style={{ padding: '2px 4px', fontSize: 'inherit', fontFamily: 'inherit', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '4px' }}
    >
      <option value="one-time">One-time</option>
      <option value="monthly">Monthly</option>
      <option value="yearly">Yearly</option>
    </select>
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

function TrueSavingsChart({ opportunities }: { opportunities: SavingsOpportunity[] }) {
  const data = useMemo(
    () => opportunities
      .filter(o => (o.true_savings_1yr ?? 0) > 0)
      .map(o => ({ name: o.action, value: o.true_savings_1yr! }))
      .sort((a, b) => b.value - a.value),
    [opportunities],
  )

  if (data.length === 0) return null

  const total = data.reduce((sum, d) => sum + d.value, 0)

  return (
    <div style={{
      marginBottom: 20,
      padding: '16px',
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
    }}>
      <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>
        True Savings by Action
        <span style={{ fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
          {fmt(total)}/yr total
        </span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={95}
            paddingAngle={2}
            label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [fmt(value), 'True savings']}
            contentStyle={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              fontSize: '12px',
            }}
          />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            iconSize={10}
            wrapperStyle={{ fontSize: '11px', lineHeight: '1.6', paddingLeft: '12px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

function RealizedSavingsSummary({
  opportunities,
  totalRealized,
  realizedByYear,
  yearFilter,
  onYearFilterChange,
}: {
  opportunities: SavingsOpportunity[]
  totalRealized: number
  realizedByYear: Record<string, number>
  yearFilter: string
  onYearFilterChange: (year: string) => void
}) {
  const doneCount = opportunities.filter(o => o.status === 'done').length
  if (doneCount === 0) return null

  const years = Object.keys(realizedByYear).sort((a, b) => parseInt(b) - parseInt(a))
  const filteredTotal = yearFilter === 'all'
    ? totalRealized
    : (realizedByYear[yearFilter] ?? 0)

  const filteredCount = yearFilter === 'all'
    ? doneCount
    : opportunities.filter(o => o.status === 'done' && completedYear(o.completed_date)?.toString() === yearFilter).length

  return (
    <div style={{
      marginBottom: 20,
      padding: '16px',
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: 12,
    }}>
      <div>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Realized Savings
        </div>
        <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--success)', marginTop: 4 }}>
          {fmt(filteredTotal)}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>
          from {filteredCount} completed {filteredCount === 1 ? 'action' : 'actions'}
          {yearFilter !== 'all' && ` in ${yearFilter}`}
        </div>
      </div>
      {years.length > 0 && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Year</span>
          <button
            onClick={() => onYearFilterChange('all')}
            className={`btn btn-ghost${yearFilter === 'all' ? ' dk-nav-active' : ''}`}
            style={{ fontSize: '12px', padding: '4px 10px' }}
          >
            All
          </button>
          {years.map(y => (
            <button
              key={y}
              onClick={() => onYearFilterChange(y)}
              className={`btn btn-ghost${yearFilter === y ? ' dk-nav-active' : ''}`}
              style={{ fontSize: '12px', padding: '4px 10px' }}
            >
              {y}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function OpportunityRow({
  opportunity,
  isFirst,
  isLast,
  onMove,
  onSavingsSave,
  onPeriodSave,
  onDateSave,
  onActualSavingsSave,
  onMarkDone,
  isMarkingDone,
}: {
  opportunity: SavingsOpportunity
  isFirst: boolean
  isLast: boolean
  onMove: (direction: 'up' | 'down') => void
  onSavingsSave: (savings: number) => void
  onPeriodSave: (period: SavingsPeriod) => void
  onDateSave: (date: string | null) => void
  onActualSavingsSave: (actual_savings: number) => void
  onMarkDone: () => void
  isMarkingDone: boolean
}) {
  const statusColor = STATUS_COLORS[opportunity.status] ?? 'var(--text-muted)'
  const interestAvoided = opportunity.true_savings_1yr != null && opportunity.annual_savings != null
    ? opportunity.true_savings_1yr - opportunity.annual_savings
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
          {opportunity.action}
          {opportunity.url && (
            <a href={opportunity.url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-muted)', lineHeight: 1 }}>
              <ExternalLink size={11} />
            </a>
          )}
        </div>
        {opportunity.category && (
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>{opportunity.category}</div>
        )}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        <InlineNumberEdit value={opportunity.savings} onSave={onSavingsSave} />
      </td>
      <td style={{ padding: '8px 12px' }}>
        <InlinePeriodSelect value={opportunity.period} onSave={onPeriodSave} />
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {opportunity.annual_savings != null ? (
          <span style={{ color: 'var(--success)' }}>
            {fmt(opportunity.annual_savings)}
          </span>
        ) : '—'}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {opportunity.true_savings_1yr != null ? (
          <span title={`+${fmt(interestAvoided)} interest avoided`} style={{ color: 'var(--success)', fontWeight: 500 }}>
            {fmt(opportunity.true_savings_1yr)}
          </span>
        ) : '—'}
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: '12px', color: statusColor, fontWeight: 500 }}>
            {STATUS_LABELS[opportunity.status] ?? opportunity.status}
          </span>
          {isActive(opportunity.status) && (
            <button
              onClick={onMarkDone}
              disabled={isMarkingDone || opportunity.annual_savings == null}
              className="btn btn-ghost"
              title={opportunity.annual_savings == null ? 'Set a savings amount first' : 'Mark as done'}
              style={{
                fontSize: '11px',
                padding: '2px 8px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                color: 'var(--success)',
              }}
            >
              <Check size={12} />
              {isMarkingDone ? 'Saving…' : 'Mark done'}
            </button>
          )}
        </div>
      </td>
      <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {opportunity.status === 'done' ? (
          <InlineNumberEdit value={opportunity.actual_savings} onSave={onActualSavingsSave} />
        ) : (
          <span style={{ color: 'var(--text-muted)' }}>—</span>
        )}
      </td>
      <td style={{ padding: '8px 12px' }}>
        <InlineDateEdit value={opportunity.completed_date} onSave={onDateSave} />
      </td>
      <td style={{ padding: '8px 12px', color: 'var(--text-muted)', fontSize: '12px' }}>
        {opportunity.added || '—'}
      </td>
    </tr>
  )
}

export default function SavingsOpportunitiesPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useSavingsOpportunities()
  const updateSavings = useUpdateSavings()
  const updatePeriod = useUpdatePeriod()
  const updateDate = useUpdateCompletedDate()
  const updateActualSavings = useUpdateActualSavings()
  const markAsDone = useMarkAsDone()
  const move = useMoveSavingsOpportunity()
  const [statusFilter, setStatusFilter] = useState<string>('active')
  const [yearFilter, setYearFilter] = useState<string>('all')

  if (isLoading) return <div className="info-box">Loading savings opportunities…</div>
  if (isError) return (
    <div className="error-box">
      Failed to load savings opportunities{error?.message ? `: ${error.message}` : ''}.
      {' '}If you just added this feature, restart the FastAPI backend so it picks up the new routes.
    </div>
  )

  const { opportunities, total_annual_savings, total_true_savings_1yr, total_realized_savings, realized_by_year, max_cc_rate } = data!

  const filtered = opportunities.filter(o => {
    if (statusFilter === 'active') return o.status === 'considering' || o.status === 'approved'
    if (statusFilter === 'all') return true
    return o.status === statusFilter
  })

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px' }}>Savings Opportunities</h2>
          {total_annual_savings > 0 && (
            <div style={{ fontSize: '12px', color: 'var(--success)', marginTop: 3, fontWeight: 500 }}>
              {fmt(total_annual_savings)}/yr potential from active opportunities
              {total_true_savings_1yr > total_annual_savings && max_cc_rate != null && (
                <> · {fmt(total_true_savings_1yr)}/yr true savings at {max_cc_rate}% APR</>
              )}
            </div>
          )}
          {max_cc_rate != null && total_annual_savings === 0 && (
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 3 }}>
              True savings calculated at {max_cc_rate}% APR (highest CC rate) over 1 year
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn btn-ghost"
            style={{ fontSize: '12px', padding: '4px 10px' }}
            title="Reload from Obsidian vault"
          >
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
          {['active', 'all', 'done', 'dropped'].map(f => (
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
          No savings opportunities found. Add a note to your vault using the <strong>template - savings opportunity</strong> template
          in <code>1 Personal/2 Areas/Personal Finance Area/Savings Opportunities</code>.
        </div>
      ) : (
        <>
          <RealizedSavingsSummary
            opportunities={opportunities}
            totalRealized={total_realized_savings}
            realizedByYear={realized_by_year}
            yearFilter={yearFilter}
            onYearFilterChange={setYearFilter}
          />
          {statusFilter !== 'done' && <TrueSavingsChart opportunities={filtered} />}
          <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '12px', textAlign: 'left' }}>
                <th style={{ width: 56 }} />
                <th style={{ padding: '6px 12px' }}>Action</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Savings</th>
                <th style={{ padding: '6px 12px' }}>Period</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Annual Savings</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>True Savings (1yr)</th>
                <th style={{ padding: '6px 12px', textAlign: 'center' }}>Status</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Actual Savings</th>
                <th style={{ padding: '6px 12px' }}>Completed Date</th>
                <th style={{ padding: '6px 12px' }}>Added</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o, idx) => (
                <OpportunityRow
                  key={o.filename}
                  opportunity={o}
                  isFirst={idx === 0}
                  isLast={idx === filtered.length - 1}
                  onMove={dir => move.mutate({ filename: o.filename, direction: dir })}
                  onSavingsSave={savings => updateSavings.mutate({ filename: o.filename, savings })}
                  onPeriodSave={period => updatePeriod.mutate({ filename: o.filename, period })}
                  onDateSave={date => updateDate.mutate({ filename: o.filename, date })}
                  onActualSavingsSave={actual_savings => updateActualSavings.mutate({ filename: o.filename, actual_savings })}
                  onMarkDone={() => markAsDone.mutate(o.filename)}
                  isMarkingDone={markAsDone.isPending && markAsDone.variables === o.filename}
                />
              ))}
            </tbody>
          </table>
          </div>
        </>
      )}
    </div>
  )
}
