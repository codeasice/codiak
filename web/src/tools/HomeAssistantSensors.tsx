import { useState } from 'react'
import { apiFetch } from '../api'

interface Sensor {
    entity_id: string
    friendly_name: string
    state: string
    unit: string
    device_class: string
    last_changed: string
}

interface SensorsResponse {
    sensors: Sensor[]
    total: number
}

function formatLastChanged(iso: string): string {
    if (!iso) return ''
    try {
        return new Date(iso).toLocaleString()
    } catch {
        return iso
    }
}

export default function HomeAssistantSensors() {
    const [entityFilter, setEntityFilter] = useState('')
    const [deviceClass, setDeviceClass] = useState('')
    const [result, setResult] = useState<SensorsResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const fetch = async () => {
        setLoading(true)
        setError('')
        try {
            const params = new URLSearchParams()
            if (entityFilter) params.set('entity_filter', entityFilter)
            if (deviceClass) params.set('device_class', deviceClass)
            const data = await apiFetch<SensorsResponse>(
                `/home-assistant/sensors?${params}`
            )
            setResult(data)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed to fetch sensors')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="info-box">
                Reads <code>HOME_ASSISTANT_API_URL</code> and <code>HOME_ASSISTANT_TOKEN</code> from
                your <code>.env</code> file. Use filters to narrow results.
            </div>

            <div style={{ display: 'flex', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
                <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
                    <label className="form-label">Filter by Entity ID</label>
                    <input
                        type="text"
                        value={entityFilter}
                        onChange={e => setEntityFilter(e.target.value)}
                        placeholder="e.g. temperature"
                        onKeyDown={e => e.key === 'Enter' && fetch()}
                    />
                </div>
                <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
                    <label className="form-label">Filter by Device Class</label>
                    <input
                        type="text"
                        value={deviceClass}
                        onChange={e => setDeviceClass(e.target.value)}
                        placeholder="e.g. temperature, humidity"
                        onKeyDown={e => e.key === 'Enter' && fetch()}
                    />
                </div>
            </div>

            <button
                className="btn btn-primary"
                onClick={fetch}
                disabled={loading}
                style={{ marginTop: 4 }}
            >
                {loading ? (
                    <><span className="spinner" style={{ width: 12, height: 12 }} /> Fetching…</>
                ) : '🔍 Fetch Sensors'}
            </button>

            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}

            {result && (
                <div style={{ marginTop: 20 }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 12 }}>
                        {result.total} sensor{result.total !== 1 ? 's' : ''} found
                    </div>
                    {result.sensors.length === 0 ? (
                        <div className="info-box">No sensors matched your filters.</div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                        {['Entity ID', 'Friendly Name', 'State', 'Unit', 'Device Class', 'Last Changed'].map(h => (
                                            <th key={h} style={{
                                                textAlign: 'left', padding: '8px 12px',
                                                color: 'var(--text-muted)', fontWeight: 500, whiteSpace: 'nowrap'
                                            }}>{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {result.sensors.map(s => (
                                        <tr
                                            key={s.entity_id}
                                            style={{ borderBottom: '1px solid var(--border)' }}
                                            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                                            onMouseLeave={e => (e.currentTarget.style.background = '')}
                                        >
                                            <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontSize: 12, color: 'var(--accent)' }}>
                                                {s.entity_id}
                                            </td>
                                            <td style={{ padding: '8px 12px' }}>{s.friendly_name}</td>
                                            <td style={{ padding: '8px 12px', fontWeight: 600 }}>
                                                {s.state}
                                            </td>
                                            <td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>{s.unit}</td>
                                            <td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>{s.device_class}</td>
                                            <td style={{ padding: '8px 12px', color: 'var(--text-muted)', fontSize: 12, whiteSpace: 'nowrap' }}>
                                                {formatLastChanged(s.last_changed)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
