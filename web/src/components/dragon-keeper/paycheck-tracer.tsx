import { useState } from 'react'
import {
  usePaycheckTracer,
  useIncomeSources,
  type PayPeriod,
  type CategorySpend,
  type CategoryAverage,
} from '../../hooks/dragon-keeper/use-paycheck-tracer'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatDateFull(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/* ---- Category Bar ---- */

const BAR_COLORS = [
  'var(--accent, #6366f1)', '#ec4899', '#f59e0b', '#10b981',
  '#8b5cf6', '#ef4444', '#06b6d4', '#f97316',
  '#84cc16', '#14b8a6', '#a855f7', '#e11d48',
]

function CategoryBar({ categories, paycheck }: { categories: CategorySpend[]; paycheck: number }) {
  const top = categories.slice(0, 8)
  const totalShown = top.reduce((s, c) => s + c.amount, 0)
  const otherAmount = categories.slice(8).reduce((s, c) => s + c.amount, 0)

  return (
    <div>
      <div style={{
        display: 'flex', height: '24px', borderRadius: '6px', overflow: 'hidden',
        background: 'var(--bg-hover)',
      }}>
        {top.map((c, i) => {
          const pct = (c.amount / paycheck) * 100
          if (pct < 1.5) return null
          return (
            <div
              key={c.category}
              title={`${c.category}: ${formatCurrency(c.amount)} (${pct.toFixed(1)}%)`}
              style={{
                width: `${Math.min(pct, 100)}%`,
                background: BAR_COLORS[i % BAR_COLORS.length],
                opacity: 0.85,
                transition: 'width 0.3s ease',
              }}
            />
          )
        })}
        {otherAmount > 0 && (
          <div
            title={`Other: ${formatCurrency(otherAmount)}`}
            style={{
              width: `${Math.min((otherAmount / paycheck) * 100, 100)}%`,
              background: 'var(--text-muted)',
              opacity: 0.3,
            }}
          />
        )}
      </div>
      <div style={{
        display: 'flex', flexWrap: 'wrap', gap: '6px 16px',
        marginTop: '8px', fontSize: '11px',
      }}>
        {top.slice(0, 6).map((c, i) => (
          <div key={c.category} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{
              width: '8px', height: '8px', borderRadius: '2px',
              background: BAR_COLORS[i % BAR_COLORS.length],
              flexShrink: 0,
            }} />
            <span style={{ color: 'var(--text-muted)' }}>
              {c.category.length > 20 ? c.category.slice(0, 20) + '...' : c.category}
            </span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
              {((c.amount / paycheck) * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ---- Pay Period Card ---- */

function PeriodCard({ period, onPayeeNavigate }: { period: PayPeriod; onPayeeNavigate?: (p: string) => void }) {
  const [expanded, setExpanded] = useState(false)
  const saveColor = period.total_saved >= 0 ? 'var(--success)' : 'var(--danger)'

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      borderLeft: period.is_current ? '3px solid var(--accent)' : undefined,
    }}>
      <div
        style={{ padding: '16px 20px', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: '10px',
        }}>
          <div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {formatDate(period.period_start)} — {formatDate(period.period_end)}
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
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Paycheck</div>
              <div style={{
                fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)',
                fontVariantNumeric: 'tabular-nums',
              }}>
                {formatCurrency(period.paycheck_amount)}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {period.total_saved >= 0 ? 'Saved' : 'Over'}
              </div>
              <div style={{
                fontSize: '14px', fontWeight: 700, color: saveColor,
                fontVariantNumeric: 'tabular-nums',
              }}>
                {period.total_saved >= 0 ? '+' : ''}{formatCurrency(period.total_saved)}
              </div>
            </div>
            <span style={{
              fontSize: '12px', color: 'var(--text-muted)',
              transition: 'transform 0.2s',
              transform: expanded ? 'rotate(180deg)' : 'none',
            }}>
              ▼
            </span>
          </div>
        </div>

        <CategoryBar categories={period.categories} paycheck={period.paycheck_amount} />
      </div>

      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border)', padding: '12px 20px',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Category', 'Amount', '% of Paycheck', 'Txns'].map((h, i) => (
                  <th key={h} style={{
                    padding: '6px 8px', fontSize: '10px', fontWeight: 700,
                    textTransform: 'uppercase', letterSpacing: '0.5px',
                    color: 'var(--text-muted)',
                    textAlign: i === 0 ? 'left' : 'right',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {period.categories.map(c => {
                const pct = period.paycheck_amount ? (c.amount / period.paycheck_amount * 100) : 0
                return (
                  <tr key={c.category} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '6px 8px', color: 'var(--text-primary)', fontWeight: 500 }}>
                      {c.category}
                    </td>
                    <td style={{
                      padding: '6px 8px', textAlign: 'right',
                      fontVariantNumeric: 'tabular-nums', fontWeight: 600,
                    }}>
                      {formatCurrency(c.amount)}
                    </td>
                    <td style={{
                      padding: '6px 8px', textAlign: 'right',
                      fontVariantNumeric: 'tabular-nums', color: 'var(--text-muted)',
                    }}>
                      {pct.toFixed(1)}%
                    </td>
                    <td style={{
                      padding: '6px 8px', textAlign: 'right',
                      color: 'var(--text-muted)',
                    }}>
                      {c.transaction_count}
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot>
              <tr style={{ borderTop: '2px solid var(--border)' }}>
                <td style={{ padding: '8px', fontWeight: 700, color: 'var(--text-primary)' }}>Total</td>
                <td style={{
                  padding: '8px', textAlign: 'right', fontWeight: 700,
                  fontVariantNumeric: 'tabular-nums',
                }}>
                  {formatCurrency(period.total_spent)}
                </td>
                <td style={{
                  padding: '8px', textAlign: 'right', fontWeight: 700,
                  fontVariantNumeric: 'tabular-nums', color: 'var(--text-muted)',
                }}>
                  {period.paycheck_amount ? (period.total_spent / period.paycheck_amount * 100).toFixed(1) : 0}%
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

/* ---- Averages Table ---- */

function AveragesSection({ averages, paycheck }: { averages: CategoryAverage[]; paycheck: number }) {
  if (averages.length === 0) return null

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
    }}>
      <div style={{
        padding: '14px 20px', borderBottom: '1px solid var(--border)',
      }}>
        <h3 style={{
          margin: 0, fontSize: '13px', fontWeight: 600,
          textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)',
        }}>
          Average per Pay Period
        </h3>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Category', 'Avg Amount', 'Avg %', 'Visual'].map((h, i) => (
                <th key={h} style={{
                  padding: '8px 12px', fontSize: '10px', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                  color: 'var(--text-muted)',
                  textAlign: i === 0 ? 'left' : i === 3 ? 'left' : 'right',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {averages.map((a, i) => (
              <tr
                key={a.category}
                style={{ borderBottom: '1px solid var(--border)' }}
                onMouseEnter={e => {
                  for (const td of e.currentTarget.children as any) td.style.background = 'var(--bg-hover)'
                }}
                onMouseLeave={e => {
                  for (const td of e.currentTarget.children as any) td.style.background = 'transparent'
                }}
              >
                <td style={{ padding: '8px 12px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {a.category}
                </td>
                <td style={{
                  padding: '8px 12px', textAlign: 'right',
                  fontVariantNumeric: 'tabular-nums', fontWeight: 600,
                }}>
                  {formatCurrency(a.avg_amount)}
                </td>
                <td style={{
                  padding: '8px 12px', textAlign: 'right',
                  fontVariantNumeric: 'tabular-nums', color: 'var(--text-muted)',
                }}>
                  {a.avg_percent.toFixed(1)}%
                </td>
                <td style={{ padding: '8px 12px', width: '120px' }}>
                  <div style={{
                    height: '10px', borderRadius: '5px', background: 'var(--bg-hover)',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(a.avg_percent, 100)}%`,
                      background: BAR_COLORS[i % BAR_COLORS.length],
                      borderRadius: '5px',
                      opacity: 0.75,
                    }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ---- Main Component ---- */

interface PaycheckTracerProps {
  onBack: () => void
  onPayeeNavigate?: (payee: string) => void
}

export default function PaycheckTracer({ onBack, onPayeeNavigate }: PaycheckTracerProps) {
  const { data: sourcesData } = useIncomeSources()
  const [selectedSourceId, setSelectedSourceId] = useState<number | undefined>(undefined)
  const [numPeriods, setNumPeriods] = useState(6)
  const { data, isLoading } = usePaycheckTracer(selectedSourceId, numPeriods)

  const sources = sourcesData?.sources ?? []
  const periods = data?.periods ?? []
  const averages = data?.category_averages ?? []
  const source = data?.income_source

  const avgPaycheck = periods.length > 0
    ? periods.reduce((s, p) => s + p.paycheck_amount, 0) / periods.length
    : 0

  const avgSpent = periods.filter(p => !p.is_current).length > 0
    ? periods.filter(p => !p.is_current).reduce((s, p) => s + p.total_spent, 0) / periods.filter(p => !p.is_current).length
    : 0

  const avgSaved = avgPaycheck - avgSpent
  const avgSaveRate = avgPaycheck ? (avgSaved / avgPaycheck * 100) : 0

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

      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: '12px',
      }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Paycheck Tracer
        </h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
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
                <option key={s.id} value={s.id}>
                  {s.payee_name.slice(0, 40)} ({s.cadence})
                </option>
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
          {' '}({source.cadence}, ~{formatCurrency(source.expected_amount)})
        </div>
      )}

      {/* Summary cards */}
      {periods.length > 0 && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{
            flex: '1 1 160px', padding: '16px 20px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Avg Paycheck
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
              {formatCurrency(avgPaycheck)}
            </div>
          </div>
          <div style={{
            flex: '1 1 160px', padding: '16px 20px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Avg Spent / Period
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums', marginTop: '4px' }}>
              {formatCurrency(avgSpent)}
            </div>
          </div>
          <div style={{
            flex: '1 1 160px', padding: '16px 20px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Avg {avgSaved >= 0 ? 'Saved' : 'Over'} / Period
            </div>
            <div style={{
              fontSize: '20px', fontWeight: 700, fontVariantNumeric: 'tabular-nums', marginTop: '4px',
              color: avgSaved >= 0 ? 'var(--success)' : 'var(--danger)',
            }}>
              {avgSaved >= 0 ? '+' : ''}{formatCurrency(avgSaved)} ({avgSaveRate >= 0 ? '+' : ''}{avgSaveRate.toFixed(0)}%)
            </div>
          </div>
        </div>
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

      {/* Period cards (most recent first) */}
      {[...periods].reverse().map((p, i) => (
        <PeriodCard key={p.period_start} period={p} onPayeeNavigate={onPayeeNavigate} />
      ))}

      {/* Category averages */}
      <AveragesSection averages={averages} paycheck={avgPaycheck} />
    </div>
  )
}
