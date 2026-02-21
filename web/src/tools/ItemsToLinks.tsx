import { useState } from 'react'
import { apiFetch } from '../api'
import CopyButton from '../components/CopyButton'

export default function ItemsToLinks() {
    const [text, setText] = useState('')
    const [excludeNumbers, setExcludeNumbers] = useState(false)
    const [boldOnly, setBoldOnly] = useState(false)
    const [result, setResult] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const convert = async (mode: 'add' | 'remove') => {
        setLoading(true)
        setError('')
        try {
            if (mode === 'add') {
                const data = await apiFetch<{ result: string }>('/tools/items-to-links', {
                    method: 'POST',
                    body: JSON.stringify({ text, exclude_numbers: excludeNumbers, bold_only: boldOnly }),
                })
                setResult(data.result)
            } else {
                const data = await apiFetch<{ result: string }>('/tools/links-to-items', {
                    method: 'POST',
                    body: JSON.stringify({ text }),
                })
                setResult(data.result)
            }
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="info-box">
                Convert items (one per line) to Obsidian-style <code>[[links]]</code>, or remove links.
                Blank lines are ignored.
            </div>
            <div className="form-group">
                <label className="form-label">Items (one per line)</label>
                <textarea
                    value={text}
                    onChange={e => setText(e.target.value)}
                    placeholder="Apple&#10;Banana&#10;Cherry"
                    style={{ minHeight: 160 }}
                />
            </div>
            <div className="checkbox-group" style={{ marginBottom: 16 }}>
                <label className="checkbox-item">
                    <input type="checkbox" checked={excludeNumbers} onChange={e => setExcludeNumbers(e.target.checked)} />
                    Exclude leading numbers (e.g. "1. Item" → "Item")
                </label>
                <label className="checkbox-item">
                    <input type="checkbox" checked={boldOnly} onChange={e => setBoldOnly(e.target.checked)} />
                    Only link bolded portions (**text** → [[text]])
                </label>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-primary" onClick={() => convert('add')} disabled={loading || !text.trim()}>
                    ➕ Add Links
                </button>
                <button className="btn btn-ghost" onClick={() => convert('remove')} disabled={loading || !text.trim()}>
                    ➖ Remove Links
                </button>
            </div>
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
