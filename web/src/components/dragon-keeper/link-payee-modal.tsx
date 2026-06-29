import { useEffect, useMemo, useState } from 'react'
import {
  useLinkPreview,
  useLinkPreviewByPayeeName,
  useLinkRecurring,
  type LinkPreview,
  type RecurringItem,
} from '../../hooks/dragon-keeper/use-recurring'
import Sparkline from './sparkline'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

type LinkMode = 'subscription' | 'payee_name'

interface LinkPayeeModalProps {
  anchorItem: RecurringItem
  candidates: RecurringItem[]
  initialSourceId?: number | null
  onClose: () => void
  onLinked: (message: string) => void
  onError: (message: string) => void
}

function severityColor(severity: LinkPreview['warnings'][0]['severity']): string {
  if (severity === 'error') return 'var(--danger)'
  if (severity === 'warning') return 'var(--warning, #f59e0b)'
  return 'var(--text-muted)'
}

function PreviewPanel({
  preview,
  previewLoading,
  hasAmountError,
  blockingErrors,
  forceAmount,
  setForceAmount,
}: {
  preview: LinkPreview | undefined
  previewLoading: boolean
  hasAmountError: boolean
  blockingErrors: LinkPreview['warnings']
  forceAmount: boolean
  setForceAmount: (v: boolean) => void
}) {
  if (previewLoading) {
    return <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Loading preview…</div>
  }
  if (!preview) return null

  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: 'var(--radius)',
      padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '10px',
    }}>
      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
        Combined history
      </div>
      <Sparkline
        points={preview.combined_charge_history.map(c => ({ date: c.date, value: c.amount }))}
      />
      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
        {preview.combined_occurrence_count} occurrences
        {preview.combined_last_seen ? ` · last seen ${preview.combined_last_seen}` : ''}
      </div>
      {preview.warnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {preview.warnings.map((w, i) => (
            <div key={i} style={{ fontSize: '12px', color: severityColor(w.severity) }}>
              {w.severity === 'error' ? '✕' : w.severity === 'warning' ? '!' : '·'} {w.message}
            </div>
          ))}
        </div>
      )}
      {hasAmountError && blockingErrors.length === 0 && (
        <label style={{
          display: 'flex', alignItems: 'flex-start', gap: '8px',
          fontSize: '12px', color: 'var(--text-primary)', cursor: 'pointer',
        }}>
          <input
            type="checkbox"
            checked={forceAmount}
            onChange={e => setForceAmount(e.target.checked)}
            style={{ marginTop: '2px' }}
          />
          These are the same subscription despite the amount difference
        </label>
      )}
    </div>
  )
}

