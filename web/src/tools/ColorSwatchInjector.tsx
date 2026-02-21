import { useState } from 'react'
import { apiFetch } from '../api'
import CopyButton from '../components/CopyButton'

export default function ColorSwatchInjector() {
    const [markdown, setMarkdown] = useState('## My Colors\n- red\n- forest green\n- #ffcc00\n- gold\n')
    const [result, setResult] = useState('')
    const [missing, setMissing] = useState<string[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const inject = async () => {
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<{ result: string; missing_colors: string[] }>('/tools/color-swatch-injector', {
                method: 'POST',
                body: JSON.stringify({ markdown }),
            })
            setResult(data.result)
            setMissing(data.missing_colors)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="info-box">
                Adds colored HTML squares next to color names in your markdown. Supports named colors and hex codes.
            </div>
            <div className="form-group">
                <label className="form-label">Markdown with Color Lists</label>
                <textarea value={markdown} onChange={e => setMarkdown(e.target.value)} style={{ minHeight: 160 }} />
            </div>
            <button className="btn btn-primary" onClick={inject} disabled={loading}>
                {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Injecting…</> : '🎨 Inject Color Swatches'}
            </button>
            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
            {missing.length > 0 && (
                <div className="info-box" style={{ marginTop: 12 }}>
                    ⚠️ Unrecognized colors: {missing.join(', ')}
                </div>
            )}
            {result && (
                <div style={{ marginTop: 20 }}>
                    <div className="result-header">
                        <span className="result-label">Output Markdown</span>
                        <CopyButton text={result} />
                    </div>
                    <div className="result-box">{result}</div>
                    <div style={{ marginTop: 16 }}>
                        <div className="result-label" style={{ marginBottom: 8 }}>Preview</div>
                        <div
                            style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}
                            dangerouslySetInnerHTML={{ __html: result.replace(/\n/g, '<br>') }}
                        />
                    </div>
                </div>
            )}
        </div>
    )
}
