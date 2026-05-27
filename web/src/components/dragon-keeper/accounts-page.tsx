import { useState, useMemo } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, LabelList,
} from 'recharts'
import { useAccountsPage, useSetInterestRate, useSetCreditLimit, type Account } from '../../hooks/dragon-keeper/use-accounts-page'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatMonth(ym: string): string {
  const [year, month] = ym.split('-')
  const d = new Date(Number(year), Number(month) - 1, 1)
  return d.toLocaleDateString('en-US', { month: 'short' })
}

const TYPE_LABEL: Record<string, string> = {
  checking: 'Checking',
  savings: 'Savings',
  creditCard: 'Credit Card',
  cash: 'Cash',
  lineOfCredit: 'Line of Credit',
  otherAsset: 'Asset',
  otherLiability: 'Liability',
  mortgage: 'Mortgage',
  autoLoan: 'Auto Loan',
  studentLoan: 'Student Loan',
  medicalDebt: 'Medical Debt',
  otherDebt: 'Other Debt',
  personalLoan: 'Personal Loan',
}

const TYPE_COLOR: Record<string, string> = {
  checking: '#10b981',
  savings: '#06b6d4',
  cash: '#84cc16',
  otherAsset: '#14b8a6',
  creditCard: '#ef4444',
  lineOfCredit: '#f97316',
  autoLoan: '#f59e0b',
  studentLoan: '#8b5cf6',
  mortgage: '#6366f1',
  medicalDebt: '#9333ea',
  otherLiability: '#dc2626',
  otherDebt: '#b91c1c',
  personalLoan: '#64748b',
}

function typeColor(type: string): string {
  return TYPE_COLOR[type] ?? '#6b7280'
}

function isDebtType(type: string) {
  return ['creditCard', 'lineOfCredit', 'mortgage', 'autoLoan', 'studentLoan',
    'medicalDebt', 'otherLiability', 'otherDebt', 'personalLoan'].includes(type)
}

function isCreditType(type: string) {
  return ['creditCard', 'lineOfCredit'].includes(type)
}

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max - 1) + '…' : s
}

/* ---- Type filter chips ---- */
interface TypeFilterProps {
  allTypes: string[]
  filter: Set<string> | 'all'
  onChange: (f: Set<string> | 'all') => void
}

function TypeFilter({ allTypes, filter, onChange }: TypeFilterProps) {
  function toggle(type: string) {
    if (filter === 'all') {
      onChange(new Set([type]))
      return
    }
    const next = new Set(filter)
    if (next.has(type)) {
      next.delete(type)
      onChange(next.size === 0 ? 'all' : next)
    } else {
      next.add(type)
      onChange(next.size === allTypes.length ? 'all' : next)
    }
  }

  function isActive(type: string) {
    return filter === 'all' || filter.has(type)
  }

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
      <button
        onClick={() => onChange('all')}
        style={{
          padding: '4px 12px', borderRadius: '99px', fontSize: '12px', fontWeight: 600,
          cursor: 'pointer', border: '1px solid',
          background: filter === 'all' ? 'var(--accent)' : 'transparent',
          borderColor: filter === 'all' ? 'var(--accent)' : 'var(--border)',
          color: filter === 'all' ? '#fff' : 'var(--text-muted)',
          transition: 'all 0.15s',
        }}
      >
        All
      </button>
      {allTypes.map(type => {
        const active = isActive(type)
        const color = typeColor(type)
        return (
          <button
            key={type}
            onClick={() => toggle(type)}
            style={{
              padding: '4px 12px', borderRadius: '99px', fontSize: '12px', fontWeight: 600,
              cursor: 'pointer', border: '1px solid',
              background: active ? color + '22' : 'transparent',
              borderColor: active ? color : 'var(--border)',
              color: active ? color : 'var(--text-muted)',
              transition: 'all 0.15s',
            }}
          >
            {TYPE_LABEL[type] ?? type}
          </button>
        )
      })}
    </div>
  )
}

/* ---- Combined overview bar chart ---- */
interface OverviewChartProps {
  accounts: Account[]
}

