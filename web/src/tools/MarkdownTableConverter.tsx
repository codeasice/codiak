import { useState } from 'react'
import { apiFetch } from '../api'
import CopyButton from '../components/CopyButton'

type ConvTab = 'from-markdown' | 'from-excel'
type OutputFormat = 'teams_html' | 'excel_csv' | 'confluence_html' | 'plain_text'

interface MarkdownResult {
    teams_html: string
    excel_csv: string
    confluence_html: string
    plain_text: string
    row_count: number
    col_count: number
}

interface ExcelResult {
    markdown: string
    row_count: number
    col_count: number
}

const FORMAT_TABS: { key: OutputFormat; label: string }[] = [
    { key: 'teams_html', label: '📋 Teams HTML' },
    { key: 'excel_csv', label: '📊 Excel CSV' },
    { key: 'confluence_html', label: '🏛 Confluence HTML' },
    { key: 'plain_text', label: '📝 Plain Text' },
]

export default function MarkdownTableConverter() {
    const [convTab, setConvTab] = useState<ConvTab>('from-markdown')
    const [mdInput, setMdInput] = useState('| Name | Age | City |\n|------|-----|------|\n| John | 25  | NYC  |\n| Jane | 30  | LA   |')
    const [excelInput, setExcelInput] = useState('Name\tAge\tCity\nJohn\t25\tNYC\nJane\t30\tLA')
    const [mdResult, setMdResult] = useState<MarkdownResult | null>(null)
    const [excelResult, setExcelResult] = useState<ExcelResult | null>(null)
    const [outputTab, setOutputTab] = useState<OutputFormat>('teams_html')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const convertMd = async () => {
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<MarkdownResult>('/tools/markdown-table-converter/from-markdown', {
                method: 'POST',
                body: JSON.stringify({ markdown: mdInput }),
            })
            setMdResult(data)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    const convertExcel = async () => {
        setLoading(true)
        setError('')
        try {
            const data = await apiFetch<ExcelResult>('/tools/markdown-table-converter/from-excel', {
                method: 'POST',
                body: JSON.stringify({ excel_text: excelInput }),
            })
            setExcelResult(data)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <div className="tab-strip">
                <button className={`tab ${convTab === 'from-markdown' ? 'active' : ''}`} onClick={() => { setConvTab('from-markdown'); setMdResult(null) }}>Markdown → Other Formats</button>
                <button className={`tab ${convTab === 'from-excel' ? 'active' : ''}`} onClick={() => { setConvTab('from-excel'); setExcelResult(null) }}>Excel → Markdown</button>
            </div>

            {convTab === 'from-markdown' && (
                <>
                    <div className="form-group">
                        <label className="form-label">Markdown Table</label>
                        <textarea value={mdInput} onChange={e => setMdInput(e.target.value)} style={{ minHeight: 140 }} />
                    </div>
                    <button className="btn btn-primary" onClick={convertMd} disabled={loading}>
                        {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Converting…</> : '⟶ Convert Table'}
                    </button>

                    {mdResult && (
                        <div style={{ marginTop: 20 }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 12 }}>
                                ✓ Parsed: {mdResult.row_count} rows × {mdResult.col_count} columns
                            </div>
                            <div className="tab-strip output-tabs">
                                {FORMAT_TABS.map(f => (
                                    <button key={f.key} className={`tab ${outputTab === f.key ? 'active' : ''}`} onClick={() => setOutputTab(f.key)}>
                                        {f.label}
                                    </button>
                                ))}
                            </div>
                            <div style={{ marginTop: 12 }}>
                                <div className="result-header">
                                    <span className="result-label">{FORMAT_TABS.find(f => f.key === outputTab)?.label}</span>
                                    <CopyButton text={mdResult[outputTab]} />
                                </div>
                                <div className="result-box">{mdResult[outputTab]}</div>
                            </div>
                        </div>
                    )}
                </>
            )}

            {convTab === 'from-excel' && (
                <>
                    <div className="info-box">Paste Excel data (tab-separated or space-separated). Converts to a markdown table.</div>
                    <div className="form-group">
                        <label className="form-label">Excel / Tab-Separated Data</label>
                        <textarea value={excelInput} onChange={e => setExcelInput(e.target.value)} style={{ minHeight: 140 }} />
                    </div>
                    <button className="btn btn-primary" onClick={convertExcel} disabled={loading}>
                        {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Converting…</> : '⟶ Convert to Markdown'}
                    </button>
                    {excelResult && (
                        <div style={{ marginTop: 20 }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 12 }}>
                                ✓ Parsed: {excelResult.row_count} rows × {excelResult.col_count} columns
                            </div>
                            <div className="result-header">
                                <span className="result-label">Markdown Table</span>
                                <CopyButton text={excelResult.markdown} />
                            </div>
                            <div className="result-box">{excelResult.markdown}</div>
                        </div>
                    )}
                </>
            )}

            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
        </div>
    )
}
