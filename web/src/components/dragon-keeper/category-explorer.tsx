import { useState, useMemo, useEffect } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from 'recharts'
import { useCategoryList, useCategoryExplorer, type PayeeSummaryRow, type DowBucket } from '../../hooks/dragon-keeper/use-category-explorer'
import PayeeName from './payee-name'

const PALETTE = [
  '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6',
  '#8b5cf6', '#ef4444', '#14b8a6', '#f97316', '#84cc16',
  '#06b6d4', '#a855f7',
]

function formatCurrency(n: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function formatWeek(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

type SortKey = 'payee_name' | 'transaction_count' | 'avg_amount' | 'total_amount'

function PayeeTable({ rows, onPayeeNavigate }: { rows: PayeeSummaryRow[], onPayeeNavigate: (payee: string) => void }) {
  const [sortKey, setSortKey] = useState<SortKey>('total_amount')
  const [sortAsc, setSortAsc] = useState(false)

  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey]
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number)
      return sortAsc ? cmp : -cmp
    })
  }, [rows, sortKey, sortAsc])

  const totalSpend = rows.reduce((s, r) => s + r.total_amount, 0)

  function header(label: string, key: SortKey) {
    const active = sortKey === key
    return (
      <th
        onClick={() => { if (active) setSortAsc(a => !a); else { setSortKey(key); setSortAsc(false) } }}
        style={{
          padding: '8px 12px', textAlign: key === 'payee_name' ? 'left' : 'right',
          fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.8px',
          color: active ? 'var(--accent)' : 'var(--text-muted)',
          cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
          borderBottom: '1px solid var(--border)',
        }}
      >
        {label} {active ? (sortAsc ? '↑' : '↓') : ''}
      </th>
    )
  }

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
      <thead>
        <tr>
          {header('Payee', 'payee_name')}
          {header('# Trans', 'transaction_count')}
          {header('Avg', 'avg_amount')}
          {header('Total', 'total_amount')}
          <th style={{
            padding: '8px 12px', textAlign: 'right', fontSize: '11px', fontWeight: 600,
            textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)',
            borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap',
          }}>Share</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((row, i) => (
          <tr
            key={row.payee_name}
            style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? 'transparent' : 'var(--bg-hover)' }}
          >
            <td style={{ padding: '8px 12px', fontWeight: 500 }}>
              <PayeeName
                payeeName={row.payee_name}
                onClick={() => onPayeeNavigate(row.payee_name)}
              />
            </td>
            <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-muted)' }}>
              {row.transaction_count}
            </td>
            <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-muted)' }}>
              {formatCurrency(row.avg_amount)}
            </td>
            <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-primary)', fontWeight: 600 }}>
              {formatCurrency(row.total_amount)}
            </td>
            <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-muted)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
                <div style={{
                  height: '4px', width: `${Math.round((row.total_amount / totalSpend) * 60)}px`,
                  background: PALETTE[i % PALETTE.length], borderRadius: '2px', opacity: 0.7,
                }} />
                {totalSpend > 0 ? `${Math.round((row.total_amount / totalSpend) * 100)}%` : '—'}
              </div>
            </td>
          </tr>
        ))}
        {sorted.length > 1 && (
          <tr style={{ borderTop: '2px solid var(--border)' }}>
            <td style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-primary)' }}>Total</td>
            <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-muted)' }}>
              {rows.reduce((s, r) => s + r.transaction_count, 0)}
            </td>
            <td />
            <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: 'var(--text-primary)' }}>
              {formatCurrency(totalSpend)}
            </td>
            <td />
          </tr>
        )}
      </tbody>
    </table>
  )
}

const DOW_KEYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const