function OverviewChart({ accounts }: OverviewChartProps) {
  if (accounts.length === 0) return null

  const data = [...accounts]
    .sort((a, b) => {
      const aSize = isCreditType(a.type) && a.credit_limit ? a.credit_limit : Math.abs(a.balance)
      const bSize = isCreditType(b.type) && b.credit_limit ? b.credit_limit : Math.abs(b.balance)
      return bSize - aSize
    })
    .map(a => {
      const used = Math.abs(a.balance)
      const available = isCreditType(a.type) && a.credit_limit != null
        ? Math.max(0, a.credit_limit - used)
        : 0
      return {
        name: truncate(a.name, 14),
        fullName: a.name,
        used,
        available,
        type: a.type,
        interest_rate: a.interest_rate,
        credit_limit: a.credit_limit,
      }
    })

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '20px',
    }}>
      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Balance Overview
      </div>
      <ResponsiveContainer width="100%" height={640}>
        <BarChart data={data} margin={{ top: 40, right: 20, bottom: 90, left: 60 }} barCategoryGap="20%">
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.4} vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: 'var(--text-primary)', angle: -40, textAnchor: 'end' } as any}
            interval={0}
            height={90}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={v => formatCurrency(v)}
            tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
            width={70}
            domain={[0, (dataMax: number) => Math.ceil(dataMax * 1.15)]}
          />
          <Tooltip
            formatter={(v: number, name: string, props: any) => {
              if (v === 0) return null as any
              if (name === 'used') return [formatCurrency(v), TYPE_LABEL[props.payload.type] ?? props.payload.type]
              if (name === 'available') return [formatCurrency(v), 'Available Credit']
              return [formatCurrency(v), name]
            }}
            labelFormatter={(_: any, payload: any[]) => payload?.[0]?.payload?.fullName ?? ''}
            contentStyle={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: '8px', fontSize: '12px',
            }}
          />
          {/* Used / balance portion — APR label here when no credit limit is set (available = 0) */}
          <Bar dataKey="used" stackId="a" radius={[0, 0, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={typeColor(entry.type)} opacity={0.85} />
            ))}
            <LabelList
              content={(props: any) => {
                const entry = data[props.index]
                if (!entry || !isDebtType(entry.type) || entry.available > 0) return null
                const hasRate = entry.interest_rate != null
                return (
                  <text
                    x={props.x + props.width / 2}
                    y={(props.y ?? 0) - 6}
                    textAnchor="middle"
                    style={{ fill: hasRate ? '#ef4444' : '#9ca3af', fontSize: 9, fontWeight: hasRate ? 700 : 400 }}
                  >
                    {hasRate ? `${entry.interest_rate}% APR` : '—%'}
                  </text>
                )
              }}
            />
          </Bar>
          {/* Available credit portion — APR label here when credit limit IS set (available > 0) */}
          <Bar dataKey="available" stackId="a" radius={[3, 3, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill="#475569" opacity={0.35} />
            ))}
            <LabelList
              content={(props: any) => {
                const entry = data[props.index]
                if (!entry || !isDebtType(entry.type) || entry.available === 0) return null
                const hasRate = entry.interest_rate != null
                return (
                  <text
                    x={props.x + props.width / 2}
                    y={(props.y ?? 0) - 6}
                    textAnchor="middle"
                    style={{ fill: hasRate ? '#ef4444' : '#9ca3af', fontSize: 9, fontWeight: hasRate ? 700 : 400 }}
                  >
                    {hasRate ? `${entry.interest_rate}% APR` : '—%'}
                  </text>
                )
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ---- Interest rate inline editor ---- */
function InterestRateField({ account }: { account: Account }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const setRate = useSetInterestRate()

  function startEdit() {
    setDraft(account.interest_rate != null ? String(account.interest_rate) : '')
    setEditing(true)
  }

  function commit() {
    const parsed = draft.trim() === '' ? null : parseFloat(draft)
    if (parsed !== null && isNaN(parsed)) { setEditing(false); return }
    setRate.mutate({ accountId: account.id, rate: parsed })
    setEditing(false)
  }

  if (editing) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <input
          autoFocus
          type="number"
          step="0.01"
          min="0"
          max="100"
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false) }}
          placeholder="e.g. 24.99"
          style={{
            width: '80px', padding: '4px 8px', fontSize: '13px',
            background: 'var(--bg-input, var(--bg-card))', border: '1px solid var(--accent)',
            borderRadius: 'var(--radius)', color: 'var(--text-primary)', outline: 'none',
          }}
        />
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>%</span>
      </div>
    )
  }

  return (
    <button
      onClick={startEdit}
      title="Click to set APR"
      style={{
        background: 'none', border: 'none', cursor: 'pointer', padding: 0,
        display: 'flex', alignItems: 'center', gap: '4px',
      }}
    >
      <span style={{ fontSize: '15px', fontWeight: 700, color: account.interest_rate != null ? 'var(--error, #ef4444)' : 'var(--text-muted)' }}>
        {account.interest_rate != null ? `${account.interest_rate}%` : '— %'}
      </span>
      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>APR ✎</span>
    </button>
  )
}

