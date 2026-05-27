import { useState, useEffect } from 'react'
import { useDkSettings, useUpdateDkSettings } from '../../hooks/dragon-keeper/use-dk-settings'
import { usePaycheckConfig, useUpdatePaycheckConfig, type DeductionItem } from '../../hooks/dragon-keeper/use-paycheck-config'
import { useToast } from './toast'
import RulesManagement from './rules-management'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

const DEDUCTION_CATEGORIES = ['taxes', 'benefits', 'retirement', 'other'] as const
const CATEGORY_LABELS: Record<string, string> = { taxes: 'Taxes', benefits: 'Benefits', retirement: 'Retirement', other: 'Other' }

function PaycheckConfigSection() {
  const { data: config } = usePaycheckConfig()
  const updateConfig = useUpdatePaycheckConfig()
  const { toast } = useToast()
  const [editing, setEditing] = useState(false)
  const [gross, setGross] = useState('')
  const [takeHome, setTakeHome] = useState('')
  const [effectiveDate, setEffectiveDate] = useState('')
  const [items, setItems] = useState<Omit<DeductionItem, 'id'>[]>([])

  useEffect(() => {
    if (config && !editing) {
      setGross(String(config.gross_amount))
      setTakeHome(String(config.take_home_amount))
      setEffectiveDate(config.effective_date)
      const flat = Object.values(config.deductions).flat().sort((a, b) => a.sort_order - b.sort_order)
      setItems(flat.map(i => ({ category: i.category, name: i.name, amount: i.amount, sort_order: i.sort_order })))
    }
  }, [config, editing])

  const handleSave = () => {
    updateConfig.mutate(
      {
        gross_amount: parseFloat(gross),
        take_home_amount: parseFloat(takeHome),
        effective_date: effectiveDate,
        deduction_items: items.map((it, idx) => ({ ...it, sort_order: idx + 1 })),
      },
      {
        onSuccess: () => { toast('Paycheck config saved', 'success'); setEditing(false) },
        onError: () => toast('Failed to save paycheck config', 'error'),
      }
    )
  }

  const inputStyle: React.CSSProperties = {
    padding: '6px 10px', fontSize: '13px',
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius)', color: 'var(--text-primary)',
    outline: 'none', boxSizing: 'border-box',
  }

  if (!config) return null

  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)' }}>
          Paycheck Configuration
        </h3>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            style={{ padding: '5px 12px', fontSize: '12px', fontWeight: 600, borderRadius: 'var(--radius)', border: '1px solid var(--border)', cursor: 'pointer', background: 'transparent', color: 'var(--accent)' }}
          >
            Edit
          </button>
        )}
      </div>

      {!editing ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '8px' }}>
            <div><span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Gross</span><div style={{ fontSize: '14px', fontWeight: 700 }}>{formatCurrency(config.gross_amount)}</div></div>
            <div><span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Take Home</span><div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--success)' }}>{formatCurrency(config.take_home_amount)}</div></div>
            <div><span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Effective</span><div style={{ fontSize: '14px', fontWeight: 700 }}>{config.effective_date}</div></div>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead><tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Category', 'Name', 'Amount'].map((h, i) => (
                <th key={h} style={{ padding: '6px 8px', textAlign: i === 2 ? 'right' : 'left', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {Object.values(config.deductions).flat().map((item, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '5px 8px', color: 'var(--text-muted)', fontSize: '11px' }}>{CATEGORY_LABELS[item.category] || item.category}</td>
                  <td style={{ padding: '5px 8px', color: 'var(--text-primary)' }}>{item.name}</td>
                  <td style={{ padding: '5px 8px', textAlign: 'right', color: 'var(--danger)', fontVariantNumeric: 'tabular-nums' }}>{formatCurrency(item.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>Gross Pay</label>
              <input type="number" value={gross} onChange={e => setGross(e.target.value)} step="0.01" style={{ ...inputStyle, width: '130px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>Take Home</label>
              <input type="number" value={takeHome} onChange={e => setTakeHome(e.target.value)} step="0.01" style={{ ...inputStyle, width: '130px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>Effective Date</label>
              <input type="date" value={effectiveDate} onChange={e => setEffectiveDate(e.target.value)} style={{ ...inputStyle, width: '150px' }} />
            </div>
          </div>

          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Deduction Items</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead><tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Category', 'Name', 'Amount', ''].map((h, i) => (
                  <th key={i} style={{ padding: '6px 8px', textAlign: i === 2 ? 'right' : 'left', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {items.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '4px 8px' }}>
                      <select value={item.category} onChange={e => setItems(prev => prev.map((it, i) => i === idx ? { ...it, category: e.target.value } : it))} style={{ ...inputStyle, padding: '4px 6px', width: '110px' }}>
                        {DEDUCTION_CATEGORIES.map(c => <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}
                      </select>
                    </td>
                    <td style={{ padding: '4px 8px' }}>
                      <input value={item.name} onChange={e => setItems(prev => prev.map((it, i) => i === idx ? { ...it, name: e.target.value } : it))} style={{ ...inputStyle, width: '180px' }} />
                    </td>
                    <td style={{ padding: '4px 8px' }}>
                      <input type="number" value={item.amount} onChange={e => setItems(prev => prev.map((it, i) => i === idx ? { ...it, amount: parseFloat(e.target.value) || 0 } : it))} step="0.01" style={{ ...inputStyle, width: '100px', textAlign: 'right' }} />
                    </td>
                    <td style={{ padding: '4px 8px' }}>
                      <button onClick={() => setItems(prev => prev.filter((_, i) => i !== idx))} style={{ padding: '2px 8px', fontSize: '11px', background: 'none', border: '1px solid var(--border)', borderRadius: 'var(--radius)', cursor: 'pointer', color: 'var(--danger)' }}>✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={() => setItems(prev => [...prev, { category: 'other', name: '', amount: 0, sort_order: prev.length + 1 }])}
              style={{ marginTop: '8px', padding: '5px 12px', fontSize: '12px', fontWeight: 600, borderRadius: 'var(--radius)', border: '1px dashed var(--border)', cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)' }}
            >
              + Add Row
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={handleSave} disabled={updateConfig.isPending} style={{ padding: '8px 20px', fontSize: '13px', fontWeight: 600, borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer', background: 'var(--accent)', color: '#fff', opacity: updateConfig.isPending ? 0.6 : 1 }}>
              {updateConfig.isPending ? 'Saving...' : 'Save'}
            </button>
            <button onClick={() => setEditing(false)} style={{ padding: '8px 20px', fontSize: '13px', fontWeight: 600, borderRadius: 'var(--radius)', border: '1px solid var(--border)', cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)' }}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function DkSettingsPage() {
  const { data, isLoading } = useDkSettings()
  const updateSettings = useUpdateDkSettings()
  const { toast } = useToast()

  const [projectionDays, setProjectionDays] = useState(30)
  const [bufferAmount, setBufferAmount] = useState(100)
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    if (data) {
      setProjectionDays(data.projection_days)
      setBufferAmount(data.buffer_amount)
      setDirty(false)
    }
  }, [data])

  const handleSave = () => {
    updateSettings.mutate(
      { projection_days: projectionDays, buffer_amount: bufferAmount },
      {
        onSuccess: () => {
          toast('Settings saved', 'success')
          setDirty(false)
        },
        onError: () => toast('Failed to save settings', 'error'),
      },
    )
  }

  const inputStyle: React.CSSProperties = {
    padding: '10px 14px', fontSize: '14px',
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius)', color: 'var(--text-primary)',
    outline: 'none', width: '120px', boxSizing: 'border-box',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
        Settings
      </h2>

      {isLoading ? (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          Loading...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '600px' }}>
          {/* Safe-to-Spend Projection */}
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)', padding: '20px',
          }}>
            <h3 style={{
              margin: '0 0 16px', fontSize: '13px', fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)',
            }}>
              Safe-to-Spend Projection
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={{
                  display: 'block', fontSize: '13px', fontWeight: 600,
                  color: 'var(--text-primary)', marginBottom: '6px',
                }}>
                  Projection Window
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input
                    type="number"
                    value={projectionDays}
                    onChange={e => { setProjectionDays(Number(e.target.value)); setDirty(true) }}
                    min={7}
                    max={365}
                    style={inputStyle}
                  />
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>days</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  How far ahead to project income and expenses for safe-to-spend calculation. Default: 30 days.
                </div>
              </div>

              <div>
                <label style={{
                  display: 'block', fontSize: '13px', fontWeight: 600,
                  color: 'var(--text-primary)', marginBottom: '6px',
                }}>
                  Minimum Buffer
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>$</span>
                  <input
                    type="number"
                    value={bufferAmount}
                    onChange={e => { setBufferAmount(Number(e.target.value)); setDirty(true) }}
                    min={0}
                    step={25}
                    style={inputStyle}
                  />
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Reserve this amount as a safety cushion. Safe-to-spend will subtract this from the projected minimum balance. Default: $100.
                </div>
              </div>
            </div>
          </div>

          {/* Paycheck Configuration */}
          <PaycheckConfigSection />

          {/* Save button */}
          {dirty && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handleSave}
                disabled={updateSettings.isPending}
                className="btn btn-primary"
                style={{ fontSize: '13px', padding: '8px 20px' }}
              >
                {updateSettings.isPending ? 'Saving...' : 'Save Settings'}
              </button>
              <button
                onClick={() => {
                  if (data) {
                    setProjectionDays(data.projection_days)
                    setBufferAmount(data.buffer_amount)
                    setDirty(false)
                  }
                }}
                style={{
                  padding: '8px 20px', fontSize: '13px', fontWeight: 600,
                  borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                  cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      <RulesManagement />
    </div>
  )
}
