import { useState, useEffect } from 'react'
import { useDkSettings, useUpdateDkSettings } from '../../hooks/dragon-keeper/use-dk-settings'
import { useToast } from './toast'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

interface SettingsPageProps {
  onBack: () => void
}

export default function DkSettingsPage({ onBack }: SettingsPageProps) {
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
    </div>
  )
}