export default function LinkPayeeModal({
  anchorItem,
  candidates,
  initialSourceId = null,
  onClose,
  onLinked,
  onError,
}: LinkPayeeModalProps) {
  const link = useLinkRecurring()
  const [mode, setMode] = useState<LinkMode>(initialSourceId ? 'subscription' : 'subscription')
  const [sourceId, setSourceId] = useState<number | null>(initialSourceId)
  const [payeeName, setPayeeName] = useState('')
  const [canonicalId, setCanonicalId] = useState<number>(anchorItem.id)
  const [forceAmount, setForceAmount] = useState(false)

  const sourceItem = useMemo(
    () => candidates.find(c => c.id === sourceId) ?? null,
    [candidates, sourceId],
  )

  const subscriptionPreviewEnabled = mode === 'subscription' && sourceId != null
  const payeePreviewEnabled = mode === 'payee_name' && payeeName.trim().length > 0

  const { data: subscriptionPreview, isLoading: subscriptionPreviewLoading } = useLinkPreview(
    anchorItem.id,
    sourceId,
    canonicalId,
    subscriptionPreviewEnabled,
  )
  const { data: payeePreview, isLoading: payeePreviewLoading } = useLinkPreviewByPayeeName(
    anchorItem.id,
    payeeName.trim(),
    payeePreviewEnabled,
  )

  const preview = mode === 'subscription' ? subscriptionPreview : payeePreview
  const previewLoading = mode === 'subscription' ? subscriptionPreviewLoading : payeePreviewLoading

  useEffect(() => {
    if (initialSourceId != null) {
      setSourceId(initialSourceId)
      setMode('subscription')
    }
  }, [initialSourceId])

  useEffect(() => {
    if (sourceId != null) {
      setCanonicalId(anchorItem.id)
      setForceAmount(false)
    }
  }, [sourceId, anchorItem.id])

  useEffect(() => {
    if (payeeName.trim()) {
      setForceAmount(false)
    }
  }, [payeeName])

  const hasAmountError = preview?.warnings.some(
    w => w.code === 'amount_mismatch' && w.severity === 'error',
  )
  const blockingErrors = preview?.warnings.filter(w => w.severity === 'error' && w.code !== 'amount_mismatch') ?? []
  const previewReady = (subscriptionPreviewEnabled || payeePreviewEnabled) && preview && !previewLoading
  const canCombine = previewReady
    && blockingErrors.length === 0
    && (!preview.blocking || (hasAmountError && forceAmount))

  const handleCombine = () => {
    if (mode === 'subscription') {
      if (!sourceId) return
      link.mutate(
        {
          itemId: anchorItem.id,
          source_recurring_id: sourceId,
          canonical_recurring_id: canonicalId,
          force_amount: forceAmount,
        },
        {
          onSuccess: () => {
            const kept = canonicalId === anchorItem.id ? anchorItem.payee_name : sourceItem?.payee_name
            const linked = canonicalId === anchorItem.id ? sourceItem?.payee_name : anchorItem.payee_name
            onLinked(`Linked "${linked}" to "${kept}"`)
            onClose()
          },
          onError: () => onError('Failed to combine payees'),
        },
      )
      return
    }

    const name = payeeName.trim()
    if (!name) return
    link.mutate(
      {
        itemId: anchorItem.id,
        payee_name: name,
        force_amount: forceAmount,
      },
      {
        onSuccess: () => {
          onLinked(`Linked "${name}" to "${anchorItem.payee_name}"`)
          onClose()
        },
        onError: () => onError('Failed to link payee'),
      },
    )
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '24px',
        width: 'min(520px, 92vw)', maxHeight: '85vh', overflow: 'auto',
        display: 'flex', flexDirection: 'column', gap: '16px',
      }} onClick={e => e.stopPropagation()}>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
            Combine payees
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Link a duplicate payee name to "{anchorItem.payee_name}" so charges roll up together.
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {([
            ['subscription', 'From list'],
            ['payee_name', 'By payee name'],
          ] as const).map(([value, label]) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              style={{
                padding: '6px 12px', fontSize: '11px', fontWeight: 600,
                borderRadius: 'var(--radius)',
                border: `1px solid ${mode === value ? 'var(--accent)' : 'var(--border)'}`,
                background: mode === value ? 'color-mix(in srgb, var(--accent) 12%, transparent)' : 'transparent',
                color: mode === value ? 'var(--accent)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {mode === 'subscription' ? (
          <>
            <div>
              <label style={{
                fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)',
                textTransform: 'uppercase', letterSpacing: '0.5px',
              }}>
                Other subscription
              </label>
              <select
                value={sourceId ?? ''}
                onChange={e => setSourceId(e.target.value ? Number(e.target.value) : null)}
                style={{
                  display: 'block', marginTop: '6px', width: '100%', boxSizing: 'border-box',
                  padding: '8px 10px', borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)', background: 'var(--bg)',
                  color: 'var(--text-primary)', fontSize: '13px',
                }}
              >
                <option value="">Select a payee…</option>
                {candidates.map(item => (
                  <option key={item.id} value={item.id}>
                    {item.payee_name} ({formatCurrency(item.expected_amount)}/{item.cadence})
                  </option>
                ))}
              </select>
            </div>

            {sourceItem && (
              <div>
                <label style={{
                  fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)',
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                }}>
                  Keep as primary row
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                  {[anchorItem, sourceItem].map(item => (
                    <label key={item.id} style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      fontSize: '13px', color: 'var(--text-primary)', cursor: 'pointer',
                    }}>
                      <input
                        type="radio"
                        name="canonical"
                        checked={canonicalId === item.id}
                        onChange={() => setCanonicalId(item.id)}
                      />
                      {item.payee_name}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div>
            <label style={{
              fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)',
              textTransform: 'uppercase', letterSpacing: '0.5px',
            }}>
              Payee name from transactions
            </label>
            <input
              type="text"
              value={payeeName}
              onChange={e => setPayeeName(e.target.value)}
              placeholder="e.g. NETFLIX.COM"
              style={{
                display: 'block', marginTop: '6px', width: '100%', boxSizing: 'border-box',
                padding: '8px 10px', borderRadius: 'var(--radius)',
                border: '1px solid var(--border)', background: 'var(--bg)',
                color: 'var(--text-primary)', fontSize: '13px',
              }}
            />
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
              Use when the payee appears in transactions but not as its own subscription row.
            </div>
          </div>
        )}

        <PreviewPanel
          preview={preview}
          previewLoading={Boolean((subscriptionPreviewEnabled || payeePreviewEnabled) && previewLoading)}
          hasAmountError={!!hasAmountError}
          blockingErrors={blockingErrors}
          forceAmount={forceAmount}
          setForceAmount={setForceAmount}
        />

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleCombine}
            disabled={!canCombine || link.isPending}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: 'none', cursor: canCombine ? 'pointer' : 'not-allowed',
              background: canCombine ? 'var(--accent)' : 'var(--bg-hover)',
              color: canCombine ? '#fff' : 'var(--text-muted)',
              opacity: link.isPending ? 0.7 : 1,
            }}
          >
            {link.isPending ? 'Combining…' : 'Combine'}
          </button>
        </div>
      </div>
    </div>
  )
}
