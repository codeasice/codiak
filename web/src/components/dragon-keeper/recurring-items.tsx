import { useState, useRef, useEffect } from 'react'
import {
  useRecurring,
  useDetectRecurring,
  useConfirmRecurring,
  useToggleSts,
  useDismissRecurring,
  type RecurringItem,
} from '../../hooks/dragon-keeper/use-recurring'
import { useToast } from './toast'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatShortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function daysUntil(iso: string): number {
  const target = new Date(iso + 'T00:00:00')
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  return Math.round((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
}

/* ---- Single Item Row ---- */

function RecurringRow({ item, onPayeeNavigate }: {
  item: RecurringItem
  onPayeeNavigate?: (payee: string) => void
}) {
  const confirm = useConfirmRecurring()
  const toggleSts = useToggleSts()
  const dismiss = useDismissRecurring()
  const { toast } = useToast()
  const days = daysUntil(item.next_expected_date)

  const daysLabel = days === 0 ? 'Today' : days === 1 ? 'Tomorrow' : days < 0 ? `${Math.abs(days)}d ago` : `in ${days}d`
  const daysColor = days <= 3 && days >= 0 ? 'var(--warning, #f59e0b)' : 'var(--text-muted)'

  return (
    <tr
      style={{ borderBottom: '1px solid var(--border)' }}
      onMouseEnter={e => {
        for (const td of e.currentTarget.children as any) td.style.background = 'var(--bg-hover)'
      }}
      onMouseLeave={e => {
        for (const td of e.currentTarget.children as any) td.style.background = 'transparent'
      }}
    >
      <td style={{ padding: '10px 12px' }}>
        <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
          {onPayeeNavigate ? (
            <span
              onClick={() => onPayeeNavigate(item.payee_name)}
              style={{ cursor: 'pointer', borderBottom: '1px dashed var(--text-muted)' }}
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)' }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--text-muted)' }}
            >
              {item.payee_name}
            </span>
          ) : item.payee_name}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
          {item.cadence === 'biweekly' ? 'Biweekly' : item.cadence === 'monthly' ? 'Monthly' : 'Annual'}
          {item.occurrence_count > 0 && ` · ${item.occurrence_count} occurrences`}
        </div>
      </td>
      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
        <span style={{
          padding: '2px 8px', fontSize: '10px', fontWeight: 600, borderRadius: '10px',
          background: item.type === 'income'
            ? 'color-mix(in srgb, var(--success) 15%, transparent)'
            : 'color-mix(in srgb, var(--danger) 15%, transparent)',
          color: item.type === 'income' ? 'var(--success)' : 'var(--danger)',
        }}>
          {item.type === 'income' ? 'Income' : 'Expense'}
        </span>
      </td>
      <td style={{
        padding: '10px 12px', textAlign: 'right', whiteSpace: 'nowrap',
        fontVariantNumeric: 'tabular-nums', fontWeight: 600,
        color: item.type === 'income' ? 'var(--success)' : 'var(--text-primary)',
      }}>
        {item.type === 'income' ? '+' : '-'}{formatCurrency(item.expected_amount)}
      </td>
      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
        <div style={{ color: 'var(--text-primary)', fontSize: '13px' }}>
          {formatShortDate(item.next_expected_date)}
        </div>
        <div style={{ fontSize: '11px', color: daysColor, fontWeight: days <= 3 && days >= 0 ? 600 : 400 }}>
          {daysLabel}
        </div>
      </td>
      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
        <input
          type="checkbox"
          checked={item.include_in_sts}
          onChange={() => {
            toggleSts.mutate(
              { id: item.id, include_in_sts: !item.include_in_sts },
              { onSuccess: () => toast(`${item.payee_name} ${!item.include_in_sts ? 'included in' : 'excluded from'} safe-to-spend`, 'info') },
            )
          }}
          style={{ cursor: 'pointer', accentColor: 'var(--accent)' }}
          title="Include in safe-to-spend projection"
        />
      </td>
      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', textAlign: 'right' }}>
        <div style={{ display: 'inline-flex', gap: '4px' }}>
          {!item.confirmed && (
            <button
              onClick={() => confirm.mutate(
                { id: item.id, confirmed: true },
                { onSuccess: () => toast(`Confirmed "${item.payee_name}"`, 'success') },
              )}
              style={{
                padding: '3px 10px', fontSize: '11px', fontWeight: 600,
                borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                background: 'color-mix(in srgb, var(--success) 15%, transparent)',
                color: 'var(--success)',
              }}
            >
              Confirm
            </button>
          )}
          <button
            onClick={() => dismiss.mutate(item.id, {
              onSuccess: () => toast(`Dismissed "${item.payee_name}"`, 'info'),
            })}
            style={{
              padding: '3px 10px', fontSize: '11px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
          >
            Dismiss
          </button>
        </div>
      </td>
    </tr>
  )
}

/* ---- Section Table ---- */

function ItemSection({ title, items, badge, onPayeeNavigate }: {
  title: string
  items: RecurringItem[]
  badge?: string
  onPayeeNavigate?: (payee: string) => void
}) {
  if (items.length === 0) return null

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
    }}>
      <div style={{
        padding: '14px 20px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <h3 style={{
          margin: 0, fontSize: '13px', fontWeight: 600,
          textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)',
        }}>
          {title}
        </h3>
        {badge && (
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
            {badge}
          </span>
        )}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Name', 'Type', 'Amount', 'Next Date', 'STS', ''].map((label, i) => (
                <th key={i} style={{
                  padding: '8px 12px', fontSize: '10px', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                  color: 'var(--text-muted)', textAlign: i === 2 ? 'right' : i === 4 ? 'center' : 'left',
                  whiteSpace: 'nowrap',
                }}>
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <RecurringRow key={item.id} item={item} onPayeeNavigate={onPayeeNavigate} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ---- Main Component ---- */