/* ---- Credit limit inline editor ---- */
function CreditLimitField({ account }: { account: Account }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const setLimit = useSetCreditLimit()

  function startEdit() {
    setDraft(account.credit_limit != null ? String(account.credit_limit) : '')
    setEditing(true)
  }

  function commit() {
    const parsed = draft.trim() === '' ? null : parseFloat(draft)
    if (parsed !== null && isNaN(parsed)) { setEditing(false); return }
    setLimit.mutate({ accountId: account.id, limit: parsed })
    setEditing(false)
  }

  const used = Math.abs(account.balance)
  const utilPct = account.credit_limit ? Math.min(100, (used / account.credit_limit) * 100) : null

  if (editing) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <input
          autoFocus
          type="number"
          step="100"
          min="0"
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false) }}
          placeholder="e.g. 10000"
          style={{
            width: '100px', padding: '4px 8px', fontSize: '13px',
            background: 'var(--bg-input, var(--bg-card))', border: '1px solid var(--accent)',
            borderRadius: 'var(--radius)', color: 'var(--text-primary)', outline: 'none',
          }}
        />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      <button
        onClick={startEdit}
        title="Click to set credit limit"
        style={{
          background: 'none', border: 'none', cursor: 'pointer', padding: 0,
          display: 'flex', alignItems: 'center', gap: '4px', alignSelf: 'flex-start',
        }}
      >
        <span style={{ fontSize: '14px', fontWeight: 600, color: account.credit_limit != null ? 'var(--text-primary)' : 'var(--text-muted)' }}>
          {account.credit_limit != null ? `${formatCurrency(account.credit_limit)} limit` : '— limit'}
        </span>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>✎</span>
      </button>
      {utilPct != null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ flex: 1, height: '6px', background: 'var(--border)', borderRadius: '99px', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '99px',
              width: `${utilPct}%`,
              background: utilPct > 80 ? '#ef4444' : utilPct > 50 ? '#f59e0b' : '#10b981',
              transition: 'width 0.3s',
            }} />
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            {utilPct.toFixed(0)}% used
          </span>
        </div>
      )}
    </div>
  )
}

