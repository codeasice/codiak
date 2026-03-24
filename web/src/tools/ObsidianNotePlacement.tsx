import { useState } from 'react'
import { apiFetch } from '../api'

interface Suggestion {
    path: string
    reason: string
    confidence: number
}

interface PlacementResult {
    tree_preview: string
    suggestions: Suggestion[]
    scan_root?: string
    parent_note?: string | null
    error?: string
    raw?: string
}

const MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']

export default function ObsidianNotePlacement() {
    const [vaultPath, setVaultPath] = useState('C:\\Users\\live\\Documents\\Codeasice')
    const [pageName, setPageName] = useState('')
    const [parentNote, setParentNote] = useState('')
    const [description, setDescription] = useState('')
    const [depth, setDepth] = useState(3)
    const [model, setModel] = useState('gpt-4o')
    const [maxTokens, setMaxTokens] = useState(500)
    const [temperature, setTemperature] = useState(0.2)
    const [result, setResult] = useState<PlacementResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const run = async () => {
        if (!pageName.trim()) {
            setError('Please provide a note name.')
            return
        }
        if (!vaultPath.trim()) {
            setError('Please provide a vault path.')
            return
        }
        setLoading(true)
        setError('')
        setResult(null)
        try {
            const data = await apiFetch<PlacementResult>('/tools/obsidian-note-placement', {
                method: 'POST',
                body: JSON.stringify({
                    vault_path: vaultPath,
                    page_name: pageName,
                    page_description: description,
                    depth,
                    parent_note_query: parentNote,
                    model,
                    max_tokens: maxTokens,
                    temperature,
                }),
            })
            if (data.error && !data.tree_preview) {
                setError(data.error)
            } else {
                setResult(data)
                if (data.error) setError(data.error)
            }
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Request failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="info-box">
                Scan your Obsidian vault and get LLM-recommended folder(s) to place a new note.
            </div>

            <div className="form-group">
                <label className="form-label">Obsidian Vault Path</label>
                <input
                    type="text"
                    value={vaultPath}
                    onChange={e => setVaultPath(e.target.value)}
                    placeholder="/Users/you/Documents/MyVault"
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="form-group">
                    <label className="form-label">New Note Name</label>
                    <input
                        type="text"
                        value={pageName}
                        onChange={e => setPageName(e.target.value)}
                        placeholder="My New Note"
                    />
                </div>
                <div className="form-group">
                    <label className="form-label">Start from Parent Note (optional)</label>
                    <input
                        type="text"
                        value={parentNote}
                        onChange={e => setParentNote(e.target.value)}
                        placeholder="Note name or relative path"
                    />
                </div>
            </div>

            <div className="form-group">
                <label className="form-label">Note Description / Context (optional)</label>
                <textarea
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    placeholder="What is this note about?"
                    style={{ minHeight: 80 }}
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Scan Depth</label>
                    <input
                        type="number"
                        min={0}
                        max={12}
                        value={depth}
                        onChange={e => setDepth(Number(e.target.value))}
                    />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Model</label>
                    <select value={model} onChange={e => setModel(e.target.value)}>
                        {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Max Tokens ({maxTokens})</label>
                    <input
                        type="range"
                        min={128}
                        max={2000}
                        step={32}
                        value={maxTokens}
                        onChange={e => setMaxTokens(Number(e.target.value))}
                    />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Temperature ({temperature.toFixed(2)})</label>
                    <input
                        type="range"
                        min={0}
                        max={1}
                        step={0.05}
                        value={temperature}
                        onChange={e => setTemperature(Number(e.target.value))}
                    />
                </div>
            </div>

            <button
                className="btn btn-primary"
                onClick={run}
                disabled={loading || !pageName.trim() || !vaultPath.trim()}
            >
                {loading
                    ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Scanning…</>
                    : '🔍 Scan and Recommend'}
            </button>

            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}

            {result && (
                <>
                    {result.tree_preview && (
                        <div style={{ marginTop: 24 }}>
                            <div className="result-header">
                                <span className="result-label">
                                    Structure Preview
                                    {result.scan_root && (
                                        <span style={{ fontWeight: 400, color: 'var(--text-secondary)', marginLeft: 8 }}>
                                            ({result.scan_root})
                                        </span>
                                    )}
                                </span>
                            </div>
                            <div className="result-box" style={{ fontFamily: 'monospace', fontSize: 12, maxHeight: 240, overflowY: 'auto', whiteSpace: 'pre' }}>
                                {result.tree_preview}
                            </div>
                        </div>
                    )}

                    {result.suggestions && result.suggestions.length > 0 && (
                        <div style={{ marginTop: 24 }}>
                            <div className="result-label" style={{ marginBottom: 12 }}>Suggested Locations</div>
                            {result.suggestions.map((s, i) => (
                                <div key={i} style={{
                                    border: '1px solid var(--border)',
                                    borderRadius: 8,
                                    padding: '14px 16px',
                                    marginBottom: 10,
                                    background: 'var(--surface)',
                                    display: 'grid',
                                    gridTemplateColumns: '1fr auto',
                                    gap: 12,
                                    alignItems: 'start',
                                }}>
                                    <div>
                                        <div style={{ fontWeight: 600, marginBottom: 4 }}>
                                            {i + 1}. {s.path}
                                        </div>
                                        {s.reason && (
                                            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                                                {s.reason}
                                            </div>
                                        )}
                                    </div>
                                    {typeof s.confidence === 'number' && (
                                        <div style={{ textAlign: 'center', minWidth: 64 }}>
                                            <div style={{
                                                fontSize: 18,
                                                fontWeight: 700,
                                                color: s.confidence >= 0.7 ? 'var(--accent)' : 'var(--text-secondary)',
                                            }}>
                                                {Math.round(s.confidence * 100)}%
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>confidence</div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {result.raw && (
                        <div style={{ marginTop: 16 }}>
                            <div className="result-label" style={{ marginBottom: 6 }}>Raw LLM Response</div>
                            <div className="result-box" style={{ fontFamily: 'monospace', fontSize: 12 }}>{result.raw}</div>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