interface RecurringItemsProps {
  onBack: () => void
  onPayeeNavigate?: (payee: string) => void
}

export default function RecurringItems({ onBack, onPayeeNavigate }: RecurringItemsProps) {
  const { data, isLoading } = useRecurring()
  const detect = useDetectRecurring()
  const { toast } = useToast()
  const detectStartRef = useRef<number>(0)

  const items = data?.items ?? []
  const income = items.filter(i => i.type === 'income')
  const expenses = items.filter(i => i.type === 'expense')
  const unconfirmed = items.filter(i => !i.confirmed)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
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

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Subscriptions & Bills
        </h2>
        <button
          onClick={() => {
            detectStartRef.current = Date.now()
            detect.mutate(undefined, {
              onSuccess: (res) => {
                const secs = ((Date.now() - detectStartRef.current) / 1000).toFixed(1)
                if (res.new > 0) {
                  toast(`Found ${res.new} new recurring item${res.new !== 1 ? 's' : ''} (${secs}s)`, 'success')
                } else {
                  toast(`No new items detected (${res.detected} total analyzed, ${secs}s)`, 'info')
                }
              },
              onError: () => toast('Detection failed', 'error'),
            })
          }}
          disabled={detect.isPending}
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '7px 14px' }}
        >
          {detect.isPending ? 'Detecting...' : 'Detect Recurring'}
        </button>
      </div>

      {/* Summary cards */}
      {data && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{
            flex: '1 1 180px', padding: '16px 20px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Monthly Income
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--success)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
              +{formatCurrency(data.monthly_income)}
            </div>
          </div>
          <div style={{
            flex: '1 1 180px', padding: '16px 20px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Monthly Expenses
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
              -{formatCurrency(data.monthly_expenses)}
            </div>
          </div>
          <div style={{
            flex: '1 1 180px', padding: '16px 20px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Net Monthly
            </div>
            {(() => {
              const net = data.monthly_income - data.monthly_expenses
              return (
                <div style={{
                  fontSize: '20px', fontWeight: 700, fontVariantNumeric: 'tabular-nums', marginTop: '4px',
                  color: net >= 0 ? 'var(--success)' : 'var(--danger)',
                }}>
                  {net >= 0 ? '+' : ''}{formatCurrency(net)}
                </div>
              )
            })()}
          </div>
          {data.total_count > 0 && (
            <div style={{
              flex: '1 1 180px', padding: '16px 20px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
            }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Total Items
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                {data.total_count}
                {data.unconfirmed_count > 0 && (
                  <span style={{
                    marginLeft: '8px', fontSize: '12px', fontWeight: 600,
                    color: 'var(--warning, #f59e0b)',
                  }}>
                    ({data.unconfirmed_count} unconfirmed)
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {isLoading && (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          Loading...
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <div style={{
          padding: '48px 24px', textAlign: 'center',
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
        }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            No recurring items detected yet
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Click "Detect Recurring" to scan your transaction history for subscriptions, bills, and paychecks.
          </div>
        </div>
      )}

      {/* Unconfirmed section */}
      {unconfirmed.length > 0 && (
        <ItemSection
          title="Needs Confirmation"
          items={unconfirmed}
          badge={`${unconfirmed.length} new`}
          onPayeeNavigate={onPayeeNavigate}
        />
      )}

      <ItemSection
        title="Income"
        items={income.filter(i => i.confirmed)}
        badge={data ? `+${formatCurrency(data.monthly_income)}/mo` : undefined}
        onPayeeNavigate={onPayeeNavigate}
      />

      <ItemSection
        title="Bills & Subscriptions"
        items={expenses.filter(i => i.confirmed)}
        badge={data ? `-${formatCurrency(data.monthly_expenses)}/mo` : undefined}
        onPayeeNavigate={onPayeeNavigate}
      />
    </div>
  )
}