function DowHeatmap({ data }: { data: DowBucket[] }) {
  const [tooltip, setTooltip] = useState<{ text: string; x: number; y: number } | null>(null)

  const maxAmount = Math.max(...data.flatMap(w => DOW_KEYS.map(d => w[d])), 0.01)

  const dowSummary = DOW_KEYS.map(day => {
    const total = data.reduce((s, w) => s + w[day], 0)
    const activeWeeks = data.filter(w => w[day] > 0).length
    return { day, total, avg: activeWeeks > 0 ? total / activeWeeks : 0, activeWeeks }
  })
  const maxTotal = Math.max(...dowSummary.map(s => s.total), 0.01)

  const CELL_W = 22
  const CELL_H = 20
  const GAP = 3
  const LABEL_W = 28

  function cellColor(amount: number): string {
    if (amount === 0) return 'var(--bg-hover)'
    const intensity = Math.max(0.12, Math.min(1, amount / maxAmount))
    return `rgba(245, 158, 11, ${intensity})`
  }

  function dateForCell(weekStart: string, dowIndex: number): string {
    const d = new Date(weekStart + 'T00:00:00')
    d.setDate(d.getDate() + dowIndex)
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '16px 20px',
      position: 'relative',
    }}>
      <div style={{
        fontSize: '12px', fontWeight: 600, textTransform: 'uppercase',
        letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: '12px',
      }}>
        Day of Week
      </div>
      <div style={{ display: 'flex', gap: GAP }}>
        {/* Day labels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: GAP, paddingTop: CELL_H + GAP }}>
          {DOW_KEYS.map(day => (
            <div key={day} style={{
              height: CELL_H, lineHeight: `${CELL_H}px`,
              fontSize: '10px', color: 'var(--text-muted)',
              width: LABEL_W, textAlign: 'right', paddingRight: '6px',
            }}>
              {day}
            </div>
          ))}
        </div>
        {/* Week columns */}
        <div style={{ display: 'flex', gap: GAP, overflowX: 'auto' }}>
          {data.map((week, wi) => (
            <div key={week.week_start} style={{ display: 'flex', flexDirection: 'column', gap: GAP }}>
              {/* Week label */}
              <div style={{
                height: CELL_H, lineHeight: `${CELL_H}px`,
                fontSize: '9px', color: 'var(--text-muted)',
                width: CELL_W, textAlign: 'center',
                whiteSpace: 'nowrap', overflow: 'hidden',
              }}>
                {wi % 2 === 0 ? formatWeek(week.week_start) : ''}
              </div>
              {DOW_KEYS.map((day, di) => (
                <div
                  key={day}
                  onMouseEnter={e => {
                    const amt = week[day]
                    if (amt > 0) setTooltip({
                      text: `${dateForCell(week.week_start, di)}: ${formatCurrency(amt)}`,
                      x: e.clientX, y: e.clientY,
                    })
                  }}
                  onMouseLeave={() => setTooltip(null)}
                  style={{
                    width: CELL_W, height: CELL_H,
                    borderRadius: '3px',
                    background: cellColor(week[day]),
                    cursor: week[day] > 0 ? 'default' : undefined,
                    transition: 'opacity 0.1s',
                  }}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Summary column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: GAP, paddingTop: CELL_H + GAP, paddingLeft: '10px', borderLeft: '1px solid var(--border)', marginLeft: '4px' }}>
          {dowSummary.map(({ day, total, avg }) => (
            <div key={day} style={{ height: CELL_H, display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Mini bar */}
              <div style={{ width: '48px', height: '6px', borderRadius: '3px', background: 'var(--bg-hover)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: '3px',
                  width: `${Math.round((total / maxTotal) * 100)}%`,
                  background: `rgba(245,158,11,0.8)`,
                }} />
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-primary)', whiteSpace: 'nowrap', minWidth: '80px' }}>
                <span style={{ fontWeight: 600 }}>{formatCurrency(avg)}</span>
                <span style={{ color: 'var(--text-muted)', marginLeft: '4px' }}>avg</span>
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                {formatCurrency(total)}
              </div>
            </div>
          ))}
        </div>
      </div>
      {/* Color scale legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', fontSize: '10px', color: 'var(--text-muted)' }}>
        <span>Less</span>
        {[0.12, 0.35, 0.6, 0.8, 1].map(op => (
          <div key={op} style={{ width: 12, height: 12, borderRadius: '2px', background: `rgba(245,158,11,${op})` }} />
        ))}
        <span>More</span>
      </div>
      {tooltip && (
        <div style={{
          position: 'fixed', left: tooltip.x + 12, top: tooltip.y - 8,
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius)', padding: '5px 10px',
          fontSize: '12px', color: 'var(--text-primary)',
          boxShadow: '0 4px 12px rgba(0,0,0,.3)', zIndex: 200,
          pointerEvents: 'none',
        }}>
          {tooltip.text}
        </div>
      )}
    </div>
  )
}

export default function CategoryExplorer({ onPayeeNavigate }: { onPayeeNavigate: (payee: string) => void }) {
  const { data: categories = [] } = useCategoryList()
  const [selectedCategory, setSelectedCategory] = useState('')
  const [weeks, setWeeks] = useState(12)

  useEffect(() => {
    if (categories.length === 0) return
    const names = categories.map(c => c.name)
    // prefer "Dining Out" if it exists, otherwise fall back to first category
    const preferred = names.find(n => n.toLowerCase().includes('dining')) ?? names[0]
    setSelectedCategory(prev => (prev && names.includes(prev) ? prev : preferred))
  }, [categories])

  const { data, isLoading } = useCategoryExplorer(selectedCategory, weeks)

  const weeklyData = data?.weekly_data ?? []
  const allPayees = (data?.all_payees ?? []).slice(0, 20)
  const payeeSummary = data?.payee_summary ?? []

  const selectStyle = {
    padding: '6px 10px', fontSize: '12px',
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius)', color: 'var(--text-primary)',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Category Explorer
        </h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
            style={selectStyle}
          >
            {!selectedCategory && <option value="">Loading categories…</option>}
            {categories.map(c => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
          <select value={weeks} onChange={e => setWeeks(Number(e.target.value))} style={selectStyle}>
            <option value={4}>4 weeks</option>
            <option value={8}>8 weeks</option>
            <option value={12}>12 weeks</option>
            <option value={26}>26 weeks</option>
            <option value={52}>52 weeks</option>
          </select>
        </div>
      </div>

      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px',
      }}>
        {!selectedCategory || isLoading ? (
          <div style={{ height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ marginRight: '8px' }} />
            Loading...
          </div>
        ) : allPayees.length === 0 ? (
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            No transactions found for "{selectedCategory}" in this period.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={weeklyData} margin={{ top: 5, right: 10, bottom: 5, left: 10 }} barCategoryGap="25%">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} vertical={false} />
              <XAxis
                dataKey="week_start"
                tickFormatter={formatWeek}
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              />
              <YAxis
                tickFormatter={v => formatCurrency(v)}
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                width={72}
              />
              <Tooltip
                formatter={(v: number, name: string) => [formatCurrency(v), name]}
                labelFormatter={formatWeek}
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                cursor={{ fill: 'var(--bg-hover)' }}
              />
              <Legend
                wrapperStyle={{ fontSize: '11px', paddingTop: '12px' }}
                formatter={(value) => <span style={{ color: 'var(--text-muted)' }}>{value}</span>}
              />
              {allPayees.map((payee, i) => (
                <Bar
                  key={payee}
                  dataKey={payee}
                  stackId="a"
                  fill={PALETTE[i % PALETTE.length]}
                  radius={i === allPayees.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {(data?.dow_heatmap ?? []).length > 0 && payeeSummary.length > 0 && (
        <DowHeatmap data={data!.dow_heatmap} />
      )}

      {payeeSummary.length > 0 && (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)', overflow: 'hidden',
        }}>
          <div style={{
            display: 'flex', gap: '24px', padding: '12px 16px',
            borderBottom: '1px solid var(--border)',
            fontSize: '12px', color: 'var(--text-muted)',
          }}>
            <span><strong style={{ color: 'var(--text-primary)' }}>{payeeSummary.length}</strong> payees</span>
            <span><strong style={{ color: 'var(--text-primary)' }}>{payeeSummary.reduce((s, r) => s + r.transaction_count, 0)}</strong> transactions</span>
            <span><strong style={{ color: 'var(--text-primary)' }}>{formatCurrency(payeeSummary.reduce((s, r) => s + r.total_amount, 0))}</strong> total</span>
          </div>
          <PayeeTable rows={payeeSummary} onPayeeNavigate={onPayeeNavigate} />
        </div>
      )}
    </div>
  )
}
