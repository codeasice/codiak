import { useEffect, useRef, useState } from 'react'
import { useRulePreview, useReclassify } from '../../hooks/dragon-keeper/use-rule-preview'
import { useToast } from './toast'

interface RulePreviewProps {
  payeePattern: string
  matchType: string
  minAmount?: number
  maxAmount?: number
  categoryId?: string
  categoryName?: string
  onReclassify?: (count: number) => void
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function RulePreview({
  payeePattern,
  matchType,
  minAmount,
  maxAmount,
  categoryId,
  categoryName,
  onReclassify,
}: RulePreviewProps) {
  const preview = useRulePreview()
  const reclassify = useReclassify()
  const { toast } = useToast()
  const [confirmed, setConfirmed] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastParamsRef = useRef('')

  useEffect(() => {
    if (!payeePattern.trim()) return

    const key = JSON.stringify({ payeePattern, matchType, minAmount, maxAmount })
    if (key === lastParamsRef.current) return
    lastParamsRef.current = key

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      preview.mutate({ payee_pattern: payeePattern, match_type: matchType, min_amount: minAmount, max_amount: maxAmount })
    }, 300)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [payeePattern, matchType, minAmount, maxAmount])

  useEffect(() => {
    setConfirmed(false)
  }, [payeePattern, matchType, minAmount, maxAmount, categoryId])

  if (!payeePattern.trim()) return null

  const isLoading = preview.isPending
  const data = preview.data
  const count = data?.count ?? 0
  const samples = data?.samples ?? []

  if (isLoading) {
    return (
      <div style={{
        padding: '12px 16px', background: 'var(--bg-card)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius)',
      }}>
        <div style={{
          width: '140px', height: '12px', background: 'var(--bg-hover)',
          borderRadius: '4px', marginBottom: '10px',
        }} />
        {[1, 2, 3].map(i => (
          <div key={i} style={{
            height: '32px', background: 'var(--bg-hover)',
            borderRadius: '4px', marginBottom: '6px',
          }} />
        ))}
      </div>
    )
  }

  if (preview.isError) {
    return (
      <div style={{
        padding: '10px 16px', fontSize: '12px', color: 'var(--danger)',
        background: 'color-mix(in srgb, var(--danger) 8%, transparent)',
        border: '1px solid color-mix(in srgb, var(--danger) 25%, var(--border))',
        borderRadius: 'var(--radius)',
      }}>
        Preview failed: {preview.error.message}
      </div>
    )
  }

  if (!data) return null

  if (count === 0) {
    return (
      <div style={{
        padding: '10px 16px', fontSize: '12px', color: 'var(--text-muted)',
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
      }}>
        No matching transactions
      </div>
    )
  }

  const handleReclassify = () => {
    if (!categoryId) return
    reclassify.mutate(
      { payee_pattern: payeePattern, match_type: matchType, category_id: categoryId, min_amount: minAmount, max_amount: maxAmount },
      {
        onSuccess: (res) => {
          toast(`Reclassified ${res.reclassified_count} transaction${res.reclassified_count !== 1 ? 's' : ''}`, 'success')
          onReclassify?.(res.reclassified_count)
          setConfirmed(false)
          preview.mutate({ payee_pattern: payeePattern, match_type: matchType, min_amount: minAmount, max_amount: maxAmount })
        },
        onError: (err) => {
          toast(`Reclassify failed: ${err.message}`, 'error')
        },
      },
    )
  }

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px', borderBottom: '1px solid var(--border)',
      }}>
        <span style={{ fontSize: '12px', color: 'var(--text-primary)', fontWeight: 600 }}>
          {count.toLocaleString()} matching transaction{count !== 1 ? 's' : ''}
          {count > samples.length && (
            <span style={{ fontWeight: 400, color: 'var(--text-muted)', marginLeft: '6px' }}>
              (showing {samples.length})
            </span>
          )}
        </span>
      </div>

      {/* Sample table */}
      <div style={{ overflowX: 'auto', maxHeight: '320px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead style={{ position: 'sticky', top: 0, zIndex: 1, background: 'var(--bg-card)' }}>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Date', 'Payee', 'Amount', 'Current Category'].map(label => (
                <th key={label} style={{
                  padding: '7px 12px', textAlign: label === 'Amount' ? 'right' : 'left',
                  fontSize: '10px', fontWeight: 700, textTransform: 'uppercase',
                  letterSpacing: '0.5px', color: 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                }}>
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {samples.map(s => {
              const wouldChange = categoryId && s.category_id !== categoryId
              return (
                <tr
                  key={s.id}
                  style={{
                    borderBottom: '1px solid var(--border)',
                    background: wouldChange
                      ? 'color-mix(in srgb, var(--warning) 6%, transparent)'
                      : 'transparent',
                  }}
                  onMouseEnter={e => {
                    for (const td of e.currentTarget.children as any)
                      td.style.background = 'var(--bg-hover)'
                  }}
                  onMouseLeave={e => {
                    const bg = wouldChange
                      ? 'color-mix(in srgb, var(--warning) 6%, transparent)'
                      : 'transparent'
                    for (const td of e.currentTarget.children as any)
                      td.style.background = bg
                  }}
                >
                  <td style={{ padding: '8px 12px', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
                    {formatDate(s.date)}
                  </td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-primary)', fontWeight: 500 }}>
                    {s.payee_name || 'Unknown'}
                  </td>
                  <td style={{
                    padding: '8px 12px', textAlign: 'right', whiteSpace: 'nowrap',
                    fontVariantNumeric: 'tabular-nums',
                    color: s.amount < 0 ? 'var(--text-primary)' : 'var(--success)',
                  }}>
                    {formatCurrency(s.amount)}
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <span style={{
                      color: wouldChange ? 'var(--warning)' : 'var(--text-muted)',
                      fontSize: '11px',
                    }}>
                      {s.category_name || '—'}
                    </span>
                    {wouldChange && categoryName && (
                      <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                        {' → '}
                        <span style={{ color: 'var(--success)' }}>{categoryName}</span>
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Reclassify action */}
      {categoryId && count > 0 && (
        <div style={{
          padding: '10px 14px', borderTop: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          {!confirmed ? (
            <button
              onClick={() => setConfirmed(true)}
              style={{
                padding: '6px 14px', fontSize: '12px', fontWeight: 600,
                borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                background: 'color-mix(in srgb, var(--accent) 15%, transparent)',
                color: 'var(--accent)',
              }}
            >
              Reclassify {count.toLocaleString()} transaction{count !== 1 ? 's' : ''} → {categoryName || 'selected'}
            </button>
          ) : (
            <>
              <span style={{ fontSize: '12px', color: 'var(--warning)' }}>
                Reclassify {count.toLocaleString()} transaction{count !== 1 ? 's' : ''}?
              </span>
              <button
                onClick={handleReclassify}
                disabled={reclassify.isPending}
                style={{
                  padding: '5px 12px', fontSize: '11px', fontWeight: 600,
                  borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                  background: 'color-mix(in srgb, var(--success) 15%, transparent)',
                  color: 'var(--success)',
                  opacity: reclassify.isPending ? 0.6 : 1,
                }}
              >
                {reclassify.isPending ? 'Working...' : 'Confirm'}
              </button>
              <button
                onClick={() => setConfirmed(false)}
                disabled={reclassify.isPending}
                style={{
                  padding: '5px 12px', fontSize: '11px', fontWeight: 600,
                  borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                  cursor: 'pointer', background: 'transparent',
                  color: 'var(--text-muted)',
                }}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
