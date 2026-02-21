import { useState } from 'react'
import { apiFetch } from '../api'

interface CategoryResult {
    categories: Record<string, string[]>
    uncategorized: string[]
}

export default function HomeAutomationCategorizer() {
    const [text, setText] = useState('')
    const [result, setResult] = useState<CategoryResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const categorize = async () => {
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<CategoryResult>('/tools/home-automation-categorizer', {
                method: 'POST',
                body: JSON.stringify({ items_text: text }),
            })
            setResult(data)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    const total = result
        ? Object.values(result.categories).reduce((s, a) => s + a.length, 0) + result.uncategorized.length
        : 0

    return (
        <div>
            <div className="info-box">
                Paste a list of home automation entity IDs (one per line). They will be categorized by their domain suffix (e.g. <code>.light</code>, <code>.switch</code>).
            </div>
            <div className="form-group">
                <label className="form-label">Entity IDs (one per line)</label>
                <textarea
                    value={text}
                    onChange={e => setText(e.target.value)}
                    placeholder="living_room.light&#10;kitchen.switch&#10;front_door.lock&#10;hallway.motion_sensor"
                    style={{ minHeight: 160 }}
                />
            </div>
            <button className="btn btn-primary" onClick={categorize} disabled={loading || !text.trim()}>
                {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Categorizing…</> : '🏠 Categorize'}
            </button>
            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
            {result && (
                <div style={{ marginTop: 20 }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 16 }}>
                        {total} items categorized into {Object.keys(result.categories).length} categories
                    </div>
                    {Object.entries(result.categories).map(([cat, items]) => (
                        <div key={cat} style={{ marginBottom: 16 }}>
                            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, color: 'var(--accent)' }}>
                                {cat} ({items.length})
                            </div>
                            <div className="result-box" style={{ maxHeight: 120 }}>
                                {items.join('\n')}
                            </div>
                        </div>
                    ))}
                    {result.uncategorized.length > 0 && (
                        <div style={{ marginBottom: 16 }}>
                            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, color: 'var(--text-muted)' }}>
                                Uncategorized ({result.uncategorized.length})
                            </div>
                            <div className="result-box" style={{ maxHeight: 120 }}>
                                {result.uncategorized.join('\n')}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
