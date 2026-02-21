import { useState } from 'react'
import { apiFetch } from '../api'
import CopyButton from '../components/CopyButton'

const OPTION_LABELS: Record<string, string> = {
    h1: 'H1 (#)',
    h2: 'H2 (##)',
    h3: 'H3 (###)',
    bullets: 'Bullets (- * +)',
    checkboxes: 'Checkboxes [ ]',
    bold: 'Bold (**text**)',
    italic: 'Italic (*text*)',
    inline_code: 'Inline Code (`code`)',
    code_block: 'Code Block (```)',
    blockquote: 'Blockquote (>)',
    hr: 'Horizontal Rule (---)',
    table: 'Tables (| col |)',
}

const DEFAULT_OPTIONS: Record<string, boolean> = {
    h1: true, h2: true, h3: true, bullets: true, checkboxes: true,
    bold: true, italic: true, inline_code: true, code_block: true,
    blockquote: true, hr: true, table: false,
}

export default function MarkdownStripper() {
    const [text, setText] = useState('')
    const [options, setOptions] = useState<Record<string, boolean>>(DEFAULT_OPTIONS)
    const [result, setResult] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const strip = async () => {
        if (!text.trim()) return
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<{ result: string }>('/tools/markdown-stripper', {
                method: 'POST',
                body: JSON.stringify({ text, options }),
            })
            setResult(data.result)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    const toggle = (key: string) =>
        setOptions(prev => ({ ...prev, [key]: !prev[key] }))

    return (
        <div>
            <div className="info-box">Select markdown elements to remove, then click Strip.</div>
            <div className="form-group">
                <label className="form-label">Markdown Input</label>
                <textarea value={text} onChange={e => setText(e.target.value)} placeholder="# My Heading..." style={{ minHeight: 160 }} />
            </div>
            <div className="form-group">
                <label className="form-label">Elements to remove</label>
                <div className="checkbox-group">
                    {Object.keys(OPTION_LABELS).map(key => (
                        <label key={key} className="checkbox-item">
                            <input type="checkbox" checked={options[key]} onChange={() => toggle(key)} />
                            {OPTION_LABELS[key]}
                        </label>
                    ))}
                </div>
            </div>
            <button className="btn btn-primary" onClick={strip} disabled={loading || !text.trim()}>
                {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Stripping…</> : '✂️ Remove Selected Formatting'}
            </button>
            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
            {result && (
                <div style={{ marginTop: 20 }}>
                    <div className="result-header">
                        <span className="result-label">Output</span>
                        <CopyButton text={result} />
                    </div>
                    <div className="result-box">{result}</div>
                </div>
            )}
        </div>
    )
}
