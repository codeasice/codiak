import { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import { useRules, useCreateRule, useUpdateRule, useDeleteRule, useRestoreRule, type Rule } from '../../hooks/dragon-keeper/use-rules'
import { useCategories } from '../../hooks/dragon-keeper/use-categorization-queue'
import { useToast } from './toast'
import RulePreview from './rule-preview'

const MATCH_TYPES = ['exact', 'contains', 'starts_with'] as const

interface RuleFormData {
  payee_pattern: string
  match_type: string
  category_id: string
  min_amount: string
  max_amount: string
}

const EMPTY_FORM: RuleFormData = {
  payee_pattern: '',
  match_type: 'contains',
  category_id: '',
  min_amount: '',
  max_amount: '',
}

function ruleToForm(rule: Rule): RuleFormData {
  return {
    payee_pattern: rule.payee_pattern,
    match_type: rule.match_type,
    category_id: rule.category_id,
    min_amount: rule.min_amount != null ? String(rule.min_amount) : '',
    max_amount: rule.max_amount != null ? String(rule.max_amount) : '',
  }
}

function formToPayload(form: RuleFormData) {
  return {
    payee_pattern: form.payee_pattern.trim(),
    match_type: form.match_type,
    category_id: form.category_id,
    min_amount: form.min_amount ? parseFloat(form.min_amount) : null,
    max_amount: form.max_amount ? parseFloat(form.max_amount) : null,
  }
}

/* ------------------------------------------------------------------ */
/* Category Combobox (dropdown variant)                                */
/* ------------------------------------------------------------------ */

function CategorySelect({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const { data } = useCategories()
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const selectedName = useMemo(() => {
    if (!value || !data?.categories) return ''
    const cat = data.categories.find(c => c.id === value)
    return cat ? `${cat.group_name} > ${cat.name}` : value
  }, [value, data])

  const grouped = useMemo(() => {
    if (!data?.categories) return {}
    const term = search.toLowerCase()
    const filtered = data.categories.filter(
      c => c.name.toLowerCase().includes(term) || c.group_name.toLowerCase().includes(term),
    )
    const groups: Record<string, typeof filtered> = {}
    for (const c of filtered) {
      ;(groups[c.group_name] ??= []).push(c)
    }
    return groups
  }, [data, search])

  return (
    <div ref={containerRef} style={{ position: 'relative', flex: 1, minWidth: '180px' }}>
      <button
        type="button"
        onClick={() => { setOpen(!open); setSearch('') }}
        style={{
          width: '100%', padding: '6px 8px', fontSize: '12px', textAlign: 'left',
          background: 'var(--bg-hover)', border: '1px solid var(--border)',
          borderRadius: '4px', color: value ? 'var(--text-primary)' : 'var(--text-muted)',
          cursor: 'pointer', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}
      >
        {selectedName || 'Select category...'}
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 30,
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius)', boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
          maxHeight: '240px', display: 'flex', flexDirection: 'column',
          minWidth: '240px', marginTop: '2px',
        }}>
          <div style={{ padding: '6px', borderBottom: '1px solid var(--border)' }}>
            <input
              ref={inputRef}
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => { if (e.key === 'Escape') setOpen(false) }}
              placeholder="Search categories..."
              style={{
                width: '100%', padding: '6px 8px', fontSize: '12px',
                background: 'var(--bg-hover)', border: '1px solid var(--border)',
                borderRadius: '4px', color: 'var(--text-primary)', outline: 'none',
                boxSizing: 'border-box',
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
                    type="button"
                    onClick={() => { onChange(c.id); setOpen(false) }}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: '5px 10px 5px 16px', fontSize: '12px',
                      background: c.id === value ? 'var(--bg-hover)' : 'transparent',
                      border: 'none', cursor: 'pointer', color: 'var(--text-primary)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                    onMouseLeave={e => (e.currentTarget.style.background = c.id === value ? 'var(--bg-hover)' : 'transparent')}
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
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Inline rule form (shared for create + edit)                         */
/* ------------------------------------------------------------------ */

function RuleForm({
  initial,
  onSave,
  onCancel,
  saving,
}: {
  initial: RuleFormData
  onSave: (data: RuleFormData) => void
  onCancel: () => void
  saving: boolean
}) {
  const [form, setForm] = useState<RuleFormData>(initial)
  const catData = useCategories()
  const set = (field: keyof RuleFormData) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }))

  const valid = form.payee_pattern.trim() && form.category_id

  const selectedCatName = useMemo(() => {
    if (!form.category_id || !catData.data?.categories) return ''
    const cat = catData.data.categories.find((c: any) => c.id === form.category_id)
    return cat ? `${cat.group_name} > ${cat.name}` : ''
  }, [form.category_id, catData.data])

  const inputStyle: React.CSSProperties = {
    padding: '6px 8px', fontSize: '12px',
    background: 'var(--bg-hover)', border: '1px solid var(--border)',
    borderRadius: '4px', color: 'var(--text-primary)', outline: 'none',
    boxSizing: 'border-box',
  }

  return (
    <>
    <tr style={{ background: 'color-mix(in srgb, var(--accent) 5%, transparent)' }}>
      <td style={{ padding: '8px 12px' }}>
        <input
          value={form.payee_pattern}
          onChange={set('payee_pattern')}
          placeholder="Payee pattern"
          autoFocus
          style={{ ...inputStyle, width: '100%' }}
        />
      </td>
      <td style={{ padding: '8px 12px' }}>
        <select value={form.match_type} onChange={set('match_type')} style={{ ...inputStyle, width: '100%' }}>
          {MATCH_TYPES.map(t => (
            <option key={t} value={t}>{t.replace('_', ' ')}</option>
          ))}
        </select>
      </td>
      <td style={{ padding: '8px 12px' }}>
        <CategorySelect value={form.category_id} onChange={id => setForm(f => ({ ...f, category_id: id }))} />
      </td>
      <td style={{ padding: '8px 12px' }} colSpan={2}>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <input
            value={form.min_amount}
            onChange={set('min_amount')}
            placeholder="Min $"
            type="number"
            step="0.01"
            style={{ ...inputStyle, width: '72px' }}
          />
          <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>–</span>
          <input
            value={form.max_amount}
            onChange={set('max_amount')}
            placeholder="Max $"
            type="number"
            step="0.01"
            style={{ ...inputStyle, width: '72px' }}
          />
        </div>
      </td>
      <td style={{ padding: '8px 12px', whiteSpace: 'nowrap' }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            type="button"
            onClick={() => onSave(form)}
            disabled={!valid || saving}
            style={{
              padding: '5px 12px', fontSize: '11px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: 'none', cursor: valid && !saving ? 'pointer' : 'default',
              background: 'color-mix(in srgb, var(--success) 15%, transparent)',
              color: 'var(--success)',
              opacity: valid && !saving ? 1 : 0.5,
            }}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            style={{
              padding: '5px 12px', fontSize: '11px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
          >
            Cancel
          </button>
        </div>
      </td>
    </tr>
    {form.payee_pattern.trim() && (
      <tr style={{ background: 'color-mix(in srgb, var(--accent) 3%, transparent)' }}>
        <td colSpan={6} style={{ padding: '0 12px 12px' }}>
          <RulePreview
            payeePattern={form.payee_pattern}
            matchType={form.match_type}
            minAmount={form.min_amount ? parseFloat(form.min_amount) : undefined}
            maxAmount={form.max_amount ? parseFloat(form.max_amount) : undefined}
            categoryId={form.category_id || undefined}
            categoryName={selectedCatName || undefined}
          />
        </td>
      </tr>
    )}
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Undo bar                                                            */
/* ------------------------------------------------------------------ */

function UndoBar({ rule, onUndo, onDismiss }: { rule: Rule; onUndo: () => void; onDismiss: () => void }) {
  const [remaining, setRemaining] = useState(6)

  useEffect(() => {
    const iv = setInterval(() => setRemaining(r => r - 1), 1000)
    const timeout = setTimeout(onDismiss, 6000)
    return () => { clearInterval(iv); clearTimeout(timeout) }
  }, [onDismiss])

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '10px',
      padding: '10px 20px', fontSize: '12px',
      background: 'color-mix(in srgb, var(--warning) 8%, transparent)',
      borderBottom: '1px solid color-mix(in srgb, var(--warning) 30%, transparent)',
      color: 'var(--text-primary)',
    }}>
      <span>
        Deleted rule <strong>"{rule.payee_pattern}"</strong>
      </span>
      <button
        type="button"
        onClick={onUndo}
        style={{
          padding: '3px 10px', fontSize: '11px', fontWeight: 600,
          borderRadius: 'var(--radius)', border: '1px solid var(--warning)',
          cursor: 'pointer', background: 'transparent', color: 'var(--warning)',
        }}
      >
        Undo ({remaining}s)
      </button>
      <button
        type="button"
        onClick={onDismiss}
        style={{
          marginLeft: 'auto', background: 'none', border: 'none',
          color: 'var(--text-muted)', cursor: 'pointer', fontSize: '14px', padding: '0 4px',
        }}
      >
        &times;
      </button>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Source badge                                                         */
/* ------------------------------------------------------------------ */

function SourceBadge({ source }: { source: string }) {
  const color = source === 'learned' ? 'var(--accent)' : 'var(--text-muted)'
  return (
    <span style={{
      fontSize: '9px', padding: '1px 5px', borderRadius: '4px',
      background: `color-mix(in srgb, ${color} 12%, transparent)`,
      color, textTransform: 'uppercase', fontWeight: 600,
    }}>
      {source}
    </span>
  )
}

/* ------------------------------------------------------------------ */
/* Main component                                                      */
/* ------------------------------------------------------------------ */

type SortKey = 'payee' | 'match_type' | 'category' | 'confidence' | 'source' | 'times_applied'
type SortDir = 'asc' | 'desc'

export default function RulesManagement({ onBack }: { onBack: () => void }) {
  const { data, isLoading } = useRules()
  const createRule = useCreateRule()
  const updateRule = useUpdateRule()
  const deleteRule = useDeleteRule()
  const restoreRule = useRestoreRule()
  const { toast } = useToast()

  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [lastDeleted, setLastDeleted] = useState<Rule | null>(null)

  const [sortKey, setSortKey] = useState<SortKey>('times_applied')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir(key === 'times_applied' || key === 'confidence' ? 'desc' : 'asc')
    }
  }

  const rules = useMemo(() => {
    const list = [...(data?.rules ?? [])]
    const dir = sortDir === 'asc' ? 1 : -1
    list.sort((a, b) => {
      switch (sortKey) {
        case 'payee': return dir * a.payee_pattern.localeCompare(b.payee_pattern)
        case 'match_type': return dir * a.match_type.localeCompare(b.match_type)
        case 'category': return dir * (a.category_name ?? '').localeCompare(b.category_name ?? '')
        case 'confidence': return dir * (a.confidence - b.confidence)
        case 'source': return dir * a.source.localeCompare(b.source)
        case 'times_applied': return dir * (a.times_applied - b.times_applied)
        default: return 0
      }
    })
    return list
  }, [data, sortKey, sortDir])

  const clearUndo = useCallback(() => {
    setLastDeleted(null)
  }, [])

  const handleCreate = (form: RuleFormData) => {
    createRule.mutate(formToPayload(form), {
      onSuccess: () => {
        toast('Rule created', 'success')
        setCreating(false)
      },
    })
  }

  const handleUpdate = (ruleId: number, form: RuleFormData) => {
    updateRule.mutate({ rule_id: ruleId, ...formToPayload(form) }, {
      onSuccess: () => {
        toast('Rule updated', 'success')
        setEditingId(null)
      },
    })
  }

  const handleDelete = (rule: Rule) => {
    clearUndo()
    deleteRule.mutate(rule.id, {
      onSuccess: (deleted) => {
        setLastDeleted(deleted)
        toast('Rule deleted', 'warning')
      },
    })
  }

  const handleUndo = () => {
    if (!lastDeleted) return
    const r = lastDeleted
    clearUndo()
    restoreRule.mutate({
      payee_pattern: r.payee_pattern,
      match_type: r.match_type,
      category_id: r.category_id,
      min_amount: r.min_amount,
      max_amount: r.max_amount,
      confidence: r.confidence,
      source: r.source,
      times_applied: r.times_applied,
    }, {
      onSuccess: () => toast('Rule restored', 'success'),
    })
  }

  const columnHeaders: { label: string; key: SortKey | null; align: string }[] = [
    { label: 'Payee Pattern', key: 'payee', align: 'left' },
    { label: 'Match', key: 'match_type', align: 'left' },
    { label: 'Category', key: 'category', align: 'left' },
    { label: 'Confidence', key: 'confidence', align: 'center' },
    { label: 'Source', key: 'source', align: 'center' },
    { label: 'Applied', key: 'times_applied', align: 'right' },
    { label: '', key: null, align: 'right' },
  ]

  /* Loading skeleton */
  if (isLoading) {
    return (
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <div style={{ width: '200px', height: '14px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
          <div style={{ width: '100px', height: '28px', background: 'var(--bg-hover)', borderRadius: '4px' }} />
        </div>
        {[1, 2, 3, 4].map(i => (
          <div key={i} style={{ height: '44px', background: 'var(--bg-hover)', margin: '8px 20px', borderRadius: '4px' }} />
        ))}
      </div>
    )
  }

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 20px', borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            type="button"
            onClick={onBack}
            style={{
              padding: '4px 10px', fontSize: '11px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
          >
            &larr; Dashboard
          </button>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Categorization Rules
            <span style={{ marginLeft: '8px', fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>
              {rules.length} rule{rules.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
        {!creating && (
          <button
            type="button"
            onClick={() => { setCreating(true); setEditingId(null) }}
            style={{
              padding: '5px 14px', fontSize: '11px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
              background: 'color-mix(in srgb, var(--accent) 15%, transparent)',
              color: 'var(--accent)',
            }}
          >
            + Create Rule
          </button>
        )}
      </div>

      {/* Undo bar */}
      {lastDeleted && (
        <UndoBar rule={lastDeleted} onUndo={handleUndo} onDismiss={clearUndo} />
      )}

      {/* Empty state */}
      {rules.length === 0 && !creating && (
        <div style={{
          padding: '40px 24px', textAlign: 'center',
        }}>
          <div style={{ fontSize: '28px', marginBottom: '8px', opacity: 0.5 }}>&#128220;</div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
            No rules yet
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Create one to get started — rules auto-categorize transactions matching payee patterns.
          </div>
        </div>
      )}

      {/* Table */}
      {(rules.length > 0 || creating) && (
        <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '560px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead style={{ position: 'sticky', top: 0, zIndex: 2, background: 'var(--bg-card)' }}>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {columnHeaders.map((col, i) => (
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
              {creating && (
                <RuleForm
                  initial={EMPTY_FORM}
                  onSave={handleCreate}
                  onCancel={() => setCreating(false)}
                  saving={createRule.isPending}
                />
              )}
              {rules.map(rule => {
                if (editingId === rule.id) {
                  return (
                    <RuleForm
                      key={rule.id}
                      initial={ruleToForm(rule)}
                      onSave={form => handleUpdate(rule.id, form)}
                      onCancel={() => setEditingId(null)}
                      saving={updateRule.isPending}
                    />
                  )
                }
                return (
                  <tr
                    key={rule.id}
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
                    <td style={{ padding: '10px 12px', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {rule.payee_pattern}
                      {(rule.min_amount != null || rule.max_amount != null) && (
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          {rule.min_amount != null && rule.max_amount != null
                            ? `$${rule.min_amount} – $${rule.max_amount}`
                            : rule.min_amount != null
                              ? `≥ $${rule.min_amount}`
                              : `≤ $${rule.max_amount}`}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-muted)', fontSize: '12px' }}>
                      {rule.match_type.replace('_', ' ')}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      {rule.group_name && (
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                          {rule.group_name} &rsaquo;{' '}
                        </span>
                      )}
                      <span style={{ color: 'var(--text-primary)', fontSize: '12px' }}>
                        {rule.category_name || '—'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <span style={{
                        fontSize: '10px', fontWeight: 600, padding: '1px 6px',
                        borderRadius: '8px',
                        color: rule.confidence >= 0.7 ? 'var(--success)' : rule.confidence >= 0.4 ? 'var(--warning)' : 'var(--danger)',
                        background: `color-mix(in srgb, ${rule.confidence >= 0.7 ? 'var(--success)' : rule.confidence >= 0.4 ? 'var(--warning)' : 'var(--danger)'} 12%, transparent)`,
                      }}>
                        {Math.round(rule.confidence * 100)}%
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <SourceBadge source={rule.source} />
                    </td>
                    <td style={{
                      padding: '10px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums',
                      color: 'var(--text-muted)', fontSize: '12px',
                    }}>
                      {rule.times_applied}
                    </td>
                    <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '4px' }}>
                        <button
                          type="button"
                          onClick={() => { setEditingId(rule.id); setCreating(false) }}
                          style={{
                            padding: '4px 10px', fontSize: '11px', fontWeight: 600,
                            borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                            cursor: 'pointer', background: 'transparent', color: 'var(--accent)',
                          }}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(rule)}
                          disabled={deleteRule.isPending}
                          style={{
                            padding: '4px 10px', fontSize: '11px', fontWeight: 600,
                            borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer',
                            background: 'color-mix(in srgb, var(--danger) 10%, transparent)',
                            color: 'var(--danger)',
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
