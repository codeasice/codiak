import { useState, useEffect } from 'react'
import { apiFetch } from '../api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StoryEntry { id: string; status: string }
interface EpicGroup {
    id: string; num: number; status: string
    retrospective: string | null
    stories: StoryEntry[]
    counts: Record<string, number>
}
interface SprintEpics {
    project: string; generated: string
    epics: EpicGroup[]
    totals: Record<string, number>
}
interface SprintFile { path: string; filename: string; data: Record<string, unknown>; epics: SprintEpics }
interface EpicHeading { num: number; title: string; story_count: number }
interface EpicsFile { path: string; filename: string; epics: EpicHeading[] }
interface BmadInfo {
    project_path: string; config_file: string | null; status_file: string | null
    sprint_status_files: string[]; epics_files: string[]
    output_folder: string | null; bmad_folder: string | null; errors: string[]
}
interface StatusSummary {
    project_name: string; current_phase: string
    active_workflows: { name: string }[]; completed_workflows: { name: string }[]
    pending_workflows: { name: string }[]; next_actions: string[]
}
interface AnalysisResult {
    bmad_info: BmadInfo
    status_data: Record<string, unknown> | null
    status_summary: StatusSummary | null
    sprint_files: SprintFile[]
    epics_files: EpicsFile[]
}

// ---------------------------------------------------------------------------
// Status styling
// ---------------------------------------------------------------------------

const STATUS_COLOR: Record<string, string> = {
    done: '#22c55e', completed: '#22c55e',
    'in-progress': '#3b82f6', in_progress: '#3b82f6',
    review: '#a855f7',
    'ready-for-dev': '#f59e0b',
    drafted: '#6b7280',
    contexted: '#06b6d4',
    backlog: '#d1d5db',
    blocked: '#ef4444',
    optional: '#9ca3af',
    unknown: '#9ca3af',
}
const STATUS_LABEL: Record<string, string> = {
    done: 'Done', completed: 'Done',
    'in-progress': 'In Progress', in_progress: 'In Progress',
    review: 'Review', 'ready-for-dev': 'Ready', drafted: 'Drafted',
    contexted: 'Contexted', backlog: 'Backlog', blocked: 'Blocked',
    optional: 'Optional', unknown: '?',
}
function statusColor(s: string) { return STATUS_COLOR[s.toLowerCase()] ?? '#9ca3af' }
function statusLabel(s: string) { return STATUS_LABEL[s.toLowerCase()] ?? s }

function StatusPill({ status, small }: { status: string; small?: boolean }) {
    const color = statusColor(status)
    return (
        <span style={{
            display: 'inline-block',
            padding: small ? '1px 6px' : '2px 8px',
            borderRadius: 99,
            fontSize: small ? 10 : 11,
            fontWeight: 600,
            background: color + '22',
            color,
            border: `1px solid ${color}55`,
            whiteSpace: 'nowrap',
        }}>
            {statusLabel(status)}
        </span>
    )
}

// ---------------------------------------------------------------------------
// Sprint epics view
// ---------------------------------------------------------------------------

const ACTIVE_STATUSES = new Set(['in-progress', 'in_progress', 'review', 'ready-for-dev', 'drafted'])

