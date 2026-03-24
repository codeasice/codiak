import { useState, useRef, useEffect, useMemo } from 'react'
import {
  useQueue, useQueueStats, useCategories, useApprove, useApproveAll, useSkip, useUnskipAll, useCategorize,
} from '../../hooks/dragon-keeper/use-categorization-queue'
import { useToast } from './toast'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (confidence == null) return null
  const pct = Math.round(confidence * 100)
  const color = confidence >= 0.7 ? 'var(--success)' : confidence >= 0.4 ? 'var(--warning)' : 'var(--danger)'
  return (
    <span style={{
      fontSize: '10px', fontWeight: 600, padding: '1px 6px',
      borderRadius: '8px', color,
      background: `color-mix(in srgb, ${color} 12%, transparent)`,
    }}>
      {pct}%
    </span>
  )
}

interface CategoryComboboxProps {
  onSelect: (categoryId: string) => void
  onCancel: () => void
}

function CategoryCombobox({ onSelect, onCancel }: CategoryComboboxProps) {
  const { data } = useCategories()
  const [search, setSearch] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  const grouped = useMemo(() => {
    if (!data?.categories) return {}
    const term = search.toLowerCase()
    const filtered = data.categories.filter(c => c.name.toLowerCase().includes(term) || c.group_name.toLowerCase().includes(term))
    const groups: Record<string, typeof filtered> = {}
    for (const c of filtered) {
      ;(groups[c.group_name] ??= []).push(c)
    }
    return groups
  }, [data, search])

  return (
    <div style={{
      position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 20,
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
      maxHeight: '260px', display: 'flex', flexDirection: 'column',
      minWidth: '240px',
    }}>
      <div style={{ padding: '6px', borderBottom: '1px solid var(--border)' }}>
        <input
          ref={inputRef}
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => { if (e.key === 'Escape') onCancel() }}
          placeholder="Search categories..."
          style={{
            width: '100%', padding: '6px 8px', fontSize: '12px',
            background: 'var(--bg-hover)', border: '1px solid var(--border)',
            borderRadius: '4px', color: 'var(--text-primary)', outline: 'none',
          }}
        />
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {Object.entries(grouped).map(([group, cats]) => (
          <div key={group}>
            <div style={{
              padding: '6px 10px 2px', fontSize: '10px', fontWeight: 700,
              textTransform: 'uppercase', letterSpacing: '0.5px',
              color: 'var(--text-muted)',
            }}>
              {group}
            </div>
            {cats.map(c => (
              <button
                key={c.id}
                onClick={() => onSelect(c.id)}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '5px 10px 5px 16px', fontSize: '12px',
                  background: 'transparent', border: 'none', cursor: 'pointer',
                  color: 'var(--text-primary)',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                {c.name}
              </button>
            ))}
          </div>
        ))}
        {Object.keys(grouped).length === 0 && (
          <div style={{ padding: '12px', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
            No categories found
          </div>
        )}
      </div>
    </div>
  )
}

export default function CategorizationQueue({ onPayeeNavigate }: { onPayeeNavigate?: (payee: string) => void }) {
  const { data, isLoading } = useQueue()
  const { data: stats } = useQueueStats()
  const { data: catData } = useCategories()
  const approve = useApprove()
  const approveAll = useApproveAll()
  const skip = useSkip()
  const unskipAll = useUnskipAll()
  const categorize = useCategorize()
  const { toast } = useToast()
  const [correctingId, setCorrectingId] = useState<string | null>(null)
  const llmAvailable = stats?.llm_available ?? true

  const catNames = useMemo(() => {
    const map: Record<string, string> = {}
    for (const c of catData?.categories ?? []) map[c.id] = c.name
    return map
  }, [catData])

  const [lastResult, setLastResult] = useState<{
    api_calls: number; tokens: number; processed: number; remaining: number
    auto_applied: number; suggested: number; invalid: number
  } | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (categorize.isPending) {
      setElapsed(0)
      timerRef.current = setInterval(() => setElapsed(s => s + 1), 1000)
    } else if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [categorize.isPending])

  type SortKey = 'date' | 'payee' | 'amount' | 'category'
  type SortDir = 'asc' | 'desc'
  const [sortKey, setSortKey] = useState<SortKey>('date')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir(key === 'amount' ? 'desc' : 'asc')
    }
  }

  const rawItems = data?.items ?? []

  const items = useMemo(() => {
    const sorted = [...rawItems]
    const dir = sortDir === 'asc' ? 1 : -1
    sorted.sort((a, b) => {
      switch (sortKey) {
        case 'date':
          return dir * a.date.localeCompare(b.date)
        case 'payee':
          return dir * (a.payee_name ?? '').localeCompare(b.payee_name ?? '')
        case 'amount':
          return dir * (Math.abs(a.amount) - Math.abs(b.amount))
        case 'category':
          return dir * (a.suggested_category_name ?? '').localeCompare(b.suggested_category_name ?? '')
        default:
          return 0
      }
    })
    return sorted
  }, [rawItems, sortKey, sortDir])

  const approvableCount = items.filter(i => i.suggested_category_id).length
  const awaitingLlm = stats?.awaiting_llm ?? 0
  const llmBatchSize = stats?.llm_batch_size ?? 50

  if (isLoading) {
    return (
      <div style={{
        padding: '24px', background: 'var(--bg-card)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
      }}>
        <div style={{
          width: '160px', height: '14px', background: 'var(--bg-hover)',
          borderRadius: '4px', marginBottom: '16px',
        }} />
        {[1, 2, 3].map(i => (
          <div key={i} style={{
            height: '44px', background: 'var(--bg-hover)',
            borderRadius: '4px', marginBottom: '8px',
          }} />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div style={{
        padding: '32px 24px', background: 'var(--bg-card)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '28px', marginBottom: '8px' }}>&#10003;</div>
        <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
          All caught up!
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          No transactions need review right now.
        </div>
      </div>
    )
  }

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 20px', borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Review Queue
          <span style={{
            marginLeft: '8px', fontSize: '11px', fontWeight: 500,
            color: 'var(--text-muted)',
          }}>
            {items.length} item{items.length !== 1 ? 's' : ''}
          </span>
          {(stats?.skipped_count ?? 0) > 0 && (
            <span style={{ marginLeft: '8px', fontSize: '11px', fontWeight: 500 }}>
              <span style={{ color: 'var(--text-muted)' }}>
                · {stats!.skipped_count} skipped
              </span>
              <button
                onClick={() => unskipAll.mutate(undefined, {
                  onSuccess: (res: any) => toast(`Restored ${res.count} skipped item${res.count !== 1 ? 's' : ''} to queue`, 'success'),
                })}
                disabled={unskipAll.isPending}
                style={{
                  marginLeft: '4px', padding: '0 4px', fontSize: '11px', fontWeight: 600,
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--accent)', textDecoration: 'underline',
                }}
              >
                {unskipAll.isPending ? 'restoring...' : 'undo'}
              </button>
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button
            onClick={() => categorize.mutate({ reprocess: true, llm_limit: llmBatchSize }, {
              onSuccess: (result) => {
                const llm = result.llm_categorizer
                setLastResult({
                  api_calls: llm.api_calls,
                  tokens: llm.tokens?.total_tokens ?? 0,
                  processed: llm.processed,
                  remaining: llm.remaining,
                  auto_applied: llm.auto_applied,
                  suggested: llm.suggested,
                  invalid: (llm as any).invalid_suggestions ?? 0,
                })
                const parts: string[] = []
                if (llm.auto_applied > 0) parts.push(`${llm.auto_applied} auto-applied`)
                if (llm.suggested > 0) parts.push(`${llm.suggested} suggested`)
                if (parts.length > 0) {
                  toast(`Categorized: ${parts.join(', ')}`, 'success')
                } else if (llm.skipped) {
                  toast('LLM skipped — API key missing', 'warning')
                } else {
                  toast('No new categorizations this batch', 'info')
                }
              },
            })}
            disabled={categorize.isPending}
            title={`Re-run rules + LLM on pending items (batch of up to ${llmBatchSize})`}
            style={{
              padding: '5px 12px', fontSize: '11px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent',
              color: 'var(--accent)',
              opacity: categorize.isPending ? 0.6 : 1,
            }}
          >
            {categorize.isPending
              ? `Running... ${elapsed}s`
              : `Categorize${awaitingLlm > 0 ? ` (${awaitingLlm})` : ''}`}
          </button>
          {approvableCount >= 3 && (
            <button
              onClick={() => approveAll.mutate(undefined, {
                onSuccess: (res: any) => toast(`Approved ${res.approved_count} transactions`, 'success'),
              })}
              disabled={approveAll.isPending}
              style={{
                padding: '5px 12px', fontSize: '11px', fontWeight: 600,
                borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                background: `color-mix(in srgb, var(--success) 15%, transparent)`,
                color: 'var(--success)',
                opacity: approveAll.isPending ? 0.6 : 1,
              }}
            >
              {approveAll.isPending ? 'Approving...' : `Approve All (${approvableCount})`}
            </button>
          )}
        </div>
      </div>

      {lastResult && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap',
          padding: '8px 20px', fontSize: '11px',
          background: lastResult.processed > 0
            ? 'color-mix(in srgb, var(--success) 6%, transparent)'
            : 'color-mix(in srgb, var(--warning) 6%, transparent)',
          borderBottom: '1px solid var(--border)',
          color: 'var(--text-muted)',
        }}>
          {lastResult.auto_applied > 0 && (
            <span style={{ color: 'var(--success)' }}>
              {lastResult.auto_applied} auto-applied
            </span>
          )}
          {lastResult.suggested > 0 && (
            <span>{lastResult.suggested} suggested for review</span>
          )}
          {lastResult.processed === 0 && lastResult.api_calls > 0 && (
            <span style={{ color: 'var(--warning)' }}>No matches from LLM</span>
          )}
          {lastResult.invalid > 0 && (
            <span style={{ color: 'var(--danger)' }}>{lastResult.invalid} invalid</span>
          )}
          <span style={{ opacity: 0.7 }}>
            {lastResult.api_calls} call{lastResult.api_calls !== 1 ? 's' : ''} &middot; {lastResult.tokens.toLocaleString()} tokens
          </span>
          {lastResult.remaining > 0 && (
            <span style={{ color: 'var(--warning)' }}>
              {lastResult.remaining.toLocaleString()} still awaiting
            </span>
          )}
          <button
            onClick={() => setLastResult(null)}
            style={{
              marginLeft: 'auto', background: 'none', border: 'none',
              color: 'var(--text-muted)', cursor: 'pointer', fontSize: '13px', padding: '0 4px',
            }}
          >
            &times;
          </button>
        </div>
      )}

      {!llmAvailable && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '10px 20px', fontSize: '12px',
          background: 'color-mix(in srgb, var(--warning) 10%, transparent)',
          borderBottom: '1px solid color-mix(in srgb, var(--warning) 30%, transparent)',
          color: 'var(--warning)',
        }}>
          <span style={{ fontSize: '14px' }}>&#9888;</span>
          <span>
            <strong>OPENAI_API_KEY</strong> not set — AI categorization is disabled.
            Add it to your <code>.env</code> file and restart the server.
          </span>
        </div>
      )}

      <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '480px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead style={{ position: 'sticky', top: 0, zIndex: 2, background: 'var(--bg-card)' }}>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {([
                { label: 'Date', key: 'date' as SortKey, align: 'left' },
                { label: 'Payee / Merchant', key: 'payee' as SortKey, align: 'left' },
                { label: 'Amount', key: 'amount' as SortKey, align: 'right' },
                { label: 'Suggested Category', key: 'category' as SortKey, align: 'left' },
                { label: '', key: null, align: 'left' },
              ]).map((col, i) => (
                <th
                  key={i}
                  onClick={col.key ? () => toggleSort(col.key!) : undefined}
                  style={{
                    padding: '10px 12px', textAlign: col.align as any,
                    fontSize: '10px', fontWeight: 700, textTransform: 'uppercase',
                    letterSpacing: '0.5px', whiteSpace: 'nowrap',
                    color: sortKey === col.key ? 'var(--accent)' : 'var(--text-muted)',
                    cursor: col.key ? 'pointer' : 'default',
                    userSelect: 'none',
                  }}
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span style={{ marginLeft: '4px', fontSize: '9px' }}>
                      {sortDir === 'asc' ? '\u25B2' : '\u25BC'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map(item => {
              const isCorrecting = correctingId === item.id
              return (
                <tr
                  key={item.id}
                  style={{ borderBottom: '1px solid var(--border)' }}
                  onMouseEnter={e => {
                    for (const td of e.currentTarget.children as any)
                      td.style.background = 'var(--bg-hover)'
                  }}
                  onMouseLeave={e => {
                    for (const td of e.currentTarget.children as any)
                      td.style.background = 'transparent'
                  }}
                >
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
                    {formatDate(item.date)}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                      {onPayeeNavigate && item.payee_name ? (
                        <span
                          onClick={() => onPayeeNavigate(item.payee_name!)}
                          style={{ cursor: 'pointer', borderBottom: '1px dashed var(--text-muted)' }}
                          onMouseEnter={e => { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)' }}
                          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--text-muted)' }}
                          title={`View all transactions for ${item.payee_name}`}
                        >
                          {item.payee_name}
                        </span>
                      ) : (
                        item.payee_name || 'Unknown'
                      )}
                    </div>
                    {item.memo && (
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '1px' }}>
                        {item.memo}
                      </div>
                    )}
                  </td>
                  <td style={{
                    padding: '10px 12px', textAlign: 'right', whiteSpace: 'nowrap',
                    fontVariantNumeric: 'tabular-nums',
                    color: item.amount < 0 ? 'var(--text-primary)' : 'var(--success)',
                  }}>
                    {formatCurrency(item.amount)}
                  </td>
                  <td style={{ padding: '10px 12px', position: 'relative' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: 'var(--text-primary)', fontSize: '12px' }}>
                        {item.suggested_category_name || '—'}
                      </span>
                      <ConfidenceBadge confidence={item.suggestion_confidence} />
                      {item.suggestion_source && (
                        <span style={{
                          fontSize: '9px', padding: '1px 5px', borderRadius: '4px',
                          background: 'var(--bg-hover)', color: 'var(--text-muted)',
                          textTransform: 'uppercase', fontWeight: 600,
                        }}>
                          {item.suggestion_source}
                        </span>
                      )}
                    </div>
                    {isCorrecting && (
                      <CategoryCombobox
                        onSelect={(categoryId) => {
                          const catName = catNames[categoryId] || 'selected category'
                          approve.mutate(
                            { transaction_id: item.id, category_id: categoryId },
                            { onSuccess: () => toast(`Corrected "${item.payee_name}" → ${catName}`, 'success') },
                          )
                          setCorrectingId(null)
                        }}
                        onCancel={() => setCorrectingId(null)}
                      />
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '4px' }}>
                      {item.suggested_category_id && (
                        <button
                          onClick={() => {
                            const catName = item.suggested_category_name || catNames[item.suggested_category_id!] || 'suggestion'
                            approve.mutate(
                              { transaction_id: item.id, category_id: item.suggested_category_id! },
                              { onSuccess: () => toast(`Approved "${item.payee_name}" → ${catName}`, 'success') },
                            )
                          }}
                          disabled={approve.isPending}
                          title="Approve suggestion"
                          style={{
                            padding: '4px 10px', fontSize: '11px', fontWeight: 600,
                            borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                            background: `color-mix(in srgb, var(--success) 15%, transparent)`,
                            color: 'var(--success)',
                          }}
                        >
                          Approve
                        </button>
                      )}
                      <button
                        onClick={() => setCorrectingId(isCorrecting ? null : item.id)}
                        title="Choose a different category"
                        style={{
                          padding: '4px 10px', fontSize: '11px', fontWeight: 600,
                          borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                          cursor: 'pointer', background: 'transparent',
                          color: 'var(--accent)',
                        }}
                      >
                        Correct
                      </button>
                      <button
                        onClick={() => skip.mutate(
                          { transaction_id: item.id },
                          { onSuccess: () => toast(`Skipped "${item.payee_name}"`, 'info') },
                        )}
                        disabled={skip.isPending}
                        title="Skip this transaction"
                        style={{
                          padding: '4px 10px', fontSize: '11px', fontWeight: 600,
                          borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                          background: 'var(--bg-hover)', color: 'var(--text-muted)',
                        }}
                      >
                        Skip
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
