import { useState, useMemo, useEffect } from 'react'
import {
  usePaycheckTracer,
  useIncomeSources,
  type PayPeriod,
  type CategorySpend,
} from '../../hooks/dragon-keeper/use-paycheck-tracer'
import { usePaycheckConfig, type PaycheckConfig } from '../../hooks/dragon-keeper/use-paycheck-config'
import { useAccountsPage, type Account } from '../../hooks/dragon-keeper/use-accounts-page'
import { useDkSettings, useUpdateDkSettings } from '../../hooks/dragon-keeper/use-dk-settings'
import { useRecurring, type RecurringItem } from '../../hooks/dragon-keeper/use-recurring'
import PayeeName from './payee-name'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function addCadenceDays(dateStr: string, cadence: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  if (cadence === 'biweekly') d.setDate(d.getDate() + 14)
  else if (cadence === 'monthly') d.setMonth(d.getMonth() + 1)
  else d.setFullYear(d.getFullYear() + 1)
  return d.toISOString().split('T')[0]
}

/* ---- Remaining Bills Panel ---- */

function RemainingBillsPanel({ bills, nextPaycheckDate, account, onPayeeNavigate }: {
  bills: RecurringItem[]
  nextPaycheckDate: string
  account?: Account
  onPayeeNavigate?: (payee: string) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const today = new Date().toISOString().split('T')[0]
  const total = bills.reduce((s, b) => s + b.expected_amount, 0)
  const afterBills = account ? account.balance - total : null

  if (bills.length === 0) return null

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
    }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px', cursor: 'pointer',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
            Remaining This Period
          </span>
          <span style={{
            padding: '1px 7px', fontSize: '10px', fontWeight: 700, borderRadius: '10px',
            background: 'color-mix(in srgb, var(--danger) 12%, transparent)',
            color: 'var(--danger)',
          }}>
            {bills.length}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums' }}>
            -{formatCurrency(total)}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : 'none' }}>▼</span>
        </div>
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)' }}>
          <div style={{ padding: '4px 20px 8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            Until estimated next paycheck · {formatDate(nextPaycheckDate)}
          </div>
          {bills.map(bill => {
            const days = Math.round(
              (new Date(bill.next_expected_date + 'T00:00:00').getTime() - new Date(today + 'T00:00:00').getTime())
              / 86400000
            )
            const isOverdue = days < 0
            const isDueToday = days === 0
            const daysColor = isOverdue ? 'var(--danger)' : isDueToday || days <= 2 ? 'var(--warning, #f59e0b)' : 'var(--text-muted)'
            const dueLabel = isOverdue
              ? `${Math.abs(days)}d overdue`
              : isDueToday
              ? 'Due today'
              : `${formatDate(bill.next_expected_date)} · in ${days}d`
            return (
              <div key={bill.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '9px 20px', borderBottom: '1px solid var(--border)',
              }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 500 }}>
                    <PayeeName
                      payeeName={bill.payee_name}
                      onClick={onPayeeNavigate ? () => onPayeeNavigate(bill.payee_name) : undefined}
                    />
                  </div>
                  <div style={{ fontSize: '11px', color: daysColor, marginTop: '1px', fontWeight: isOverdue || isDueToday ? 600 : 400 }}>
                    {dueLabel}
                  </div>
                </div>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums' }}>
                  -{formatCurrency(bill.expected_amount)}
                </span>
              </div>
            )
          })}

          {account && afterBills !== null && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '12px 20px',
              background: 'color-mix(in srgb, var(--bg-hover) 60%, transparent)',
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
                  {account.name}
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums', marginTop: '2px' }}>
                  {formatCurrency(account.balance)}
                </div>
              </div>
              <div style={{ fontSize: '16px', color: 'var(--text-muted)', flexShrink: 0 }}>→</div>
              <div style={{ flex: 1, textAlign: 'right' }}>
                <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
                  After Bills
                </div>
                <div style={{
                  fontSize: '16px', fontWeight: 700, fontVariantNumeric: 'tabular-nums', marginTop: '2px',
                  color: afterBills >= 0 ? 'var(--success)' : 'var(--danger)',
                }}>
                  {formatCurrency(afterBills)}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ---- Paycheck Breakdown Panel ---- */

const CATEGORY_LABELS: Record<string, string> = {
  taxes: 'Taxes',
  benefits: 'Benefits',
  retirement: 'Retirement',
  other: 'Other',
}

const CATEGORY_COLORS: Record<string, string> = {
  taxes: 'var(--danger)',
  benefits: '#06b6d4',
  retirement: '#8b5cf6',
  other: '#f59e0b',
}

function PaycheckBreakdownPanel({ config }: { config: PaycheckConfig }) {
  const [expanded, setExpanded] = useState(false)
  const [expandedCat, setExpandedCat] = useState<Record<string, boolean>>({})

  const totalDeductions = Object.values(config.deductions)
    .flat()
    .reduce((s, i) => s + i.amount, 0)

  const categories = Object.entries(config.deductions).filter(([, items]) => items.length > 0)

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
    }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px', cursor: 'pointer',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
          Paycheck Breakdown
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
            {formatCurrency(totalDeductions)} deducted
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : 'none' }}>▼</span>
        </div>
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '8px 0' }}>
          {/* Visual bar */}
          <div style={{ padding: '0 20px 12px' }}>
            <div style={{ display: 'flex', height: '8px', borderRadius: '4px', overflow: 'hidden', gap: '2px' }}>
              {categories.map(([cat, items]) => {
                const total = items.reduce((s, i) => s + Math.abs(i.amount), 0)
                const pct = (total / config.gross_amount) * 100
                return (
                  <div
                    key={cat}
                    title={`${CATEGORY_LABELS[cat]}: ${formatCurrency(-total)}`}
                    style={{ width: `${pct}%`, background: CATEGORY_COLORS[cat] || 'var(--text-muted)', borderRadius: '2px', opacity: 0.8 }}
                  />
                )
              })}
            </div>
          </div>

          {categories.map(([cat, items]) => {
            const subtotal = items.reduce((s, i) => s + i.amount, 0)
            const catExpanded = expandedCat[cat] ?? false
            return (
              <div key={cat}>
                <div
                  onClick={() => setExpandedCat(prev => ({ ...prev, [cat]: !catExpanded }))}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '8px 20px', cursor: 'pointer',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: CATEGORY_COLORS[cat] || 'var(--text-muted)', flexShrink: 0 }} />
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {CATEGORY_LABELS[cat] || cat}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums' }}>
                      {formatCurrency(subtotal)}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{catExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>
                {catExpanded && items.map((item, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '5px 20px 5px 36px', fontSize: '12px',
                  }}>
                    <span style={{ color: 'var(--text-muted)' }}>{item.name}</span>
                    <span style={{ color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                      {formatCurrency(item.amount)}
                    </span>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

/* ---- Category Bar ---- */

const BAR_COLORS = [
  'var(--accent, #6366f1)', '#ec4899', '#f59e0b', '#10b981',
  '#8b5cf6', '#ef4444', '#06b6d4', '#f97316',
  '#84cc16', '#14b8a6', '#a855f7', '#e11d48',
]

function CategoryBar({ categories, takeHome }: { categories: CategorySpend[]; takeHome: number }) {
  const top = categories.slice(0, 8)
  const otherAmount = categories.slice(8).reduce((s, c) => s + c.amount, 0)

  return (
    <div>
      <div style={{ display: 'flex', height: '24px', borderRadius: '6px', overflow: 'hidden', background: 'var(--bg-hover)' }}>
        {top.map((c, i) => {
          const pct = (c.amount / takeHome) * 100
          if (pct < 1.5) return null
          return (
            <div
              key={c.category}
              title={`${c.category}: ${formatCurrency(c.amount)} (${pct.toFixed(1)}%)`}
              style={{ width: `${Math.min(pct, 100)}%`, background: BAR_COLORS[i % BAR_COLORS.length], opacity: 0.85, transition: 'width 0.3s ease' }}
            />
          )
        })}
        {otherAmount > 0 && (
          <div
            title={`Other: ${formatCurrency(otherAmount)}`}
            style={{ width: `${Math.min((otherAmount / takeHome) * 100, 100)}%`, background: 'var(--text-muted)', opacity: 0.3 }}
          />
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 16px', marginTop: '8px', fontSize: '11px' }}>
        {top.slice(0, 6).map((c, i) => (
          <div key={c.category} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: BAR_COLORS[i % BAR_COLORS.length], flexShrink: 0 }} />
            <span style={{ color: 'var(--text-muted)' }}>
              {c.category.length > 20 ? c.category.slice(0, 20) + '...' : c.category}
            </span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
              {((c.amount / takeHome) * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ---- Pay Period Card ---- */

function PeriodCard({ period, takeHome, onPayeeNavigate, onNavigateToExplorer }: {
  period: PayPeriod
  takeHome: number
  onPayeeNavigate?: (p: string) => void
  onNavigateToExplorer?: (filters: { category_id?: string; date_from?: string; date_to?: string }) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const saveColor = period.total_saved >= 0 ? 'var(--success)' : 'var(--danger)'
  const savedLabel = period.is_current ? 'Spent so far' : (period.total_saved >= 0 ? 'Saved' : 'Over')

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      borderLeft: period.is_current ? '3px solid var(--accent)' : undefined,
    }}>
      <div style={{ padding: '16px 20px', cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {formatDate(period.period_start)} — {formatDate(period.period_end)}{period.period_end_is_estimate ? ' (est.)' : ''}
            </span>
            {period.is_current && (
              <span style={{
                marginLeft: '8px', padding: '1px 8px', fontSize: '10px', fontWeight: 600,
                borderRadius: '10px', background: 'color-mix(in srgb, var(--accent) 15%, transparent)',
                color: 'var(--accent)',
              }}>
                Current
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Deposited</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                {formatCurrency(period.paycheck_amount)}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{savedLabel}</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: period.is_current ? 'var(--text-primary)' : saveColor, fontVariantNumeric: 'tabular-nums' }}>
                {period.is_current ? formatCurrency(period.total_spent) : `${period.total_saved >= 0 ? '+' : ''}${formatCurrency(period.total_saved)}`}
              </div>
            </div>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : 'none' }}>▼</span>
          </div>
        </div>
        <CategoryBar categories={period.categories} takeHome={takeHome} />
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '12px 20px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Category', 'Amount', '% of Take Home', 'Txns'].map((h, i) => (
                  <th key={h} style={{
                    padding: '6px 8px', fontSize: '10px', fontWeight: 700,
                    textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)',
                    textAlign: i === 0 ? 'left' : 'right',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {period.categories.map(c => {
                const pct = takeHome ? (c.amount / takeHome * 100) : 0
                return (
                  <tr key={c.category} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>
                      {c.category === 'Uncategorized' && onNavigateToExplorer ? (
                        <span
                          onClick={() => onNavigateToExplorer({ category_id: '__uncategorized__', date_from: period.period_start, date_to: period.period_end })}
                          style={{ cursor: 'pointer', color: 'var(--warning, #f59e0b)', borderBottom: '1px dashed currentColor' }}
                          onMouseEnter={e => (e.currentTarget.style.opacity = '0.7')}
                          onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                          title="View uncategorized transactions for this period"
                        >
                          {c.category}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-primary)' }}>{c.category}</span>
                      )}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                      {formatCurrency(c.amount)}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: 'var(--text-muted)' }}>
                      {pct.toFixed(1)}%
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', color: 'var(--text-muted)' }}>
                      {c.transaction_count}
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot>
              <tr style={{ borderTop: '2px solid var(--border)' }}>
                <td style={{ padding: '8px', fontWeight: 700, color: 'var(--text-primary)' }}>Total</td>
                <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                  {formatCurrency(period.total_spent)}
                </td>
                <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: 'var(--text-muted)' }}>
                  {takeHome ? (period.total_spent / takeHome * 100).toFixed(1) : 0}%
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  )
}

/* ---- Main Component ---- */

interface PaycheckTracerProps {
  onPayeeNavigate?: (payee: string) => void
  onNavigateToExplorer?: (filters: { category_id?: string; date_from?: string; date_to?: string }) => void
}

export default function PaycheckTracer({ onPayeeNavigate, onNavigateToExplorer }: PaycheckTracerProps) {
  const { data: sourcesData } = useIncomeSources()
  const { data: accountsData } = useAccountsPage()
  const { data: config } = usePaycheckConfig()
  const { data: settings } = useDkSettings()
  const updateSettings = useUpdateDkSettings()

  const [selectedSourceId, setSelectedSourceId] = useState<number | undefined>(undefined)
  const [numPeriods, setNumPeriods] = useState(6)
  const [selectedAccountId, setSelectedAccountId] = useState<string | undefined>(undefined)

  const accounts = useMemo(() =>
    (accountsData?.accounts ?? []).filter(a => a.on_budget),
    [accountsData]
  )

  const fallbackAccountId = useMemo(() =>
    accounts.find(a => a.type === 'checking')?.id ?? accounts[0]?.id,
    [accounts]
  )

  // Initialise from persisted setting once accounts + settings are loaded
  useEffect(() => {
    if (selectedAccountId !== undefined) return
    if (!settings || accounts.length === 0) return
    setSelectedAccountId(settings.paycheck_account_id || fallbackAccountId || '')
  }, [settings, accounts, fallbackAccountId, selectedAccountId])

  const effectiveAccountId = selectedAccountId || fallbackAccountId

  const handleAccountChange = (id: string) => {
    setSelectedAccountId(id)
    updateSettings.mutate({ paycheck_account_id: id })
  }

  const { data, isLoading } = usePaycheckTracer(selectedSourceId, numPeriods, effectiveAccountId)
  const { data: recurringData } = useRecurring()

  const sources = sourcesData?.sources ?? []
  const periods = data?.periods ?? []
  const source = data?.income_source

  const takeHome = config?.take_home_amount ?? 0
  const gross = config?.gross_amount ?? 0
  const totalDeductions = gross - takeHome

  const selectedAccount = accounts.find(a => a.id === effectiveAccountId)

  const lastPeriod = periods[periods.length - 1]
  // Current active period: period_start = last paycheck, period_end = estimated next
  // Fall back to computing estimate from last complete period if backend didn't add one
  const currentPeriodStart = lastPeriod?.is_current
    ? lastPeriod.period_start
    : lastPeriod?.period_end ?? null
  const nextPaycheckEstimate = lastPeriod?.is_current
    ? lastPeriod.period_end
    : (lastPeriod?.period_end && source ? addCadenceDays(lastPeriod.period_end, source.cadence) : null)

  const remainingBills = useMemo(() => {
    if (!currentPeriodStart || !nextPaycheckEstimate) return []
    return (recurringData?.items ?? [])
      .filter(item =>
        item.type === 'expense' &&
        !item.cancelled_date &&
        item.confirmed &&
        item.next_expected_date >= currentPeriodStart &&
        item.next_expected_date <= nextPaycheckEstimate
      )
      .sort((a, b) => a.next_expected_date.localeCompare(b.next_expected_date))
  }, [recurringData, currentPeriodStart, nextPaycheckEstimate])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Paycheck Tracer
        </h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Account selector */}
          <select
            value={effectiveAccountId ?? ''}
            onChange={e => handleAccountChange(e.target.value)}
            style={{
              padding: '6px 10px', fontSize: '12px',
              background: 'var(--bg-card)', border: '1px solid var(--accent)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
            }}
          >
            <option value="">All Accounts</option>
            {accounts.map(a => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
          {sources.length > 1 && (
            <select
              value={selectedSourceId ?? ''}
              onChange={e => setSelectedSourceId(e.target.value ? Number(e.target.value) : undefined)}
              style={{
                padding: '6px 10px', fontSize: '12px',
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius)', color: 'var(--text-primary)',
              }}
            >
              <option value="">Auto-detect</option>
              {sources.map(s => (
                <option key={s.id} value={s.id}>{s.payee_name.slice(0, 40)} ({s.cadence})</option>
              ))}
            </select>
          )}
          <select
            value={numPeriods}
            onChange={e => setNumPeriods(Number(e.target.value))}
            style={{
              padding: '6px 10px', fontSize: '12px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
            }}
          >
            {[4, 6, 8, 12, 26].map(n => (
              <option key={n} value={n}>{n} periods</option>
            ))}
          </select>
        </div>
      </div>

      {source && (
        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Tracking:{' '}
          <span
            style={{
              fontWeight: 600, color: 'var(--text-primary)',
              cursor: onPayeeNavigate ? 'pointer' : 'default',
              borderBottom: onPayeeNavigate ? '1px dashed var(--text-muted)' : 'none',
            }}
            onClick={() => onPayeeNavigate?.(source.payee_name)}
          >
            {source.payee_name.slice(0, 60)}
          </span>
          {' '}({source.cadence})
        </div>
      )}

      {/* Stat cards */}
      {(config || selectedAccount) && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {selectedAccount && (
            <div style={{ flex: '1 1 160px', padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--accent)', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {selectedAccount.name}
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: selectedAccount.balance >= 0 ? 'var(--text-primary)' : 'var(--danger)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
                {formatCurrency(selectedAccount.balance)}
              </div>
              {selectedAccount.uncleared_balance !== 0 && (
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {formatCurrency(selectedAccount.cleared_balance)} cleared
                </div>
              )}
            </div>
          )}
          {config && (
            <>
              <div style={{ flex: '1 1 160px', padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Gross Pay
                </div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
                  {formatCurrency(gross)}
                </div>
              </div>
              <div style={{ flex: '1 1 160px', padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Deductions
                </div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
                  {formatCurrency(-totalDeductions)}
                </div>
              </div>
              <div style={{ flex: '1 1 160px', padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--success)', borderRadius: 'var(--radius-lg)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Take Home
                </div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--success)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
                  {formatCurrency(takeHome)}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Paycheck breakdown panel */}
      {config && <PaycheckBreakdownPanel config={config} />}

      {/* Remaining bills for active period */}
      {nextPaycheckEstimate && remainingBills.length > 0 && (
        <RemainingBillsPanel
          bills={remainingBills}
          nextPaycheckDate={nextPaycheckEstimate}
          account={selectedAccount}
          onPayeeNavigate={onPayeeNavigate}
        />
      )}

      {isLoading && (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          Loading paycheck data...
        </div>
      )}

      {!isLoading && periods.length === 0 && (
        <div style={{
          padding: '48px 24px', textAlign: 'center',
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
        }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            No paycheck data available
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Make sure you have recurring income detected on the Subscriptions page. At least 2 paycheck deposits are needed to define a pay period.
          </div>
        </div>
      )}

      {[...periods].reverse().map((p) => (
        <PeriodCard
          key={p.period_start}
          period={p}
          takeHome={takeHome || p.paycheck_amount}
          onPayeeNavigate={onPayeeNavigate}
          onNavigateToExplorer={onNavigateToExplorer}
        />
      ))}
    </div>
  )
}