function EpicRow({ epic, titleMap }: { epic: EpicGroup; titleMap: Record<number, string> }) {
    const [open, setOpen] = useState(false)
    const total = epic.stories.length
    const done = epic.counts['done'] ?? 0
    const active = Object.entries(epic.counts)
        .filter(([s]) => ACTIVE_STATUSES.has(s))
        .reduce((a, [, v]) => a + v, 0)
    const pct = total > 0 ? Math.round((done / total) * 100) : 0
    const title = titleMap[epic.num]

    return (
        <div style={{ borderBottom: '1px solid var(--border)' }}>
            <div
                onClick={() => total > 0 && setOpen(o => !o)}
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr auto auto auto',
                    gap: 10,
                    alignItems: 'center',
                    padding: '8px 12px',
                    cursor: total > 0 ? 'pointer' : 'default',
                    background: open ? 'var(--surface)' : 'transparent',
                }}
            >
                <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'monospace', minWidth: 48 }}>
                    {open ? '▾' : '▸'} {epic.id}
                </span>
                <span style={{ fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {title ?? ''}
                </span>
                <StatusPill status={epic.status} />
                {total > 0 && (
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                        {done}/{total}
                        {active > 0 && <span style={{ color: '#3b82f6', marginLeft: 4 }}>({active} active)</span>}
                    </span>
                )}
                {total > 0 && (
                    <div style={{ width: 60, height: 5, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: '#22c55e', borderRadius: 99 }} />
                    </div>
                )}
            </div>

            {open && total > 0 && (
                <div style={{ paddingLeft: 24, paddingBottom: 8 }}>
                    {epic.stories.map(s => (
                        <div key={s.id} style={{
                            display: 'flex', alignItems: 'center', gap: 8,
                            padding: '3px 8px', fontSize: 12,
                        }}>
                            <StatusPill status={s.status} small />
                            <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{s.id}</span>
                        </div>
                    ))}
                    {epic.retrospective && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '3px 8px', fontSize: 12 }}>
                            <StatusPill status={epic.retrospective} small />
                            <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>retrospective</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

function SprintSection({ file, titleMap }: { file: SprintFile; titleMap: Record<number, string> }) {
    const { epics, totals } = file.epics
    const [showRaw, setShowRaw] = useState(false)
    const [filter, setFilter] = useState<string>('all')

    const activeStatuses = ['in-progress', 'review', 'ready-for-dev', 'drafted']
    const filterOptions = [
        { value: 'all', label: 'All' },
        { value: 'active', label: 'Active' },
        { value: 'backlog', label: 'Backlog' },
    ]

    const filteredEpics = epics.filter(ep => {
        if (filter === 'all') return true
        if (filter === 'backlog') return ep.stories.some(s => s.status === 'backlog')
        if (filter === 'active') return ep.stories.some(s => activeStatuses.includes(s.status))
        return true
    })

    return (
        <div style={{ marginBottom: 24 }}>
            <div className="result-label" style={{ marginBottom: 10 }}>
                🏃 Sprint Status — {file.epics.project}
                {file.epics.generated && (
                    <span style={{ fontWeight: 400, fontSize: 11, color: 'var(--text-secondary)', marginLeft: 8 }}>
                        generated {file.epics.generated}
                    </span>
                )}
            </div>

            {/* Totals row */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                {Object.entries(totals)
                    .sort(([a], [b]) => (STATUS_COLOR[a] ? -1 : 1) - (STATUS_COLOR[b] ? -1 : 1))
                    .map(([s, n]) => (
                        <div key={s} style={{
                            display: 'flex', alignItems: 'center', gap: 5,
                            padding: '4px 10px', borderRadius: 6,
                            background: statusColor(s) + '18',
                            border: `1px solid ${statusColor(s)}44`,
                            fontSize: 12,
                        }}>
                            <span style={{ fontWeight: 700, color: statusColor(s) }}>{n}</span>
                            <span style={{ color: 'var(--text-secondary)' }}>{statusLabel(s)}</span>
                        </div>
                    ))
                }
            </div>

            {/* Filter */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                {filterOptions.map(opt => (
                    <button key={opt.value} onClick={() => setFilter(opt.value)} style={{
                        padding: '3px 10px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                        border: '1px solid var(--border)',
                        background: filter === opt.value ? 'var(--accent)' : 'var(--surface)',
                        color: filter === opt.value ? '#fff' : 'var(--text-primary)',
                    }}>
                        {opt.label}
                    </button>
                ))}
            </div>

            {/* Epic list */}
            <div style={{ border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                {filteredEpics.length === 0
                    ? <div style={{ padding: 16, color: 'var(--text-secondary)', fontSize: 13 }}>No epics match filter.</div>
                    : filteredEpics.map(ep => <EpicRow key={ep.id} epic={ep} titleMap={titleMap} />)
                }
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn" style={{ fontSize: 12, padding: '4px 10px' }}
                    onClick={() => {
                        const blob = new Blob([JSON.stringify(file.data, null, 2)], { type: 'application/json' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a'); a.href = url; a.download = file.filename.replace('.yaml', '.json'); a.click()
                        URL.revokeObjectURL(url)
                    }}>↓ JSON</button>
                <button className="btn" style={{ fontSize: 12, padding: '4px 10px' }} onClick={() => setShowRaw(v => !v)}>
                    {showRaw ? 'Hide' : 'Show'} Raw
                </button>
            </div>
            {showRaw && (
                <div className="result-box" style={{ fontFamily: 'monospace', fontSize: 11, maxHeight: 300, overflowY: 'auto', marginTop: 8, whiteSpace: 'pre' }}>
                    {JSON.stringify(file.data, null, 2)}
                </div>
            )}
        </div>
    )
}

// ---------------------------------------------------------------------------
// Epics.md section
// ---------------------------------------------------------------------------

function EpicsSection({ file }: { file: EpicsFile }) {
    return (
        <div style={{ marginBottom: 24 }}>
            <div className="result-label" style={{ marginBottom: 10 }}>
                📋 Epics — {file.filename}
            </div>
            <div style={{ border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                {file.epics.length === 0
                    ? <div style={{ padding: 16, color: 'var(--text-secondary)', fontSize: 13 }}>No epic headings found.</div>
                    : file.epics.map(ep => (
                        <div key={ep.num} style={{
                            display: 'grid', gridTemplateColumns: '40px 1fr auto',
                            gap: 10, alignItems: 'center', padding: '8px 14px',
                            borderBottom: '1px solid var(--border)',
                            fontSize: 13,
                        }}>
                            <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: 12 }}>#{ep.num}</span>
                            <span>{ep.title}</span>
                            {ep.story_count > 0 && (
                                <span style={{ fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                    {ep.story_count} {ep.story_count === 1 ? 'story' : 'stories'}
                                </span>
                            )}
                        </div>
                    ))
                }
            </div>
        </div>
    )
}

// ---------------------------------------------------------------------------
// Workflow status section
// ---------------------------------------------------------------------------

function WorkflowSection({ summary, raw, onDownload }: {
    summary: StatusSummary; raw: Record<string, unknown>; onDownload: () => void
}) {
    const [showRaw, setShowRaw] = useState(false)
    return (
        <div style={{ marginBottom: 24 }}>
            <div className="result-label" style={{ marginBottom: 10 }}>
                📊 Workflow Status — {summary.project_name}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                {[
                    { label: 'Active', count: summary.active_workflows.length, color: '#3b82f6' },
                    { label: 'Completed', count: summary.completed_workflows.length, color: '#22c55e' },
                    { label: 'Pending', count: summary.pending_workflows.length, color: '#9ca3af' },
                ].map(b => (
                    <div key={b.label} style={{
                        padding: '6px 14px', borderRadius: 8, background: b.color + '18',
                        border: `1px solid ${b.color}44`, textAlign: 'center', minWidth: 64,
                    }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: b.color }}>{b.count}</div>
                        <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{b.label}</div>
                    </div>
                ))}
            </div>
            {summary.active_workflows.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                    {summary.active_workflows.map((w, i) => <div key={i} style={{ fontSize: 13, padding: '2px 0' }}>🔄 {w.name}</div>)}
                </div>
            )}
            {summary.next_actions.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>NEXT ACTIONS</div>
                    {summary.next_actions.map((a, i) => <div key={i} style={{ fontSize: 13, padding: '2px 0' }}>→ {a}</div>)}
                </div>
            )}
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button className="btn" style={{ fontSize: 12, padding: '4px 10px' }} onClick={onDownload}>↓ JSON</button>
                <button className="btn" style={{ fontSize: 12, padding: '4px 10px' }} onClick={() => setShowRaw(v => !v)}>
                    {showRaw ? 'Hide' : 'Show'} Raw
                </button>
            </div>
            {showRaw && (
                <div className="result-box" style={{ fontFamily: 'monospace', fontSize: 11, maxHeight: 300, overflowY: 'auto', marginTop: 8, whiteSpace: 'pre' }}>
                    {JSON.stringify(raw, null, 2)}
                </div>
            )}
        </div>
    )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const DEFAULT_BASE = 'C:\\Users\\live\\dev'

export default function BmadProjectStatus() {
    const [baseFolder, setBaseFolder] = useState(DEFAULT_BASE)
    const [projects, setProjects] = useState<string[]>([])
    const [scanLoading, setScanLoading] = useState(false)
    const [scanError, setScanError] = useState('')
    const [selectedProject, setSelectedProject] = useState<string | null>(null)
    const [result, setResult] = useState<AnalysisResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [showStructure, setShowStructure] = useState(false)

    const scanProjects = async (folder: string) => {
        if (!folder.trim()) return
        setScanLoading(true)
        setScanError('')
        setProjects([])
        setSelectedProject(null)
        setResult(null)
        try {
            const data = await apiFetch<{ projects: string[] }>('/tools/scan-bmad-projects', {
                method: 'POST',
                body: JSON.stringify({ folder_path: folder }),
            })
            setProjects(data.projects)
        } catch (e: unknown) {
            setScanError(e instanceof Error ? e.message : 'Failed to scan folder')
        } finally {
            setScanLoading(false)
        }
    }

    useEffect(() => { scanProjects(DEFAULT_BASE) }, [])

    const analyze = async (name: string) => {
        setSelectedProject(name)
        setLoading(true)
        setError('')
        setResult(null)
        setShowStructure(false)
        try {
            const data = await apiFetch<AnalysisResult>('/tools/bmad-project-status', {
                method: 'POST',
                body: JSON.stringify({ project_path: `${baseFolder}\\${name}` }),
            })
            setResult(data)
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Request failed')
        } finally {
            setLoading(false)
        }
    }

    // Build a title map from epics files: epic num -> title
    const titleMap: Record<number, string> = {}
    if (result) {
        for (const ef of result.epics_files) {
            for (const ep of ef.epics) {
                if (!titleMap[ep.num]) titleMap[ep.num] = ep.title
            }
        }
    }

    return (
        <div>
            <div className="info-box">
                Scans a dev folder for BMAD projects. Select one to view sprint status and epics.
            </div>

            {/* Folder picker */}
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', marginBottom: 14 }}>
                <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                    <label className="form-label">Dev Folder</label>
                    <input
                        type="text"
                        value={baseFolder}
                        onChange={e => setBaseFolder(e.target.value)}
                        placeholder="C:\Users\you\dev"
                        onKeyDown={e => e.key === 'Enter' && scanProjects(baseFolder)}
                    />
                </div>
                <button className="btn" onClick={() => scanProjects(baseFolder)}
                    disabled={scanLoading || !baseFolder.trim()} style={{ whiteSpace: 'nowrap' }}>
                    {scanLoading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Scanning…</> : '🔄 Scan'}
                </button>
            </div>

            {scanError && <div className="error-box" style={{ marginBottom: 10 }}>{scanError}</div>}

            {/* Project buttons */}
            {projects.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                    <div className="form-label" style={{ marginBottom: 8 }}>BMAD Projects ({projects.length})</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                        {projects.map(name => (
                            <button key={name} onClick={() => analyze(name)} disabled={loading} style={{
                                padding: '6px 14px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
                                border: '1px solid var(--border)',
                                background: selectedProject === name ? 'var(--accent)' : 'var(--surface)',
                                color: selectedProject === name ? '#fff' : 'var(--text-primary)',
                                fontWeight: selectedProject === name ? 600 : 400,
                            }}>
                                {name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {projects.length === 0 && !scanLoading && !scanError && (
                <div className="info-box" style={{ marginBottom: 14 }}>
                    No BMAD projects found in <code>{baseFolder}</code>.
                </div>
            )}

            {loading && (
                <div style={{ marginBottom: 12, color: 'var(--text-secondary)', fontSize: 13 }}>
                    <span className="spinner" style={{ width: 13, height: 13 }} /> Analyzing <strong>{selectedProject}</strong>…
                </div>
            )}
            {error && <div className="error-box" style={{ marginBottom: 12 }}>{error}</div>}

            {result && (() => {
                const { bmad_info, status_summary, status_data, sprint_files, epics_files } = result
                return (
                    <div style={{ marginTop: 4 }}>
                        {/* Errors/warnings */}
                        {bmad_info.errors.map((e, i) => (
                            <div key={i} className="info-box" style={{ marginBottom: 8, borderColor: '#f59e0b55', color: '#92400e' }}>⚠️ {e}</div>
                        ))}

                        {/* Workflow status */}
                        {status_summary && status_data ? (
                            <WorkflowSection
                                summary={status_summary}
                                raw={status_data}
                                onDownload={() => {
                                    const blob = new Blob([JSON.stringify(status_data, null, 2)], { type: 'application/json' })
                                    const url = URL.createObjectURL(blob)
                                    const a = document.createElement('a'); a.href = url; a.download = 'bmm-workflow-status.json'; a.click()
                                    URL.revokeObjectURL(url)
                                }}
                            />
                        ) : bmad_info.status_file ? (
                            <div className="error-box" style={{ marginBottom: 16 }}>Could not parse workflow status file.</div>
                        ) : null}

                        {/* Epics files */}
                        {epics_files.map((ef, i) => <EpicsSection key={i} file={ef} />)}

                        {/* Sprint files */}
                        {sprint_files.map((sf, i) => <SprintSection key={i} file={sf} titleMap={titleMap} />)}

                        {sprint_files.length === 0 && epics_files.length === 0 && !status_summary && (
                            <div className="info-box">No BMAD output files found in this project yet.</div>
                        )}

                        {/* Project structure (collapsed) */}
                        <button className="btn" style={{ fontSize: 12, padding: '4px 10px' }}
                            onClick={() => setShowStructure(v => !v)}>
                            📂 {showStructure ? 'Hide' : 'Show'} Project Structure
                        </button>
                        {showStructure && (
                            <div style={{ marginTop: 10, padding: 14, background: 'var(--surface)', borderRadius: 8, border: '1px solid var(--border)', fontSize: 12 }}>
                                {[
                                    ['Project Path', bmad_info.project_path],
                                    ['BMAD Folder', bmad_info.bmad_folder],
                                    ['Config File', bmad_info.config_file],
                                    ['Output Folder', bmad_info.output_folder],
                                    ['Workflow Status', bmad_info.status_file],
                                ].map(([label, val]) => val && (
                                    <div key={label} style={{ marginBottom: 5 }}>
                                        <span style={{ color: 'var(--text-secondary)', marginRight: 8 }}>{label}</span>
                                        <code style={{ fontSize: 11 }}>{val}</code>
                                    </div>
                                ))}
                                {bmad_info.sprint_status_files.map((f, i) => (
                                    <div key={i} style={{ marginBottom: 5 }}>
                                        <span style={{ color: 'var(--text-secondary)', marginRight: 8 }}>Sprint File {i + 1}</span>
                                        <code style={{ fontSize: 11 }}>{f}</code>
                                    </div>
                                ))}
                                {bmad_info.epics_files.map((f, i) => (
                                    <div key={i} style={{ marginBottom: 5 }}>
                                        <span style={{ color: 'var(--text-secondary)', marginRight: 8 }}>Epics File {i + 1}</span>
                                        <code style={{ fontSize: 11 }}>{f}</code>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )
            })()}
        </div>
    )
}
