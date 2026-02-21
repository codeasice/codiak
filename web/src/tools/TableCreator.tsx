import { useState } from 'react'
import { apiFetch } from '../api'
import CopyButton from '../components/CopyButton'

type Tab = 'from-list' | 'join'

const DELIMITERS = [
    { label: 'Auto', value: '' },
    { label: ', (comma)', value: ',' },
    { label: '\\t (tab)', value: '\t' },
    { label: 'None (single column)', value: '__single__' },
]

export default function TableCreator() {
    const [tab, setTab] = useState<Tab>('from-list')
    const [listInput, setListInput] = useState('Apple\nBanana\nCherry')
    const [delimiter, setDelimiter] = useState('')
    const [table1, setTable1] = useState('| Fruit | Color |\n|-------|-------|\n| Apple | Red   |')
    const [table2, setTable2] = useState('| Fruit | Color |\n|-------|-------|\n| Banana| Yellow|')
    const [joinType, setJoinType] = useState<'append' | 'align'>('append')
    const [result, setResult] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const createTable = async () => {
        setLoading(true)
        setError('')
        try {
            const isSingle = delimiter === '__single__'
            const data = await apiFetch<{ result: string }>('/tools/table-creator/from-list', {
                method: 'POST',
                body: JSON.stringify({
                    input_text: listInput,
                    delimiter: isSingle ? null : (delimiter || null),
                    force_single_column: isSingle,
                }),
            })
            setResult(data.result)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    const joinTables = async () => {
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<{ result: string }>('/tools/table-creator/join', {
                method: 'POST',
                body: JSON.stringify({ table1, table2, how: joinType }),
            })
            setResult(data.result)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="tab-strip">
                <button className={`tab ${tab === 'from-list' ? 'active' : ''}`} onClick={() => { setTab('from-list'); setResult('') }}>Create from List</button>
                <button className={`tab ${tab === 'join' ? 'active' : ''}`} onClick={() => { setTab('join'); setResult('') }}>Join Two Tables</button>
            </div>

            {tab === 'from-list' && (
                <>
                    <div className="form-group">
                        <label className="form-label">List or CSV/TSV Input</label>
                        <textarea value={listInput} onChange={e => setListInput(e.target.value)} style={{ minHeight: 120 }} />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Delimiter</label>
                        <select value={delimiter} onChange={e => setDelimiter(e.target.value)}>
                            {DELIMITERS.map(d => <option key={d.label} value={d.value}>{d.label}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={createTable} disabled={loading}>
                        {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Creating…</> : '📊 Create Table'}
                    </button>
                </>
            )}

            {tab === 'join' && (
                <>
                    <div className="form-group">
                        <label className="form-label">Table 1 (Markdown)</label>
                        <textarea value={table1} onChange={e => setTable1(e.target.value)} style={{ minHeight: 100 }} />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Table 2 (Markdown)</label>
                        <textarea value={table2} onChange={e => setTable2(e.target.value)} style={{ minHeight: 100 }} />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Join Type</label>
                        <select value={joinType} onChange={e => setJoinType(e.target.value as 'append' | 'align')}>
                            <option value="append">Append Rows</option>
                            <option value="align">Align Columns (outer join)</option>
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={joinTables} disabled={loading}>
                        {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Joining…</> : '🔗 Join Tables'}
                    </button>
                </>
            )}

            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
            {result && (
                <div style={{ marginTop: 20 }}>
                    <div className="result-header">
                        <span className="result-label">Markdown Table</span>
                        <CopyButton text={result} />
                    </div>
                    <div className="result-box">{result}</div>
                </div>
            )}
        </div>
    )
}
