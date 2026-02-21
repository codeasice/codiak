import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../api'

interface ToolMeta {
    id: string
    short_title: string
    long_title: string
    category: string
    description: string
}

export default function ToolDirectory() {
    const navigate = useNavigate()
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

    const { data: tools = [], isLoading } = useQuery<ToolMeta[]>({
        queryKey: ['tools'],
        queryFn: () => apiFetch('/tools'),
    })

    const categories = [...new Set(tools.map(t => t.category))].sort()
    const filtered = selectedCategory
        ? tools.filter(t => t.category === selectedCategory)
        : tools

    return (
        <div>
            <h1 className="page-title">🛠 Tool Directory</h1>
            <p className="page-subtitle">
                Select a tool from the sidebar or launch one below. &nbsp;
                <span style={{ color: 'var(--accent)' }}>{tools.length} tools available</span>
            </p>

            {isLoading ? (
                <div className="loading-spinner">
                    <div className="spinner" />
                    Loading tools…
                </div>
            ) : (
                <>
                    <div className="filter-chips">
                        <button
                            className={`chip ${selectedCategory == null ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(null)}
                        >
                            All
                        </button>
                        {categories.map(cat => (
                            <button
                                key={cat}
                                className={`chip ${selectedCategory === cat ? 'active' : ''}`}
                                onClick={() => setSelectedCategory(cat)}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>

                    <div className="tool-grid">
                        {filtered.map(tool => (
                            <div key={tool.id} className="tool-card" onClick={() => navigate(`/tool/${tool.id}`)}>
                                <div className="tool-card-category">{tool.category}</div>
                                <div className="tool-card-title">{tool.short_title}</div>
                                <div className="tool-card-desc">{tool.description}</div>
                                <button className="tool-card-launch" onClick={e => { e.stopPropagation(); navigate(`/tool/${tool.id}`) }}>
                                    Launch →
                                </button>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    )
}