/* ---- Per-account card ---- */
function AccountCard({ account }: { account: Account }) {
  const debt = isDebtType(account.type)
  const displayBalance = debt ? Math.abs(account.balance) : account.balance
  const color = typeColor(account.type)

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '20px',
      display: 'flex', flexDirection: 'column', gap: '12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
        <div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>{account.name}</div>
          <div style={{
            display: 'inline-block', marginTop: '4px',
            fontSize: '10px', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase',
            padding: '2px 7px', borderRadius: '99px',
            background: color + '22',
            color,
          }}>
            {TYPE_LABEL[account.type] ?? account.type}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '22px', fontWeight: 700, color, lineHeight: 1 }}>
            {formatCurrency(displayBalance)}
          </div>
          {account.uncleared_balance !== 0 && (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '3px' }}>
              {formatCurrency(Math.abs(account.uncleared_balance))} uncleared
            </div>
          )}
        </div>
      </div>

      {debt && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '80px' }}>Interest rate:</span>
            <InterestRateField account={account} />
          </div>
          {isCreditType(account.type) && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '80px', paddingTop: '2px' }}>Credit limit:</span>
              <CreditLimitField account={account} />
            </div>
          )}
        </div>
      )}

      {account.monthly_activity.length > 0 ? (
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
            Monthly activity
            <span style={{ marginLeft: '12px' }}>
              <span style={{ color: '#ef4444' }}>■</span> Debits&nbsp;&nbsp;
              <span style={{ color: '#10b981' }}>■</span> Credits
            </span>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={account.monthly_activity} margin={{ top: 0, right: 0, bottom: 0, left: 0 }} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.4} vertical={false} />
              <XAxis
                dataKey="month"
                tickFormatter={formatMonth}
                tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide />
              <Tooltip
                formatter={(v: number, name: string) => [formatCurrency(v), name === 'debits' ? 'Debits' : 'Credits']}
                labelFormatter={formatMonth}
                contentStyle={{
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  borderRadius: '8px', fontSize: '12px',
                }}
              />
              <Bar dataKey="debits" fill="#ef4444" opacity={0.85} radius={[2, 2, 0, 0]} />
              <Bar dataKey="credits" fill="#10b981" opacity={0.85} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', padding: '16px 0' }}>
          No recent activity
        </div>
      )}
    </div>
  )
}

/* ---- Section ---- */
function AccountSection({ title, accounts }: { title: string; accounts: Account[] }) {
  if (accounts.length === 0) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
        {title}
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '16px',
      }}>
        {accounts.map(a => <AccountCard key={a.id} account={a} />)}
      </div>
    </div>
  )
}

/* ---- Page ---- */
export default function AccountsPage() {
  const { data, isLoading, isError, error } = useAccountsPage()
  const [typeFilter, setTypeFilter] = useState<Set<string> | 'all'>('all')

  const allTypes = useMemo(() => {
    if (!data) return []
    const seen = new Set<string>()
    for (const a of data.accounts) seen.add(a.type)
    // Sort: asset types first, then debt types
    return [...seen].sort((a, b) => {
      const aDebt = isDebtType(a) ? 1 : 0
      const bDebt = isDebtType(b) ? 1 : 0
      return aDebt - bDebt || (TYPE_LABEL[a] ?? a).localeCompare(TYPE_LABEL[b] ?? b)
    })
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    if (typeFilter === 'all') return data.accounts
    return data.accounts.filter(a => typeFilter.has(a.type))
  }, [data, typeFilter])

  const debitAccounts = filtered.filter(a => !isDebtType(a.type))
  const creditAccounts = filtered.filter(a => isDebtType(a.type))
  const totalDebit = debitAccounts.reduce((s, a) => s + a.balance, 0)
  const totalDebt = creditAccounts.reduce((s, a) => s + Math.abs(a.balance), 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>Accounts</h2>
        {data && (
          <div style={{ display: 'flex', gap: '24px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Debit total: <strong style={{ color: '#10b981' }}>{formatCurrency(totalDebit)}</strong>
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Debt total: <strong style={{ color: '#ef4444' }}>{formatCurrency(totalDebt)}</strong>
            </span>
          </div>
        )}
      </div>

      {isLoading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)' }}>
          <div className="spinner" />
          Loading accounts...
        </div>
      )}

      {isError && (
        <div className="error-box">Failed to load accounts: {(error as Error).message}</div>
      )}

      {data && (
        <>
          {allTypes.length > 1 && (
            <TypeFilter allTypes={allTypes} filter={typeFilter} onChange={setTypeFilter} />
          )}
          <OverviewChart accounts={filtered} />
          <AccountSection title="Debit & Savings" accounts={debitAccounts} />
          <AccountSection title="Credit Cards & Debt" accounts={creditAccounts} />
        </>
      )}
    </div>
  )
}
