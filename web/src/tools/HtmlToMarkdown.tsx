import { useState } from 'react'
import { apiFetch } from '../api'
import CopyButton from '../components/CopyButton'

export default function HtmlToMarkdown() {
    const [html, setHtml] = useState('')
    const [result, setResult] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const convert = async () => {
        if (!html.trim()) return
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<{ result: string }>('/tools/html-to-markdown', {
                method: 'POST',
                body: JSON.stringify({ html }),
            })
            setResult(data.result)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Conversion failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="info-box">
                Paste HTML content below. The tool converts it to clean Markdown.
            </div>
            <div className="form-group">
                <label className="form-label">HTML Input</label>
                <textarea
                    value={html}
                    onChange={e => setHtml(e.target.value)}
                    placeholder="<h1>Hello</h1><p>World</p>"
                    style={{ minHeight: 180 }}
                />
            </div>
            <button className="btn btn-primary" onClick={convert} disabled={loading || !html.trim()}>
                {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Converting…</> : '⟶ Convert to Markdown'}
            </button>

            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}

            {result && (
                <div style={{ marginTop: 20 }}>
                    <div className="result-header">
                        <span className="result-label">Markdown Output</span>
                        <CopyButton text={result} />
                    </div>
                    <div className="result-box">{result}</div>
                </div>
            )}
        </div>
    )
}
