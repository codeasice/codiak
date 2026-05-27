import { useState, useRef, useEffect } from 'react'
import { usePayeeMap, useUpdatePayee, type PayeeMeta } from '../../hooks/dragon-keeper/use-payees'

interface EditPopoverProps {
  meta: PayeeMeta
  anchor: DOMRect
  onClose: () => void
}

function EditPopover({ meta, anchor, onClose }: EditPopoverProps) {
  const update = useUpdatePayee()
  const [displayName, setDisplayName] = useState(meta.display_name ?? '')
  const [note, setNote] = useState(meta.note ?? '')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [onClose])

  function save() {
    update.mutate(
      {
        id: meta.id,
        display_name: displayName.trim() || null,
        note: note.trim() || null,
      },
      { onSuccess: onClose },
    )
  }

  const top = anchor.bottom + window.scrollY + 6
  const left = anchor.left + window.scrollX

  return (
    <div
      ref={ref}
      style={{
        position: 'absolute', top, left, zIndex: 2000,
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '14px 16px',
        display: 'flex', flexDirection: 'column', gap: '10px',
        width: '260px', boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
      }}
    >
      <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Edit Payee
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
        {meta.name}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>Display Name</label>
        <input
          autoFocus
          value={displayName}
          onChange={e => setDisplayName(e.target.value)}
          placeholder={meta.name}
          onKeyDown={e => { if (e.key === 'Enter') save(); if (e.key === 'Escape') onClose() }}
          style={{
            padding: '6px 8px', fontSize: '12px', borderRadius: 'var(--radius)',
            border: '1px solid var(--border)', background: 'var(--bg)',
            color: 'var(--text-primary)', width: '100%', boxSizing: 'border-box',
          }}
        />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>Note</label>
        <input
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder="Add a note…"
          onKeyDown={e => { if (e.key === 'Enter') save(); if (e.key === 'Escape') onClose() }}
          style={{
            padding: '6px 8px', fontSize: '12px', borderRadius: 'var(--radius)',
            border: '1px solid var(--border)', background: 'var(--bg)',
            color: 'var(--text-primary)', width: '100%', boxSizing: 'border-box',
          }}
        />
      </div>
      <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
        <button
          onClick={onClose}
          style={{
            padding: '5px 12px', fontSize: '11px', fontWeight: 600,
            borderRadius: 'var(--radius)', border: '1px solid var(--border)',
            background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          onClick={save}
          disabled={update.isPending}
          style={{
            padding: '5px 12px', fontSize: '11px', fontWeight: 600,
            borderRadius: 'var(--radius)', border: 'none',
            background: 'var(--accent)', color: '#fff', cursor: 'pointer',
          }}
        >
          Save
        </button>
      </div>
    </div>
  )
}

interface PayeeNameProps {
  /** Raw YNAB payee name — used for lookup and shown as secondary label when display_name is set. */
  payeeName: string
  onClick?: () => void
  style?: React.CSSProperties
}

export default function PayeeName({ payeeName, onClick, style }: PayeeNameProps) {
  const payeeMap = usePayeeMap()
  const [editing, setEditing] = useState(false)
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null)
  const penRef = useRef<HTMLButtonElement>(null)

  const meta = payeeMap.get(payeeName.toLowerCase())
  const displayName = meta?.display_name ?? null
  const note = meta?.note ?? null
  const hasAlias = !!displayName

  function openEdit(e: React.MouseEvent) {
    e.stopPropagation()
    if (!meta) return
    setAnchorRect(penRef.current?.getBoundingClientRect() ?? null)
    setEditing(true)
  }

  return (
    <>
      <span
        style={{ display: 'inline-flex', flexDirection: 'column', gap: '1px', ...style }}
        title={note ?? undefined}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          {hasAlias && (
            <span style={{ fontSize: '10px', color: 'var(--accent)', lineHeight: 1, flexShrink: 0 }} title="Custom display name">✎</span>
          )}
          <span
            onClick={onClick}
            style={{
              cursor: onClick ? 'pointer' : 'default',
              borderBottom: onClick ? '1px dashed var(--text-muted)' : 'none',
              fontWeight: 500,
              color: 'var(--text-primary)',
            }}
            onMouseEnter={e => { if (onClick) { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)' } }}
            onMouseLeave={e => { if (onClick) { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--text-muted)' } }}
          >
            {displayName ?? payeeName}
          </span>
          {meta && (
            <button
              ref={penRef}
              onClick={openEdit}
              title="Edit display name / note"
              style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: '0 2px',
                fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1, flexShrink: 0,
                opacity: 0,
              }}
              className="payee-edit-btn"
            >
              ✎
            </button>
          )}
        </span>
        {hasAlias && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.2 }}>
            {payeeName}
          </span>
        )}
      </span>

      {editing && meta && anchorRect && (
        <EditPopover meta={meta} anchor={anchorRect} onClose={() => setEditing(false)} />
      )}
    </>
  )
}
