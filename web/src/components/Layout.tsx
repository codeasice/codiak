import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiFetch } from '../api'

interface ToolMeta {
    id: string
    short_title: string
    long_title: string
    category: string
    description: string
    requires_vault_path: boolean
}

export default function Layout({ children }: { children: React.ReactNode }) {
    const navigate = useNavigate()
    const location = useLocation()
    const [openCategories, setOpenCategories] = useState<Set<string>>(new Set())

    const { data: tools = [] } = useQuery<ToolMeta[]>({
        queryKey: ['tools'],
        queryFn: () => apiFetch('/tools'),
    })

    // Group by category
    const categories: Record<string, ToolMeta[]> = {}
    for (const tool of tools) {
        if (!categories[tool.category]) categories[tool.category] = []
        categories[tool.category].push(tool)
    }

    const currentToolId = location.pathname.startsWith('/tool/')
        ? location.pathname.split('/tool/')[1]
        : null

    // Auto-open category of current tool
    const toggleCategory = (cat: string) => {
        setOpenCategories(prev => {
            const next = new Set(prev)
            next.has(cat) ? next.delete(cat) : next.add(cat)
            return next
        })
    }

    const isCatOpen = (cat: string) =>
        openCategories.has(cat) ||
        (currentToolId != null && categories[cat]?.some(t => t.id === currentToolId))

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div>
                        <div className="sidebar-logo">🛠 Codiak</div>
                        <div className="sidebar-subtitle">Tool Platform</div>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <button
                        className={`sidebar-home-btn ${location.pathname === '/' ? 'active' : ''}`}
                        onClick={() => navigate('/')}
                    >
                        🏠 Tool Directory
                    </button>

                    {Object.entries(categories)
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([cat, catTools]) => (
                            <div key={cat} className="category-group">
                                <div
                                    className={`category-header ${isCatOpen(cat) ? 'open' : ''}`}
                                    onClick={() => toggleCategory(cat)}
                                >
                                    <span>{cat}</span>
                                    <span className="chevron">▶</span>
                                </div>
                                <div className={`category-tools ${isCatOpen(cat) ? 'open' : ''}`}>
                                    {catTools.map(tool => (
                                        <button
                                            key={tool.id}
                                            className={`tool-btn ${currentToolId === tool.id ? 'active' : ''}`}
                                            onClick={() => navigate(`/tool/${tool.id}`)}
                                            title={tool.long_title}
                                        >
                                            {tool.short_title}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ))}
                </nav>
            </aside>

            <main className="main-content">
                {children}
            </main>
        </div>
    )
}
