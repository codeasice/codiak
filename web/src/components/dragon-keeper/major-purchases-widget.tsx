import { useState, useMemo } from 'react'
import { useTransactionSearch } from '../../hooks/dragon-keeper/use-transaction-explorer'

interface Props {
  onPayeeNavigate: (payee: string) => void
  onViewAll: (filters: { amount_min: number; date_from?: string; sort_by: string; sort_dir: string; outflow_only: boolean; exclude_recurring: boolean }) => void
}

const PERIODS = [
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
  { label: '6mo', days: 180 },
  { label: '1yr', days: 365 },
  { label: 'All', days: 0 },
]

const THRESHOLDS = [100, 200, 500, 1000]

function dateFromDays(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(amount))
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function MajorPurchasesWidget({ onPayeeNavigate, onViewAll }: Props) {
  const [days, setDays] = useState(0)
  const [threshold, setThreshold] = useState(1000)

  const dateFrom = useMemo(() => days > 0 ? dateFromDays(days) : undefined, [days])

  const { data, isLoading } = useTransactionSearch({
    amount_min: threshold,
    date_from: dateFrom,
    sort_by: 'amount',
    sort_dir: 'desc',
    page_size: 15,
    outflow_only: true,
    exclude_recurring: true,
  })

  const transactions = data?.transactions ?? []
  const totalAmount = data?.total_amount ?? 0
  const totalCount = data?.total_count ?? 0

  return (
    <div className="dk-card" style={{ padding: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', gap: '8px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Major Purchases</span>
          {totalCount > 0 && (
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'var(--surface-raised)', padding: '1px 6px', borderRadius: '10px' }}>
              {totalCount} &middot; {formatCurrency(totalAmount)}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginRight: '2px' }}>min</span>
          {THRESHOLDS.map(t => (
            <button
              key={t}
              onClick={() => setThreshold(t)}
              className={`btn btn-ghost`}
              style={{
                fontSize: '11px', padding: '2px 6px',
                color: threshold === t ? 'var(--accent)' : 'var(--text-muted)',
                fontWeight: threshold === t ? 700 : 400,
              }}
            >
              ${t}
            </button>
          ))}
          <span style={{ width: '1px', background: 'var(--border)', height: '14px', margin: '0 4px' }} />
          {PERIODS.map(p => (
            <button
              key={p.days}
              onClick={() => setDays(p.days)}
              className={`btn btn-ghost`}
              style={{
                fontSize: '11px', padding: '2px 6px',
                color: days === p.days ? 'var(--accent)' : 'var(--text-muted)',
                fontWeight: days === p.days ? 700 : 400,
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '13px' }}>
          <div className="spinner" />
          Loading...
        </div>
      )}

      {!isLoading && transactions.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '16px 0' }}>
          No purchases over ${threshold} in the last {days} days
        </div>
      )}

      {!isLoading && transactions.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
          {transactions.map(txn => (
            <div
              key={txn.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '90px 1fr auto',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 4px',
                borderRadius: 'var(--radius)',
                cursor: 'pointer',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-raised)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              onClick={() => txn.payee_name && onPayeeNavigate(txn.payee_name)}
            >
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                {formatDate(txn.date)}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: '13px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {txn.payee_name ?? '—'}
                </div>
                {txn.category_name && (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {txn.category_name}
                  </div>
                )}
              </div>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                {formatCurrency(txn.amount)}
              </span>
            </div>
          ))}
        </div>
      )}

      {totalCount > 15 && (
        <button
          onClick={() => onViewAll({ amount_min: threshold, date_from: dateFrom, sort_by: 'amount', sort_dir: 'desc', outflow_only: true, exclude_recurring: true })}
          className="btn btn-ghost"
          style={{ marginTop: '8px', fontSize: '12px', color: 'var(--accent)', width: '100%' }}
        >
          View all {totalCount} purchases →
        </button>
      )}
    </div>
  )
}
